"""One-off / periodic data import: populates the college-football free-agent
pool with real rosters from ESPN's public (unofficial) site API, for the
32-team subset in game_data.COLLEGE_TEAMS (the only college teams ESPN
actually has current roster data for that we've wired in).

Only player names and a link to ESPN's own hosted headshot image are stored
-- no photo bytes are copied or re-hosted. ESPN doesn't track an exact age
for college athletes (amateur roster data), so age is a plausible 18-23
random value; `overall` has no real-world source either and is synthesized
(rank-based, see rate_candidates() below), nudged by class year
(freshman..senior) the same way the NFL import nudges by pro experience.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.import_college_players
"""

import random
import time
from dataclasses import dataclass

import requests
from sqlalchemy.orm import Session

from app.core.clock import get_or_create_league
from app.core.database import SessionLocal
from app.core.game_data import COLLEGE_OVR_PERCENTILE_CURVE, COLLEGE_TEAMS, overall_from_percentile, player_market_value
from app.models.enums import Position
from app.models.player import Player

ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/roster"
LEADERS_URL = (
    "https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/seasons/2025/types/2/leaders"
    "?lang=en&region=us"
)
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


@dataclass
class Candidate:
    espn_id: str
    first_name: str
    last_name: str
    position: Position
    age: int
    class_years: int
    depth_index: int
    headshot: str | None
    team_code: str
    existing: Player | None
    overall: int = 0
    potential: int = 0


