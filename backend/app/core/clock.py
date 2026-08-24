"""Dev/test virtual clock: a stored offset added to real wall-clock time,
so an admin panel can fast-forward training/stadium/matches without waiting.

Everything else in the game (season length, playoff pacing, sponsor days)
still runs on real time -- only the checks this module's `now_utc()` feeds
into move with the virtual clock. See app/routers/admin.py.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.league import League
from app.models.match import Match

DEFAULT_LEAGUE_NAME = "Franchise Liga"


def get_or_create_default_league(db: Session) -> League:
    league = db.query(League).filter(League.name == DEFAULT_LEAGUE_NAME).first()
    if league is None:
        league = League(name=DEFAULT_LEAGUE_NAME)
        db.add(league)
        db.flush()
    return league


def now_utc(db: Session) -> datetime:
    league = get_or_create_default_league(db)
    return datetime.now(timezone.utc) + timedelta(seconds=league.time_offset_seconds)


def get_offset_seconds(db: Session) -> int:
    return get_or_create_default_league(db).time_offset_seconds


def advance_time(db: Session, hours: float) -> datetime:
    league = get_or_create_default_league(db)
    league.time_offset_seconds += round(hours * 3600)
    db.commit()
    return now_utc(db)


def reset_time(db: Session) -> datetime:
    """Zeroing the offset alone would leave any not-yet-played matches
    stamped with scheduled_at times computed under the old (larger) offset
    -- e.g. weeks "in the future" relative to the just-reset clock. Clear
    them so the next daily cycle's ensure_fixtures_scheduled recreates
    fresh ones anchored to the new time; already-played matches (and every
    other stat) are untouched."""
    league = get_or_create_default_league(db)
    league.time_offset_seconds = 0
    db.query(Match).filter(Match.league_id == league.id, Match.played.is_(False)).delete()
    db.commit()
    return now_utc(db)
