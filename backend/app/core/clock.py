"""Dev/test virtual clock: a stored offset added to real wall-clock time,
so an admin panel can fast-forward training/stadium/matches without waiting.

Everything else in the game (season length, playoff pacing, sponsor days)
still runs on real time -- only the checks this module's `now_utc()` feeds
into move with the virtual clock. See app/routers/admin.py.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.league import League

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
    league = get_or_create_default_league(db)
    league.time_offset_seconds = 0
    db.commit()
    return now_utc(db)
