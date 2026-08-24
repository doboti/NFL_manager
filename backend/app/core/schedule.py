from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.game_data import LEAGUE_TIMEZONE, MATCH_HOUR

LEAGUE_TZ = ZoneInfo(LEAGUE_TIMEZONE)


def next_match_time(created_at: datetime, now: datetime | None = None) -> datetime:
    """First match is the day after joining, at MATCH_HOUR local time; after that,
    the next upcoming daily occurrence of MATCH_HOUR."""
    now = (now or datetime.now(LEAGUE_TZ)).astimezone(LEAGUE_TZ)
    created_local = created_at.astimezone(LEAGUE_TZ)

    candidate_date = created_local.date() + timedelta(days=1)
    candidate = datetime.combine(candidate_date, time(hour=MATCH_HOUR), tzinfo=LEAGUE_TZ)

    while candidate <= now:
        candidate += timedelta(days=1)

    return candidate
