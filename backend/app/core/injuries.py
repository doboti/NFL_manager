import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.player import Player

# Roughly 1 injury per team every 5 matches, on average -- but it's a flat
# per-match coin flip, not a counter, so real playthroughs naturally see
# streaks and long gaps instead of a metronomic "every 5th game" pattern.
INJURY_CHANCE_PER_MATCH = 0.20

# One virtual day == one played match == one NFL "week" (the regular season
# is 17 days long, same as the real 17-week season), so a week of recovery
# is exactly one day of game-clock time.
DAYS_PER_WEEK = 1

# Skewed toward short knocks -- a tweak that costs a game or two happens a
# lot more often than a multi-week injury.
_WEEK_WEIGHTS = [30, 22, 16, 12, 8, 6, 4, 2]  # weeks 1..8


def _roll_injury_weeks() -> int:
    return random.choices(range(1, 9), weights=_WEEK_WEIGHTS, k=1)[0]


def injured_player_ids(db: Session, team_id: int, now: datetime) -> set[int]:
    rows = (
        db.query(Player.id)
        .filter(Player.team_id == team_id, Player.injured_until.isnot(None), Player.injured_until > now)
        .all()
    )
    return {player_id for (player_id,) in rows}


def maybe_injure_player(players_in_play: list[Player], now: datetime) -> Player | None:
    """Rolls a per-match injury chance for one team; if it hits, hurts a
    random player who actually took the field (not currently already hurt)
    for a random 1-8 week span. Returns the injured player, or None."""
    if not players_in_play:
        return None
    if random.random() >= INJURY_CHANCE_PER_MATCH:
        return None

    candidates = [p for p in players_in_play if not (p.injured_until and p.injured_until > now)]
    if not candidates:
        return None

    player = random.choice(candidates)
    weeks = _roll_injury_weeks()
    player.injured_until = now + timedelta(days=weeks * DAYS_PER_WEEK)
    return player
