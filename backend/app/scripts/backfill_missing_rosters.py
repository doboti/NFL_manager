"""One-off repair script: assigns a real roster to any existing team (bot
or human-claimed) that currently has zero players.

This happens if a team was created (e.g. by seed_bot_teams on the backend's
very first startup) before the real player import scripts had ever been
run -- team creation only pulls from already-imported free agents, and
nothing retroactively backfills a team that missed out.

Safe to run any time: only touches teams with an empty roster right now,
never deletes or reassigns anything from a team that already has players.

Run inside the backend container, AFTER import_nfl_players /
import_college_players:
    docker compose exec backend python -m app.scripts.backfill_missing_rosters
"""

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.team_setup import assign_real_roster
from app.models.player import Player
from app.models.team import Team


def _roster_size(db: Session, team_id: int) -> int:
    # assign_real_roster sets Player.team_id directly (not via the ORM
    # relationship attribute), so Team.players' in-memory cache doesn't
    # pick up the change -- count from a fresh query instead of trusting it.
    return db.query(Player).filter(Player.team_id == team_id).count()


def backfill_missing_rosters(db: Session) -> dict:
    teams = db.query(Team).filter(Team.nfl_team_code.isnot(None)).all()
    fixed = []
    still_empty = []

    for team in teams:
        if _roster_size(db, team.id) > 0:
            continue
        assign_real_roster(db, team, team.nfl_team_code, team.league_id)
        if _roster_size(db, team.id) > 0:
            fixed.append(team.name)
        else:
            still_empty.append(team.name)

    db.commit()
    return {"teams_fixed": len(fixed), "fixed": fixed, "still_empty": still_empty}


if __name__ == "__main__":
    session = SessionLocal()
    try:
        summary = backfill_missing_rosters(session)
        print(summary)
    finally:
        session.close()
