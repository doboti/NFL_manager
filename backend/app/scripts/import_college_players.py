"""One-off / periodic data import: populates the college-football free-agent
pool with real rosters from ESPN's public (unofficial) site API, for the
32-team subset in game_data.COLLEGE_TEAMS (the only college teams ESPN
actually has current roster data for that we've wired in).

Only player names and a link to ESPN's own hosted headshot image are stored
-- no photo bytes are copied or re-hosted. ESPN doesn't track an exact age
for college athletes (amateur roster data), so age is a plausible 18-23
random value; `overall` has no real-world source either and is synthesized,
nudged by class year (freshman..senior) the same way the NFL import nudges
by pro experience.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.import_college_players
"""

import random
import time

import requests
from sqlalchemy.orm import Session

from app.core.clock import get_or_create_league
from app.core.database import SessionLocal
from app.core.game_data import COLLEGE_TEAMS, player_market_value
from app.models.enums import Position
from app.models.player import Player

ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/roster"
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
    "DL": Position.DEF,
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


def fetch_roster(espn_team_id: str) -> dict:
    resp = requests.get(ROSTER_URL.format(team_id=espn_team_id), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def generate_ratings(class_years: int, depth_index: int) -> tuple[int, int]:
    """Same philosophy as the NFL import's generate_ratings() (see its
    docstring, issues #19/#20): depth-chart position + real class-year
    experience set a realistic, capped baseline, and only a rare,
    signal-weighted "elite roll" can reach the 85-95 range -- being a
    senior starter meaningfully improves the odds, but it's never
    guaranteed. Returns (overall, potential).

    depth_index must be scoped per real ESPN position label, not per merged
    Position enum bucket -- see the depth_index build site in
    import_players() below for why."""
    base = 58.0
    class_component = min(class_years, 5) * 3.2
    depth_component = (4 - min(depth_index, 12)) * 1.5
    noise = random.uniform(-4, 4)
    baseline = max(42, min(80, round(base + class_component + depth_component + noise)))

    elite_chance = 0.02 + (0.05 if depth_index == 0 else 0) + (0.03 if class_years >= 4 else 0)
    if random.random() < elite_chance:
        overall = random.randint(85, 95)
        potential = min(95, overall + random.randint(0, 4))
        return overall, potential

    if class_years <= 1:
        headroom = random.randint(6, 14)
    elif class_years <= 3:
        headroom = random.randint(2, 8)
    else:
        headroom = random.randint(0, 3)
    potential = min(84, baseline + headroom)
    return baseline, potential


def import_players(db: Session) -> dict:
    league = get_or_create_league(db, "college")
    created = 0
    updated = 0
    skipped = 0

    for team in COLLEGE_TEAMS:
        code = team["code"]
        print(f"Importing roster: {team['name']} ({code})")

        roster = fetch_roster(team["espn_id"])
        position_depth: dict[str, int] = {}
        for group in roster.get("athletes", []):
            if group.get("position") not in ACTIVE_GROUPS:
                continue

            for athlete in group.get("items", []):
                espn_position = (athlete.get("position") or {}).get("abbreviation")
                position = POSITION_MAP.get(espn_position)
                if position is None:
                    skipped += 1
                    continue

                # Keyed by the raw ESPN label, not the merged Position
                # bucket -- see generate_ratings()'s docstring.
                depth_index = position_depth.get(espn_position, 0)
                position_depth[espn_position] = depth_index + 1

                espn_id = athlete["id"]
                display_name = athlete.get("displayName", "")
                first_name = athlete.get("firstName") or display_name.split(" ")[0]
                last_name = athlete.get("lastName") or display_name.split(" ")[-1]
                age = athlete.get("age") or random.randint(18, 23)
                class_years = (athlete.get("experience") or {}).get("years", 1)
                headshot = (athlete.get("headshot") or {}).get("href")

                existing = db.query(Player).filter(Player.espn_id == espn_id).first()

                if existing is None:
                    overall, potential = generate_ratings(class_years, depth_index)
                    player = Player(
                        team_id=None,
                        league_id=league.id,
                        first_name=first_name,
                        last_name=last_name,
                        position=position,
                        age=age,
                        overall=overall,
                        base_overall=overall,
                        potential=potential,
                        market_price=max(1, round(player_market_value(BASE_MARKET_PRICE, overall, age))),
                        espn_id=espn_id,
                        photo_url=headshot,
                        nfl_team=code,
                    )
                    db.add(player)
                    created += 1
                else:
                    existing.photo_url = headshot
                    existing.nfl_team = code
                    if existing.team_id is None:
                        # Free agents have no training investment to lose --
                        # safe to re-rate with the improved formula (#19/#20)
                        # on every re-run, instead of being stuck with
                        # whatever the old random roll gave them.
                        overall, potential = generate_ratings(class_years, depth_index)
                        existing.overall = overall
                        existing.base_overall = overall
                        existing.potential = potential
                        existing.market_price = max(
                            1, round(player_market_value(BASE_MARKET_PRICE, overall, existing.age))
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
