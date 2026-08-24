from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SeasonHistory(Base):
    """Snapshot of a team's final record for one completed season, taken right
    before wins/losses/ties reset for the next one."""

    __tablename__ = "season_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)

    wins: Mapped[int] = mapped_column(Integer, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, nullable=False)
    ties: Mapped[int] = mapped_column(Integer, nullable=False)

    # "missed_playoffs" | "conference_semifinal" | "conference_final" | "runner_up" | "champion"
    playoff_result: Mapped[str] = mapped_column(String(30), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    team: Mapped["Team"] = relationship()
