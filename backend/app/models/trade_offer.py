from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TradeStatus


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id: Mapped[int] = mapped_column(primary_key=True)

    from_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    to_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)

    target_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    offered_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    cash_offer: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[TradeStatus] = mapped_column(Enum(TradeStatus, name="trade_status"), default=TradeStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Bot-only: when a bot-addressed offer gets its automatic accept/reject
    # decision (0-4h after creation, see trades.py: BOT_RESPONSE_WINDOW_HOURS).
    respond_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Every offer, bot or human target: auto-expires if still PENDING after
    # this (24h from creation) -- a human recipient who never responds
    # shouldn't leave an offer stuck forever. Nullable only because it
    # predates existing rows; those get backfilled once, see the migration.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    from_team: Mapped["Team"] = relationship(foreign_keys=[from_team_id])
    to_team: Mapped["Team"] = relationship(foreign_keys=[to_team_id])
    target_player: Mapped["Player"] = relationship(foreign_keys=[target_player_id])
    offered_player: Mapped["Player | None"] = relationship(foreign_keys=[offered_player_id])

    @property
    def from_team_name(self) -> str:
        return self.from_team.name

    @property
    def to_team_name(self) -> str:
        return self.to_team.name

    @property
    def to_team_is_bot(self) -> bool:
        return self.to_team.is_bot
