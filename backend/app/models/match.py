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
