import random
from dataclasses import dataclass

from app.models.enums import Position, Tactic
from app.models.player import Player

LINEUP_SLOTS = {
    Position.QB: 1,
    Position.RB: 2,
    Position.WR: 2,
    Position.TE: 1,
    Position.K: 1,
    Position.DEF: 1,
}


def select_starting_lineup(players: list[Player]) -> dict[Position, list[Player]]:
    """Prefers the manager's chosen starters; for any slot without enough of
    them (never set, or a starter got traded/released/injured away), falls
    back to the best available player at that position by OVR."""
    lineup: dict[Position, list[Player]] = {}
    for position, slots in LINEUP_SLOTS.items():
        position_players = [p for p in players if p.position == position]
        starters = sorted(
            (p for p in position_players if p.is_starter), key=lambda p: p.overall, reverse=True
        )
        if len(starters) >= slots:
            lineup[position] = starters[:slots]
            continue

        candidates = sorted(position_players, key=lambda p: p.overall, reverse=True)
        lineup[position] = candidates[:slots]
    return lineup


@dataclass
class TeamStrength:
    offense: float
    defense: float
    variance: float
    lineup: dict[Position, list[Player]]


def _lineup_overall(players: list[Player]) -> int:
    return sum(p.overall for p in players)


def compute_team_strength(players: list[Player], tactic: Tactic, opponent_tactic: Tactic) -> TeamStrength:
    lineup = select_starting_lineup(players)

    qb_ovr = _lineup_overall(lineup[Position.QB])
    rb_ovr = _lineup_overall(lineup[Position.RB])
    wr_ovr = _lineup_overall(lineup[Position.WR])
    te_ovr = _lineup_overall(lineup[Position.TE])
    k_ovr = _lineup_overall(lineup[Position.K])
    def_ovr = _lineup_overall(lineup[Position.DEF])

    offense = qb_ovr + rb_ovr + wr_ovr + te_ovr + k_ovr * 0.5
    defense = float(def_ovr)
    variance = 1.0

    if tactic == Tactic.PASS_HEAVY:
        offense = offense - (qb_ovr + wr_ovr) + (qb_ovr + wr_ovr) * 1.2
        variance *= 1.35
        if opponent_tactic == Tactic.BLITZ:
            offense *= 0.9
    elif tactic == Tactic.RUN_HEAVY:
        offense = offense - rb_ovr + rb_ovr * 1.2
        variance *= 0.85
    elif tactic == Tactic.PREVENT:
        offense *= 0.9
        defense *= 1.15
        variance *= 0.8
    elif tactic == Tactic.BLITZ:
        defense *= 1.1
        variance *= 1.15

    return TeamStrength(offense=offense, defense=defense, variance=variance, lineup=lineup)


def _decompose_score(score: int) -> list[int]:
    remaining = score
    plays: list[int] = []
    while remaining > 0:
        if remaining >= 7:
            pts = 7 if random.random() < 0.75 else random.choice([3, 6])
        elif remaining >= 6:
            pts = random.choice([3, 6])
        elif remaining >= 3:
            pts = 3
        else:
            pts = remaining
        pts = min(pts, remaining)
        plays.append(pts)
        remaining -= pts
    return plays


def _play_description(team_name: str, quarter: int, points: int, lineup: dict[Position, list[Player]], tactic: Tactic) -> str:
    qb = lineup[Position.QB][0] if lineup[Position.QB] else None
    rb = lineup[Position.RB][0] if lineup[Position.RB] else None
    wr = lineup[Position.WR][0] if lineup[Position.WR] else None
    k = lineup[Position.K][0] if lineup[Position.K] else None

    if points == 7 or points == 6:
        prefer_pass = tactic == Tactic.PASS_HEAVY or (tactic != Tactic.RUN_HEAVY and random.random() < 0.55)
        if prefer_pass and qb and wr:
            yards = random.randint(5, 55)
            play = f"{qb.first_name} {qb.last_name} egy {yards} yardos passzt ad {wr.first_name} {wr.last_name}-nek -> Touchdown"
        elif rb:
            yards = random.randint(1, 30)
            play = f"{rb.first_name} {rb.last_name} {yards} yardos futással pontszerez -> Touchdown"
        else:
            play = "Touchdown"
        if points == 6:
            play += " (a mezőnygól kísérlet kimarad)"
    elif points == 3 and k:
        play = f"{k.first_name} {k.last_name} mezőnygólt értékesít"
    elif points == 2:
        play = "Biztonsági pont (safety)"
    else:
        play = f"{points} pontos pontszerzés"

    return f"[{team_name}] {quarter}. negyed: {play} (+{points})"


def simulate_match(
    home_name: str,
    away_name: str,
    home_players: list[Player],
    away_players: list[Player],
    home_tactic: Tactic = Tactic.BALANCED,
    away_tactic: Tactic = Tactic.BALANCED,
) -> dict:
    home = compute_team_strength(home_players, home_tactic, away_tactic)
    away = compute_team_strength(away_players, away_tactic, home_tactic)

    home_net = max(0.0, home.offense - away.defense * 0.6)
    away_net = max(0.0, away.offense - home.defense * 0.6)

    home_expected = max(3.0, home_net * 0.07)
    away_expected = max(3.0, away_net * 0.07)

    home_score = max(0, round(random.gauss(home_expected, home_expected * 0.25 * home.variance)))
    away_score = max(0, round(random.gauss(away_expected, away_expected * 0.25 * away.variance)))

    plays: list[tuple[int, int, str]] = []
    for pts in _decompose_score(home_score):
        plays.append((random.randint(1, 4), pts, "home"))
    for pts in _decompose_score(away_score):
        plays.append((random.randint(1, 4), pts, "away"))
    plays.sort(key=lambda p: p[0])

    log = []
    for quarter, pts, side in plays:
        if side == "home":
            log.append(_play_description(home_name, quarter, pts, home.lineup, home_tactic))
        else:
            log.append(_play_description(away_name, quarter, pts, away.lineup, away_tactic))

    return {
        "home_score": home_score,
        "away_score": away_score,
        "home_power": round(home.offense),
        "away_power": round(away.offense),
        "play_log": log,
    }
