from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.game_data import MAX_STADIUM_LEVEL, STADIUM_LEVELS
from app.models.stadium_upgrade import StadiumUpgrade
from app.models.team import Team


class StadiumError(Exception):
    pass


def get_pending_upgrade(db: Session, team_id: int) -> StadiumUpgrade | None:
    return (
        db.query(StadiumUpgrade)
        .filter(StadiumUpgrade.team_id == team_id, StadiumUpgrade.collected.is_(False))
        .first()
    )


def start_upgrade(db: Session, team: Team) -> StadiumUpgrade:
    if team.stadium_level >= MAX_STADIUM_LEVEL:
        raise StadiumError("Stadium is already at max level")

    if get_pending_upgrade(db, team.id) is not None:
        raise StadiumError("A stadium upgrade is already in progress")

    next_level = team.stadium_level + 1
    level_data = STADIUM_LEVELS[next_level]

    if team.franchise_capital < level_data["upgrade_cost"]:
        raise StadiumError("Not enough Franchise Tőke")

    team.franchise_capital -= level_data["upgrade_cost"]

    now = now_utc(db)
    upgrade = StadiumUpgrade(
        team_id=team.id,
        target_level=next_level,
        started_at=now,
        ends_at=now + timedelta(hours=level_data["upgrade_hours"]),
    )
    db.add(upgrade)
    db.commit()
    db.refresh(upgrade)
    return upgrade


def collect_upgrade(db: Session, team: Team) -> StadiumUpgrade:
    upgrade = get_pending_upgrade(db, team.id)
    if upgrade is None:
        raise StadiumError("No stadium upgrade in progress")

    now = now_utc(db)
    if now < upgrade.ends_at:
        raise StadiumError("Upgrade is not finished yet")

    team.stadium_level = upgrade.target_level
    upgrade.collected = True

    db.commit()
    db.refresh(upgrade)
    return upgrade
