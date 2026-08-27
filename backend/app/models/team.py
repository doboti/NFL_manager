from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.config import settings
from app.core.game_data import player_daily_salary, team_colors, team_logo_url_by_code
from app.core.schedule import next_match_time
from app.models.enums import Tactic


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        # A user can now own multiple teams (one per league instance, up to
        # their unlocked slot count) but never two in the *same* instance.
        UniqueConstraint("owner_id", "league_id", name="uq_teams_owner_league"),
        # The same real team code (e.g. "NE") legitimately exists once per
        # league instance now that multiple concurrent instances of the
        # same sport can exist -- was a bare global unique before.
        UniqueConstraint("league_id", "nfl_team_code", name="uq_teams_league_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nfl_team_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)

    franchise_capital: Mapped[int] = mapped_column(Integer, default=settings.starting_capital)
    stadium_level: Mapped[int] = mapped_column(Integer, default=1)
    tactic: Mapped[Tactic] = mapped_column(Enum(Tactic, name="tactic"), default=Tactic.BALANCED)

    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ties: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner: Mapped["User"] = relationship(back_populates="teams", foreign_keys=[owner_id])
    league: Mapped["League"] = relationship()
    players: Mapped[list["Player"]] = relationship(back_populates="team")
    sponsors: Mapped[list["Sponsor"]] = relationship(back_populates="team", cascade="all, delete-orphan")

    @property
    def next_match_at(self) -> datetime:
        return next_match_time(self.created_at)

    @property
    def daily_salary_cost(self) -> int:
        return sum(player_daily_salary(p.overall) for p in self.players)

    @property
    def primary_color(self) -> str:
        return team_colors(self.nfl_team_code)["primary"]

    @property
    def secondary_color(self) -> str:
        return team_colors(self.nfl_team_code)["secondary"]

    @property
    def logo_url(self) -> str | None:
        return team_logo_url_by_code(self.nfl_team_code)
