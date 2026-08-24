from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.game_data import xp_to_next_level
from app.models.enums import Position


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True, index=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False, index=True)

    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    position: Mapped[Position] = mapped_column(Enum(Position, name="player_position"), nullable=False)

    age: Mapped[int] = mapped_column(Integer, nullable=False)
    overall: Mapped[int] = mapped_column(Integer, nullable=False)
    base_overall: Mapped[int] = mapped_column(Integer, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0)

    market_price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    espn_id: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nfl_team: Mapped[str | None] = mapped_column(String(10), nullable=True)

    listed_for_transfer: Mapped[bool] = mapped_column(Boolean, default=False)
    asking_price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_starter: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    team: Mapped["Team | None"] = relationship(back_populates="players")

    @property
    def xp_to_next_level(self) -> int:
        return xp_to_next_level(self.overall)
