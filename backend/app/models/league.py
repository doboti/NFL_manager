from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import SeasonPhase


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[int] = mapped_column(default=1)

    phase: Mapped[SeasonPhase] = mapped_column(Enum(SeasonPhase, name="season_phase"), default=SeasonPhase.REGULAR)
    season_day: Mapped[int] = mapped_column(Integer, default=0)
    current_playoff_round: Mapped[str | None] = mapped_column(String(30), nullable=True)
    season_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