def fetch_roster(espn_team_id: str) -> dict:
    resp = requests.get(ROSTER_URL.format(team_id=espn_team_id), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


LEADER_BONUS_SCALE = 3


def fetch_leaders() -> dict[str, int]:
    """Same idea as the NFL import's fetch_leaders() -- a cheap, single-request
    real-performance signal from ESPN's public top-25 stat leaderboards
    (summed across every category/rank appearance, rank 1 worth 25 points
    down to rank 25 worth 1), so a genuine college stat leader can't land in
    the generic depth-chart ranking's basement. Best-effort: any failure
    just means no bonus this run."""
    try:
        resp = requests.get(LEADERS_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return {}

    bonuses: dict[str, int] = {}
    for category in data.get("categories", []):
        for rank, leader in enumerate(category.get("leaders", []), start=1):
            ref = ((leader.get("athlete") or {}).get("$ref")) or ""
            marker = "/athletes/"
            idx = ref.find(marker)
            if idx == -1:
                continue
            espn_id = ref[idx + len(marker) :].split("?")[0].split("/")[0]
            bonuses[espn_id] = bonuses.get(espn_id, 0) + max(0, 26 - rank)
    return bonuses


def _sort_key(candidate: Candidate, leader_bonuses: dict[str, int]) -> tuple[int, str]:
    """Same philosophy as the NFL import: depth-chart position dominates,
    class year only breaks ties within a depth tier, a real stat-leader
    bonus is folded into the same ranking (not a separate reserved slice --
    see the NFL import's rate_candidates() docstring for why), and espn_id
    is a final deterministic tiebreak."""
    depth_score = -candidate.depth_index * 10 + min(candidate.class_years, 5)
    bonus = leader_bonuses.get(candidate.espn_id, 0) * LEADER_BONUS_SCALE
    return (depth_score + bonus, candidate.espn_id)


def rate_candidates(candidates: list[Candidate], leader_bonuses: dict[str, int]) -> None:
    """Same rank-based approach as the NFL import's rate_candidates() (see
    its docstring, #20 follow-up): ranks each position group independently
    and maps rank -> overall via COLLEGE_OVR_PERCENTILE_CURVE, guaranteeing
    the target distribution by construction instead of an independent
    per-player random "elite roll"."""
    by_position: dict[Position, list[Candidate]] = {}
    for c in candidates:
        by_position.setdefault(c.position, []).append(c)

    for group in by_position.values():
        n = len(group)
        group.sort(key=lambda c: _sort_key(c, leader_bonuses))
        for rank, c in enumerate(group):
            percentile = rank / (n - 1) if n > 1 else 1.0
            c.overall = overall_from_percentile(percentile, COLLEGE_OVR_PERCENTILE_CURVE)

        cap = COLLEGE_OVR_PERCENTILE_CURVE[-1][1]
        for c in group:
            if c.class_years <= 1:
                headroom = random.randint(6, 14)
            elif c.class_years <= 3:
                headroom = random.randint(2, 8)
            else:
                headroom = random.randint(0, 3)
            c.potential = min(cap, c.overall + headroom)


def import_players(db: Session) -> dict:
    league = get_or_create_league(db, "college")
    skipped = 0
    candidates: list[Candidate] = []
    seen_espn_ids: set[str] = set()

    for team in COLLEGE_TEAMS:
        code = team["code"]
        print(f"Fetching roster: {team['name']} ({code})")

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
                # bucket -- see the NFL import's equivalent comment for why.
                depth_index = position_depth.get(espn_position, 0)
                position_depth[espn_position] = depth_index + 1

                espn_id = athlete["id"]
                if espn_id in seen_espn_ids:
                    continue
                seen_espn_ids.add(espn_id)

                display_name = athlete.get("displayName", "")
                first_name = athlete.get("firstName") or display_name.split(" ")[0]
                last_name = athlete.get("lastName") or display_name.split(" ")[-1]
                age = athlete.get("age") or random.randint(18, 23)
                class_years = (athlete.get("experience") or {}).get("years", 1)
                headshot = (athlete.get("headshot") or {}).get("href")

                existing = db.query(Player).filter(Player.espn_id == espn_id).first()
                candidates.append(
                    Candidate(
                        espn_id=espn_id,
                        first_name=first_name,
                        last_name=last_name,
                        position=position,
                        age=age,
                        class_years=class_years,
                        depth_index=depth_index,
                        headshot=headshot,
                        team_code=code,
                        existing=existing,
                    )
                )

        time.sleep(DELAY_BETWEEN_TEAMS)

    leader_bonuses = fetch_leaders()
    rate_candidates(candidates, leader_bonuses)

    created = 0
    updated = 0
    current_team_code = None
    for c in candidates:
        if c.team_code != current_team_code:
            if current_team_code is not None:
                db.commit()
            current_team_code = c.team_code

        if c.existing is None:
            player = Player(
                team_id=None,
                league_id=league.id,
                first_name=c.first_name,
                last_name=c.last_name,
                position=c.position,
                age=c.age,
                overall=c.overall,
                base_overall=c.overall,
                potential=c.potential,
                market_price=max(1, round(player_market_value(BASE_MARKET_PRICE, c.overall, c.age))),
                espn_id=c.espn_id,
                photo_url=c.headshot,
                nfl_team=c.team_code,
            )
            db.add(player)
            created += 1
        else:
            existing = c.existing
            existing.photo_url = c.headshot
            existing.nfl_team = c.team_code
            if existing.team_id is None:
                # Free agents have no training investment to lose -- safe to
                # fully re-rate with the improved formula on every re-run.
                existing.overall = c.overall
                existing.base_overall = c.overall
                existing.potential = c.potential
                existing.market_price = max(
                    1, round(player_market_value(BASE_MARKET_PRICE, c.overall, existing.age))
                )
            else:
                # Owned players may have live training progress on `overall`
                # -- only refresh the season-reset target and ceiling, same
                # reasoning as the NFL import.
                existing.base_overall = c.overall
                existing.potential = c.potential
                existing.market_price = max(
                    1, round(player_market_value(BASE_MARKET_PRICE, existing.overall, existing.age))
                )
            updated += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


if __name__ == "__main__":
    session = SessionLocal()
    try:
        summary = import_players(session)
        print(summary)
    finally:
        session.close()
