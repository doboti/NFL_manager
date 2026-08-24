from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.config import settings
from app.core.schedule import next_match_time
from app.models.enums import Tactic


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    nfl_team_code: Mapped[str | None] = mapped_column(String(10), unique=True, nullable=True, index=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)

    franchise_capital: Mapped[int] = mapped_column(Integer, default=settings.starting_capital)
    stadium_level: Mapped[int] = mapped_column(Integer, default=1)
    tactic: Mapped[Tactic] = mapped_column(Enum(Tactic, name="tactic"), default=Tactic.BALANCED)

    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ties: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner: Mapped["User"] = relationship(back_populates="team")
    players: Mapped[list["Player"]] = relationship(back_populates="team")
    sponsors: Mapped[list["Sponsor"]] = relationship(back_populates="team", cascade="all, delete-orphan")

    @property
    def next_match_at(self) -> datetime:
        return next_match_time(self.created_at)
