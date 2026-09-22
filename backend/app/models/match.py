import math
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Tactic


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False, index=True)
    season: Mapped[int] = mapped_column(Integer, default=1)

    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    home_tactic: Mapped[Tactic] = mapped_column(Enum(Tactic, name="tactic"), default=Tactic.BALANCED)
    away_tactic: Mapped[Tactic] = mapped_column(Enum(Tactic, name="tactic"), default=Tactic.BALANCED)

    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    play_log: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Structured per-play data (field position, participants, pass/run
    # success) for the animated field-view replay -- additive alongside
    # play_log, nullable since older matches predate it and simply fall
    # back to the classic text-log viewer.
    play_events: Mapped[list | None] = mapped_column(JSON, nullable=True)
    played: Mapped[bool] = mapped_column(Boolean, default=False)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_playoff: Mapped[bool] = mapped_column(Boolean, default=False)
    playoff_round: Mapped[str | None] = mapped_column(String(30), nullable=True)

    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id])

    @property
    def home_team_name(self) -> str:
        return self.home_team.name

    @property
    def away_team_name(self) -> str:
        return self.away_team.name

    @property
    def home_team_logo_url(self) -> str | None:
        return self.home_team.logo_url

    @property
    def away_team_logo_url(self) -> str | None:
        return self.away_team.logo_url

    @property
    def home_win_probability(self) -> float:
        """Derived from the exact same expected-score model simulate_match()
        uses to decide the real outcome (#27 -- the old version estimated
        this from a plain average-OVR-of-the-whole-roster Elo formula, which
        could diverge sharply from the actual simulated matchup: it ignored
        starting lineups/tactics entirely and gave the single DEF rating
        only 1-of-N roster weight instead of the full weight it carries
        against the opponent's offense in the simulator, so the displayed
        odds regularly didn't match what the sim would actually produce).

        home_score and away_score are each ~Normal(expected, std) in
        simulate_match, so their difference is also Normal with mean
        home_expected-away_expected and variance std_home^2+std_away^2;
        the win probability is the mass of that distribution above zero."""
        from app.core.simulation import (
            BASE_TEAM_POINTS,
            MIN_SCORE_STD,
            POINT_SCALE,
            SCORE_STD_RATIO,
            compute_team_strength,
        )

        home = compute_team_strength(self.home_team.players, self.home_tactic, self.away_tactic)
        away = compute_team_strength(self.away_team.players, self.away_tactic, self.home_tactic)

        home_expected = max(3.0, BASE_TEAM_POINTS + (home.offense - away.defense) * POINT_SCALE)
        away_expected = max(3.0, BASE_TEAM_POINTS + (away.offense - home.defense) * POINT_SCALE)
        home_std = max(MIN_SCORE_STD, home_expected * SCORE_STD_RATIO) * home.variance
        away_std = max(MIN_SCORE_STD, away_expected * SCORE_STD_RATIO) * away.variance

        margin_std = math.sqrt(home_std**2 + away_std**2)
        z = (home_expected - away_expected) / margin_std
        probability = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return round(probability, 3)
