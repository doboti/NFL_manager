"""Dev/test virtual clock: a stored offset added to real wall-clock time,
so an admin panel can fast-forward training/stadium/matches without waiting.
Training, stadium upgrades, sponsor contracts, and match scheduling all read
"now" through this module's `now_utc()`, so they all move with the virtual
clock. See app/routers/admin.py.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.league import League
from app.models.match import Match
from app.models.sponsor import Sponsor
from app.models.stadium_upgrade import StadiumUpgrade
from app.models.training import TrainingSession

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
    """Zeroing the offset alone would leave every in-progress
    training/upgrade/sponsor/match still stamped with an ends_at/scheduled_at
    computed under the old (larger) offset -- e.g. "26 days" of remaining
    upgrade time that barely moves under further advances, because it's
    actually weeks in the future relative to the just-reset clock. Shift
    every such timestamp back by exactly the amount the offset shrank, so
    everyone's *remaining* duration is preserved instead of stranded."""
    league = get_or_create_default_league(db)
    delta = timedelta(seconds=league.time_offset_seconds)
    league.time_offset_seconds = 0

    if delta:
        db.query(Match).filter(Match.league_id == league.id, Match.played.is_(False)).update(
            {Match.scheduled_at: Match.scheduled_at - delta}, synchronize_session=False
        )
        db.query(StadiumUpgrade).filter(StadiumUpgrade.collected.is_(False)).update(
            {StadiumUpgrade.ends_at: StadiumUpgrade.ends_at - delta}, synchronize_session=False
        )
        db.query(TrainingSession).filter(TrainingSession.collected.is_(False)).update(
            {TrainingSession.ends_at: TrainingSession.ends_at - delta}, synchronize_session=False
        )
        db.query(Sponsor).update({Sponsor.expires_at: Sponsor.expires_at - delta}, synchronize_session=False)

    db.commit()
    return now_utc(db)
