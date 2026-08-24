"""Fills every NFL team that has no franchise yet with a lightweight AI-controlled
one (runs automatically on backend startup too -- this is for manual re-seeding).

Run inside the backend container:
    docker compose exec backend python -m app.scripts.seed_bot_teams
"""

from app.core.bots import seed_bot_teams
from app.core.database import SessionLocal

if __name__ == "__main__":
    session = SessionLocal()
    try:
        created = seed_bot_teams(session)
        print(f"Created {created} bot team(s).")
    finally:
        session.close()
