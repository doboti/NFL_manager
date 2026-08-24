from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StadiumUpgrade(Base):
    __tablename__ = "stadium_upgrades"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)

    target_level: Mapped[int] = mapped_column(Integer, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    collected: Mapped[bool] = mapped_column(Boolean, default=False)

    team: Mapped["Team"] = relationship()
