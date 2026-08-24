from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    xp_awarded: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    collected: Mapped[bool] = mapped_column(Boolean, default=False)

    player: Mapped["Player"] = relationship()
