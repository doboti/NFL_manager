"""Fills every team (in every league) that has no franchise yet with a
lightweight AI-controlled one (runs automatically on backend startup too --
this is for manual re-seeding).

Run inside the backend container:
    docker compose exec backend python -m app.scripts.seed_bot_teams
"""

from app.core.bots import seed_bot_teams
from app.core.clock import list_leagues
from app.core.database import SessionLocal

if __name__ == "__main__":
    session = SessionLocal()
    try:
        total = 0
        for league in list_leagues(session):
            created = seed_bot_teams(session, league)
            print(f"{league.key}: created {created} bot team(s).")
            total += created
        print(f"Total: {total} bot team(s) created.")
    finally:
        session.close()
