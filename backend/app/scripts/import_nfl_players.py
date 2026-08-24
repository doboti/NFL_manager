"""One-off / periodic data import: populates the free-agent pool with real NFL
rosters from ESPN's public (unofficial) site API.

Only player names, ages and a link to ESPN's own hosted headshot image are
stored -- no photo bytes are copied or re-hosted, the frontend hotlinks the
ESPN CDN URL directly. There is no official rating in the source data, so
`overall` is a synthesized value (loosely nudged by NFL experience), not a
real skill rating.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.import_nfl_players
"""

import random
import time

import requests
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.game_data import player_market_value
from app.models.enums import Position
from app.models.player import Player

TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams?limit=40"
ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
REQUEST_TIMEOUT = 15
DELAY_BETWEEN_TEAMS = 0.3

BASE_MARKET_PRICE = 1000

ACTIVE_GROUPS = {"offense", "defense", "specialTeam"}

POSITION_MAP: dict[str, Position] = {
    "QB": Position.QB,
    "RB": Position.RB,
    "FB": Position.RB,
    "WR": Position.WR,
    "TE": Position.TE,
    "K": Position.K,
    "PK": Position.K,
    "DT": Position.DEF,
    "NT": Position.DEF,
    "DE": Position.DEF,
    "EDGE": Position.DEF,
    "LB": Position.DEF,
    "OLB": Position.DEF,
    "ILB": Position.DEF,
    "MLB": Position.DEF,
    "CB": Position.DEF,
    "S": Position.DEF,
    "FS": Position.DEF,
    "SS": Position.DEF,
    "DB": Position.DEF,
}


def fetch_teams() -> list[dict]:
    resp = requests.get(TEAMS_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return [t["team"] for t in data["sports"][0]["leagues"][0]["teams"]]


def fetch_roster(team_id: str) -> dict:
    resp = requests.get(ROSTER_URL.format(team_id=team_id), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def generate_overall(experience_years: int) -> int:
    """No real rating exists in the source data; synthesize a plausible one."""
    base = random.randint(52, 80)
    veteran_bonus = min(experience_years, 10) * random.uniform(0.5, 1.5)
    if random.random() > 0.93:
        base += random.randint(10, 18)
    return max(40, min(99, round(base + veteran_bonus)))


def import_players(db: Session) -> dict:
    teams = fetch_teams()
    created = 0
    updated = 0
    skipped = 0

    for team in teams:
        team_id = team["id"]
        abbreviation = team["abbreviation"]
        print(f"Importing roster: {team['displayName']} ({abbreviation})")

        roster = fetch_roster(team_id)
        for group in roster.get("athletes", []):
            if group.get("position") not in ACTIVE_GROUPS:
                continue

            for athlete in group.get("items", []):
                espn_position = (athlete.get("position") or {}).get("abbreviation")
                position = POSITION_MAP.get(espn_position)
                if position is None:
                    skipped += 1
                    continue

                espn_id = athlete["id"]
                display_name = athlete.get("displayName", "")
                first_name = athlete.get("firstName") or display_name.split(" ")[0]
                last_name = athlete.get("lastName") or display_name.split(" ")[-1]
                age = athlete.get("age") or random.randint(22, 34)
                experience_years = (athlete.get("experience") or {}).get("years", 0)
                headshot = (athlete.get("headshot") or {}).get("href")

                existing = db.query(Player).filter(Player.espn_id == espn_id).first()

                if existing is None:
                    overall = generate_overall(experience_years)
                    player = Player(
                        team_id=None,
                        first_name=first_name,
                        last_name=last_name,
                        position=position,
                        age=age,
                        overall=overall,
                        market_price=max(1, round(player_market_value(BASE_MARKET_PRICE, overall, age))),
                        espn_id=espn_id,
                        photo_url=headshot,
                        nfl_team=abbreviation,
                    )
                    db.add(player)
                    created += 1
                else:
                    existing.age = age
                    existing.photo_url = headshot
                    existing.nfl_team = abbreviation
                    if existing.team_id is None:
                        existing.market_price = max(
                            1, round(player_market_value(BASE_MARKET_PRICE, existing.overall, age))
                        )
                    updated += 1

        db.commit()
        time.sleep(DELAY_BETWEEN_TEAMS)

    return {"created": created, "updated": updated, "skipped": skipped}


if __name__ == "__main__":
    session = SessionLocal()
    try:
        summary = import_players(session)
        print(summary)
    finally:
        session.close()
