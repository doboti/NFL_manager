import random

from app.core.clock import now_utc
from app.core.game_data import STADIUM_LEVELS, player_daily_salary
from app.models.enums import SponsorType
from app.models.team import Team


def apply_stadium_revenue(team: Team) -> int:
    level_data = STADIUM_LEVELS[team.stadium_level]
    revenue = round(level_data["base_revenue"] * random.uniform(0.9, 1.1))
    team.franchise_capital += revenue
    return revenue


def apply_player_salaries(team: Team) -> int:
    """Every rostered player (bench included, bots too) costs upkeep scaled
    by OVR -- a stronger roster is more expensive to maintain, which is the
    main lever against runaway franchise capital growth."""
    total = sum(player_daily_salary(p.overall) for p in team.players)
    team.franchise_capital -= total
    return total


def apply_sponsor_payouts(db, team: Team, won_today: bool | None) -> int:
    total = 0
    expired = []
    now = now_utc(db)

    for sponsor in team.sponsors:
        total += sponsor.daily_amount
        if sponsor.sponsor_type == SponsorType.PERFORMANCE and won_today:
            total += sponsor.win_bonus
        if sponsor.expires_at <= now:
            expired.append(sponsor)

    for sponsor in expired:
        db.delete(sponsor)

    team.franchise_capital += total
    return total
