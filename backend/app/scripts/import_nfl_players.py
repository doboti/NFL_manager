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

from app.core.clock import get_or_create_league
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


def generate_ratings(experience_years: int, depth_index: int, age: int) -> tuple[int, int]:
    """No real rating exists in the source data. Two real ESPN-derived
    signals (depth-chart position -- 0 is the player ESPN lists first at
    that spot, almost always the starter -- and real career length) set a
    realistic baseline, capped well below elite. A rare, signal-weighted
    "elite roll" is the *only* way to reach 88-99 (#20) -- being a proven
    starter meaningfully improves the odds, but it's never guaranteed,
    which is what keeps a 90+ rating a genuine rarity instead of routine
    (previously nearly every real starter with some tenure computed into
    the 90s deterministically, and #19's fix alone didn't limit *how many*
    players that could be true for across a whole roster).

    depth_index must be scoped per real ESPN position label (CB, DT, LB,
    ...), not per merged Position enum bucket -- Position.DEF alone
    aggregates ~10 real positions, and a shared counter across all of them
    would make a legitimate starting CB look like a 15th-string scrub just
    because ESPN lists DL/LB athletes first. See the depth_index build site
    in import_players() below.

    Returns (overall, potential) -- potential is what training can never
    push a player past."""
    base = 66.0
    experience_component = min(experience_years, 14) * 1.4
    depth_component = (4 - min(depth_index, 12)) * 1.5
    noise = random.uniform(-3, 3)
    baseline = max(45, min(84, round(base + experience_component + depth_component + noise)))

    elite_chance = 0.02 + (0.05 if depth_index == 0 else 0) + (0.03 if experience_years >= 8 else 0)
    if random.random() < elite_chance:
        overall = random.randint(88, 99)
        potential = min(99, overall + random.randint(0, 5))
        return overall, potential

    if age <= 24:
        headroom = random.randint(6, 14)
    elif age <= 28:
        headroom = random.randint(2, 8)
    else:
        headroom = random.randint(0, 3)
    potential = min(89, baseline + headroom)
    return baseline, potential


def import_players(db: Session) -> dict:
    league = get_or_create_league(db, "nfl")
    teams = fetch_teams()
    created = 0
    updated = 0
    skipped = 0

    for team in teams:
        team_id = team["id"]
        abbreviation = team["abbreviation"]
        print(f"Importing roster: {team['displayName']} ({abbreviation})")

        roster = fetch_roster(team_id)
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

                # ESPN lists each position group in depth-chart order --
                # index 0 is (almost always) the starter. Keyed by the raw
                # ESPN label (CB, DT, LB, ...), not the merged Position
                # bucket, so Position.DEF's ~10 aggregated real positions
                # each get their own starter-relative signal instead of
                # sharing one long counter. Real signal for
                # generate_ratings(), see its docstring.
                depth_index = position_depth.get(espn_position, 0)
                position_depth[espn_position] = depth_index + 1

                espn_id = athlete["id"]
                display_name = athlete.get("displayName", "")
                first_name = athlete.get("firstName") or display_name.split(" ")[0]
                last_name = athlete.get("lastName") or display_name.split(" ")[-1]
                age = athlete.get("age") or random.randint(22, 34)
                experience_years = (athlete.get("experience") or {}).get("years", 0)
                headshot = (athlete.get("headshot") or {}).get("href")

                existing = db.query(Player).filter(Player.espn_id == espn_id).first()

                if existing is None:
                    overall, potential = generate_ratings(experience_years, depth_index, age)
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
                        nfl_team=abbreviation,
                    )
                    db.add(player)
                    created += 1
                else:
                    existing.age = age
                    existing.photo_url = headshot
                    existing.nfl_team = abbreviation
                    new_overall, new_potential = generate_ratings(experience_years, depth_index, age)
                    if existing.team_id is None:
                        # Free agents have no training investment to lose --
                        # safe to fully re-rate with the improved formula
                        # (#19/#20) on every re-run, instead of being stuck
                        # with whatever the old random roll gave them.
                        existing.overall = new_overall
                        existing.base_overall = new_overall
                        existing.potential = new_potential
                        existing.market_price = max(
                            1, round(player_market_value(BASE_MARKET_PRICE, new_overall, age))
                        )
                    else:
                        # Owned players may have live training progress on
                        # `overall` -- only refresh the season-reset target
                        # and ceiling, so a corrected (previously stale,
                        # pre-#19/#20) baseline takes effect naturally at the
                        # next season_manager.reset_player_ratings() instead
                        # of yanking a manager's current-season gains out
                        # from under them mid-season.
                        existing.base_overall = new_overall
                        existing.potential = new_potential
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
