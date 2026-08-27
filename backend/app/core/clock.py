"""Dev/test virtual clock: a stored offset added to real wall-clock time,
so an admin panel can fast-forward training/stadium/matches without waiting.
Training, stadium upgrades, sponsor contracts, and match scheduling all read
"now" through this module's `now_utc()`, so they all move with the virtual
clock -- shared by every league, since it's a single admin testing tool, not
a per-league concept. See app/routers/admin.py.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.game_data import LEAGUES
from app.models.enums import TradeStatus
from app.models.game_clock import GameClock
from app.models.league import League
from app.models.match import Match
from app.models.player import Player
from app.models.sponsor import Sponsor
from app.models.stadium_upgrade import StadiumUpgrade
from app.models.trade_offer import TradeOffer
from app.models.training import TrainingSession

DEFAULT_LEAGUE_KEY = "nfl"


def get_or_create_game_clock(db: Session) -> GameClock:
    clock = db.query(GameClock).first()
    if clock is None:
        clock = GameClock()
        db.add(clock)
        db.flush()
    return clock


def get_or_create_league(db: Session, key: str) -> League:
    """Resolves/creates the *default* (first) instance of a sport -- `key`
    is historically just the sport name ("nfl"/"college") for these two
    built-in rows. See create_league_instance() for any additional,
    self-service-created instance of the same sport."""
    league = db.query(League).filter(League.key == key).first()
    if league is None:
        league = League(key=key, sport=key, name=LEAGUES[key]["name"])
        db.add(league)
        db.flush()
    return league


def create_league_instance(db: Session, sport: str) -> League:
    """Creates an additional, independent instance of a sport (own
    32-team universe: schedule, free-agent pool, economy) -- what lets a
    manager hold 2 concurrent NFL teams once a league slot unlocks, since
    a single NFL instance only ever has 32 real teams to claim. Immediately
    imports real players and seeds bot teams so it's playable right away.
    Caller (routers/league.py) is responsible for checking the requester
    actually has a free slot and that no existing instance of this sport
    still has room before calling this."""
    if sport not in LEAGUES:
        raise ValueError(f"Unknown sport: {sport}")

    existing_count = db.query(League).filter(League.sport == sport).count()
    n = existing_count + 1
    key = sport if n == 1 else f"{sport}-{n}"
    name = LEAGUES[sport]["name"] if n == 1 else f"{LEAGUES[sport]['name']} #{n}"

    league = League(key=key, sport=sport, name=name)
    db.add(league)
    db.flush()

    # Local import to avoid a circular import (these scripts import from
    # app.core.clock themselves).
    from app.core.bots import seed_bot_teams
    from app.scripts.import_college_players import import_players as import_college
    from app.scripts.import_nfl_players import import_players as import_nfl

    if sport == "nfl":
        import_nfl(db, league)
    elif sport == "college":
        import_college(db, league)
    seed_bot_teams(db, league)

    return league


def get_or_create_default_league(db: Session) -> League:
    """Back-compat shorthand for the NFL league, used anywhere that hasn't
    been made explicitly league-aware yet."""
    return get_or_create_league(db, DEFAULT_LEAGUE_KEY)


def list_leagues(db: Session) -> list[League]:
    """Ensures every registered league (see game_data.LEAGUES) has a row,
    then returns all of them -- the daily cycle and startup seeding loop
    over this."""
    for key in LEAGUES:
        get_or_create_league(db, key)
    return db.query(League).order_by(League.id).all()


def now_utc(db: Session) -> datetime:
    clock = get_or_create_game_clock(db)
    return datetime.now(timezone.utc) + timedelta(seconds=clock.time_offset_seconds)


def get_offset_seconds(db: Session) -> int:
    return get_or_create_game_clock(db).time_offset_seconds


def advance_time(db: Session, hours: float) -> datetime:
    clock = get_or_create_game_clock(db)
    clock.time_offset_seconds += round(hours * 3600)
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
    clock = get_or_create_game_clock(db)
    delta = timedelta(seconds=clock.time_offset_seconds)
    clock.time_offset_seconds = 0

    if delta:
        db.query(Match).filter(Match.played.is_(False)).update(
            {Match.scheduled_at: Match.scheduled_at - delta}, synchronize_session=False
        )
        db.query(StadiumUpgrade).filter(StadiumUpgrade.collected.is_(False)).update(
            {StadiumUpgrade.ends_at: StadiumUpgrade.ends_at - delta}, synchronize_session=False
        )
        db.query(TrainingSession).filter(TrainingSession.collected.is_(False)).update(
            {TrainingSession.ends_at: TrainingSession.ends_at - delta}, synchronize_session=False
        )
        db.query(Sponsor).update({Sponsor.expires_at: Sponsor.expires_at - delta}, synchronize_session=False)
        db.query(Player).filter(Player.injured_until.isnot(None)).update(
            {Player.injured_until: Player.injured_until - delta}, synchronize_session=False
        )
        db.query(TradeOffer).filter(
            TradeOffer.status == TradeStatus.PENDING, TradeOffer.respond_at.isnot(None)
        ).update({TradeOffer.respond_at: TradeOffer.respond_at - delta}, synchronize_session=False)

    db.commit()
    return now_utc(db)
