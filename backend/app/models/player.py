from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.game_data import sessions_required_for_next_point
from app.models.enums import Position


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        # The same real ESPN athlete now legitimately gets a separate Player
        # row per league instance (each instance re-imports the full real
        # player pool independently) -- was a bare global unique before,
        # which would have blocked importing into a 2nd instance entirely.
        UniqueConstraint("league_id", "espn_id", name="uq_players_league_espn_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True, index=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False, index=True)

    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    position: Mapped[Position] = mapped_column(Enum(Position, name="player_position"), nullable=False)

    age: Mapped[int] = mapped_column(Integer, nullable=False)
    overall: Mapped[int] = mapped_column(Integer, nullable=False)
    base_overall: Mapped[int] = mapped_column(Integer, nullable=False)
    # Ceiling training can never push overall past (see #20) -- nullable only
    # because existing rows predate this column; backfill_potential.py sets
    # it for every row, and new imports always set it explicitly.
    potential: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Sessions banked toward the next point at the current training band
    # (see game_data.sessions_required_for_next_point) -- resets on level-up
    # since the required count changes per band.
    xp: Mapped[int] = mapped_column(Integer, default=0)

    market_price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    espn_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nfl_team: Mapped[str | None] = mapped_column(String(10), nullable=True)

    listed_for_transfer: Mapped[bool] = mapped_column(Boolean, default=False)
    asking_price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_starter: Mapped[bool] = mapped_column(Boolean, default=False)

    injured_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    team: Mapped["Team | None"] = relationship(back_populates="players")

    @property
    def sessions_to_next_point(self) -> int:
        return sessions_required_for_next_point(self.overall)
