"""One-off / periodic data import: populates the free-agent pool with real NFL
rosters from ESPN's public (unofficial) site API.

Only player names, ages and a link to ESPN's own hosted headshot image are
stored -- no photo bytes are copied or re-hosted, the frontend hotlinks the
ESPN CDN URL directly. There is no official rating in the source data, so
`overall` is a synthesized value (rank-based, see rate_candidates()
below), not a real skill rating.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.import_nfl_players
"""

import random
import time
from dataclasses import dataclass

import requests
from sqlalchemy.orm import Session

from app.core.clock import get_or_create_league
from app.core.database import SessionLocal
from app.core.game_data import NFL_OVR_PERCENTILE_CURVE, overall_from_percentile, player_market_value
from app.models.enums import Position
from app.models.league import League
from app.models.player import Player

TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams?limit=40"
ROSTER_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
LEADERS_URL = (
    "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/leaders"
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
    experience_years: int
    depth_index: int
    headshot: str | None
    team_code: str
    existing: Player | None
    overall: int = 0
    potential: int = 0


def fetch_teams() -> list[dict]:
    resp = requests.get(TEAMS_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return [t["team"] for t in data["sports"][0]["leagues"][0]["teams"]]


def fetch_roster(team_id: str) -> dict:
    resp = requests.get(ROSTER_URL.format(team_id=team_id), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


LEADER_BONUS_SCALE = 3


def fetch_leaders() -> dict[str, int]:
    """Returns {espn_id: bonus_points} summed across every ESPN top-25
    stat-category leaderboard appearance (#20 follow-up) -- rank 1 in a
    category contributes 25 points, rank 25 contributes 1, so a true
    across-the-board great player (top of several categories at once, e.g.
    a real league's leading passer *and* TD scorer) accumulates a much
    bigger bonus than someone who barely cracks one leaderboard once. This
    is a cheap, single-request real-performance signal so a genuine stat
    leader can't land in the generic depth-chart ranking's basement.
    Best-effort: any failure here just means no bonus this run, not a
    failed import (a single flaky ESPN call shouldn't abort an otherwise
    good roster fetch)."""
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
    """Depth-chart position dominates (a 3rd-string player never outranks a
    starter just for having more tenure); experience only breaks ties within
    a depth tier. A real stat-leader bonus (see fetch_leaders()) is added on
    top -- as an input to the SAME ranking rather than a separate reserved
    top slice, so it nudges rank order without ever being able to inflate
    the share of players landing above any given threshold beyond what the
    percentile curve guarantees. espn_id is a final deterministic tiebreak
    so re-running with unchanged inputs doesn't reshuffle free-agent
    ratings for no reason."""
    depth_score = -candidate.depth_index * 10 + min(candidate.experience_years, 10)
    bonus = leader_bonuses.get(candidate.espn_id, 0) * LEADER_BONUS_SCALE
    return (depth_score + bonus, candidate.espn_id)


def rate_candidates(candidates: list[Candidate], leader_bonuses: dict[str, int]) -> None:
    """Ranks each position group independently and maps rank -> overall via
    NFL_OVR_PERCENTILE_CURVE, guaranteeing the target distribution by
    construction (#20 follow-up) instead of an independent per-player random
    "elite roll" that could drift arbitrarily from the intended share. A
    separate design that reserved literal top-of-group slots for every
    leaders-list player was tried and rejected: with e.g. ~100 defensive
    leaders spread across a ~2500-player DEF pool, that alone is already 4%
    of the group, well past the intended top-1% band -- reserving slots
    proportional to *how many* real players happen to be leaders-list
    members, rather than the intended elite fraction, blew right past the
    target percentages. Folding leader status into the sort key instead
    keeps the percentile math exact regardless of how many leaders a group
    happens to contain."""
    by_position: dict[Position, list[Candidate]] = {}
    for c in candidates:
        by_position.setdefault(c.position, []).append(c)

    for group in by_position.values():
        n = len(group)
        group.sort(key=lambda c: _sort_key(c, leader_bonuses))
        for rank, c in enumerate(group):
            percentile = rank / (n - 1) if n > 1 else 1.0
            c.overall = overall_from_percentile(percentile, NFL_OVR_PERCENTILE_CURVE)

        cap = NFL_OVR_PERCENTILE_CURVE[-1][1]
        for c in group:
            if c.age <= 24:
                headroom = random.randint(6, 14)
            elif c.age <= 28:
                headroom = random.randint(2, 8)
            else:
                headroom = random.randint(0, 3)
            c.potential = min(cap, c.overall + headroom)


def import_players(db: Session, league: League | None = None) -> dict:
    """`league` defaults to the original single NFL instance for backward
    compatibility (CLI usage, existing re-runs) -- a freshly self-service
    created 2nd+ instance passes its own League row explicitly (see
    core.clock.create_league_instance)."""
    if league is None:
        league = get_or_create_league(db, "nfl")
    teams = fetch_teams()
    skipped = 0
    candidates: list[Candidate] = []
    seen_espn_ids: set[str] = set()

    for team in teams:
        team_id = team["id"]
        abbreviation = team["abbreviation"]
        print(f"Fetching roster: {team['displayName']} ({abbreviation})")

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
                # sharing one long counter.
                depth_index = position_depth.get(espn_position, 0)
                position_depth[espn_position] = depth_index + 1

                espn_id = athlete["id"]
                if espn_id in seen_espn_ids:
                    # Same athlete listed twice (e.g. offense + specialTeam) --
                    # first occurrence's depth signal wins, don't double-count.
                    continue
                seen_espn_ids.add(espn_id)

                display_name = athlete.get("displayName", "")
                first_name = athlete.get("firstName") or display_name.split(" ")[0]
                last_name = athlete.get("lastName") or display_name.split(" ")[-1]
                age = athlete.get("age") or random.randint(22, 34)
                experience_years = (athlete.get("experience") or {}).get("years", 0)
                headshot = (athlete.get("headshot") or {}).get("href")

                existing = (
                    db.query(Player)
                    .filter(Player.espn_id == espn_id, Player.league_id == league.id)
                    .first()
                )
                candidates.append(
                    Candidate(
                        espn_id=espn_id,
                        first_name=first_name,
                        last_name=last_name,
                        position=position,
                        age=age,
                        experience_years=experience_years,
                        depth_index=depth_index,
                        headshot=headshot,
                        team_code=abbreviation,
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
            existing.age = c.age
            existing.photo_url = c.headshot
            existing.nfl_team = c.team_code
            if existing.team_id is None:
                # Free agents have no training investment to lose -- safe to
                # fully re-rate with the improved formula (#19/#20) on every
                # re-run, instead of being stuck with whatever an earlier
                # run gave them.
                existing.overall = c.overall
                existing.base_overall = c.overall
                existing.potential = c.potential
                existing.market_price = max(
                    1, round(player_market_value(BASE_MARKET_PRICE, c.overall, c.age))
                )
            else:
                # Owned players may have live training progress on `overall`
                # -- only refresh the season-reset target and ceiling, so a
                # corrected (previously stale) baseline takes effect
                # naturally at the next season_manager.reset_player_ratings()
                # instead of yanking a manager's current-season gains out
                # from under them mid-season. Note: because ranking is
                # population-relative, this can shift slightly between
                # re-runs purely from *other* players' roster churn even if
                # this player's own signal didn't change -- expected, not a
                # bug.
                existing.base_overall = c.overall
                existing.potential = c.potential
                existing.market_price = max(
                    1, round(player_market_value(BASE_MARKET_PRICE, existing.overall, c.age))
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
