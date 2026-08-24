from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SponsorType


class Sponsor(Base):
    __tablename__ = "sponsors"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)

    template_key: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sponsor_type: Mapped[SponsorType] = mapped_column(Enum(SponsorType, name="sponsor_type"), nullable=False)
    daily_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    win_bonus: Mapped[int] = mapped_column(Integer, default=0)

    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="sponsors")
