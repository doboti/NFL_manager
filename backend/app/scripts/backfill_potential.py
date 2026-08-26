"""One-off repair script: assigns a `potential` ceiling to every player that
doesn't have one yet -- every row imported before issue #20's migration.

Computed from the player's CURRENT rating and age (their original
depth-chart/experience signal from import time is long gone), with a
guarantee that potential never lands below where the player already is --
this must never retroactively nerf an existing, possibly already-trained
player.

Safe to run any time: only touches rows where potential IS NULL.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.backfill_potential
"""

import random

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.player import Player


def _headroom(age: int) -> int:
    if age <= 24:
        return random.randint(6, 14)
    if age <= 28:
        return random.randint(2, 8)
    return random.randint(0, 3)


def backfill_potential(db: Session) -> dict:
    players = db.query(Player).filter(Player.potential.is_(None)).all()
    for player in players:
        current = max(player.overall, player.base_overall)
        if current >= 88:
            # Already elite by current rating -- treat as having won the
            # "elite roll" retroactively, same ceiling shape as a fresh import.
            player.potential = min(99, current + random.randint(0, 5))
        else:
            player.potential = max(current, min(89, current + _headroom(player.age)))

    db.commit()
    return {"backfilled": len(players)}


if __name__ == "__main__":
    session = SessionLocal()
    try:
        summary = backfill_potential(session)
        print(summary)
    finally:
        session.close()
