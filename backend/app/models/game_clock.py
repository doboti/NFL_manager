from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GameClock(Base):
    """Singleton row: the dev/test virtual clock offset, shared by every
    league (it's an admin testing tool, not a per-league concept)."""

    __tablename__ = "game_clock"

    id: Mapped[int] = mapped_column(primary_key=True)
    time_offset_seconds: Mapped[int] = mapped_column(Integer, default=0)
