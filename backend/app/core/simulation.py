import random
from dataclasses import dataclass

from app.models.enums import Position, Tactic
from app.models.player import Player

# Average NFL-ish score for an evenly matched team; the OVR differential
# between offense and opposing defense shifts a team up/down from here.
BASE_TEAM_POINTS = 17.0
# Points of expected score added/removed per point of OVR advantage.
POINT_SCALE = 0.45
# Random noise as a fraction of expected score -- kept low enough that a
# real quality gap between rosters reliably shows up in the result.
SCORE_STD_RATIO = 0.16
MIN_SCORE_STD = 4.0

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


# Weight of each offensive position when averaging starter OVR into a single
# offense rating -- QBs and WRs swing games more than a backup-caliber TE or
# a kicker, so they count for more.
POSITION_WEIGHT: dict[Position, float] = {
    Position.QB: 1.4,
    Position.RB: 1.0,
    Position.WR: 1.1,
    Position.TE: 0.9,
    Position.K: 0.4,
}


def _offense_rating(lineup: dict[Position, list[Player]], weight_overrides: dict[Position, float] | None = None) -> float:
    """Weighted-average OVR of the starting offense, kept on the same 0-99
    scale as a single defensive rating so the two are directly comparable."""
    weights = dict(POSITION_WEIGHT)
    if weight_overrides:
        weights.update(weight_overrides)
    players = lineup[Position.QB] + lineup[Position.RB] + lineup[Position.WR] + lineup[Position.TE] + lineup[Position.K]
    if not players:
        return 0.0
    total_weight = sum(weights[p.position] for p in players)
    if total_weight <= 0:
        return 0.0
    return sum(p.overall * weights[p.position] for p in players) / total_weight


def compute_team_strength(players: list[Player], tactic: Tactic, opponent_tactic: Tactic) -> TeamStrength:
    lineup = select_starting_lineup(players)

    offense = _offense_rating(lineup)
    defense = float(_lineup_overall(lineup[Position.DEF]))
    variance = 1.0

    if tactic == Tactic.PASS_HEAVY:
        offense = _offense_rating(lineup, {Position.QB: 1.9, Position.WR: 1.6, Position.RB: 0.6})
        variance *= 1.3
        if opponent_tactic == Tactic.BLITZ:
            offense *= 0.92
    elif tactic == Tactic.RUN_HEAVY:
        offense = _offense_rating(lineup, {Position.RB: 1.7, Position.QB: 1.0, Position.WR: 0.8})
        variance *= 0.85
    elif tactic == Tactic.PREVENT:
        offense *= 0.92
        defense *= 1.12
        variance *= 0.82
    elif tactic == Tactic.BLITZ:
        defense *= 1.1
        variance *= 1.15
        if opponent_tactic == Tactic.RUN_HEAVY:
            defense *= 0.93

    return TeamStrength(offense=offense, defense=defense, variance=variance, lineup=lineup)


def _decompose_score(score: int) -> list[int]:
    remaining = score
    plays: list[int] = []
    while remaining > 0:
        if remaining == 1:
            # A lone point isn't a real scoring play -- an extra point only
            # ever follows a touchdown -- so fold it into the previous score.
            if plays:
                plays[-1] += 1
            else:
                plays.append(1)
            remaining = 0
            continue
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

    if points in (6, 7, 8):
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
        elif points == 8:
            play += " (sikeres 2 pontos extra próbával)"
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

    # Both offense and defense now live on the same ~0-99 OVR scale, so their
    # difference is a meaningful "who wins this matchup" signal instead of
    # being swamped by a scale mismatch between a 6-player sum and a single
    # defensive rating.
    home_net = home.offense - away.defense
    away_net = away.offense - home.defense

    home_expected = max(3.0, BASE_TEAM_POINTS + home_net * POINT_SCALE)
    away_expected = max(3.0, BASE_TEAM_POINTS + away_net * POINT_SCALE)

    home_std = max(MIN_SCORE_STD, home_expected * SCORE_STD_RATIO) * home.variance
    away_std = max(MIN_SCORE_STD, away_expected * SCORE_STD_RATIO) * away.variance

    # A real football score can never total exactly 1 point (the smallest
    # non-zero scores are 2/3/6/7/8) -- for a heavily outmatched team this
    # isn't just a one-in-a-million rounding fluke, so clamp it down to a
    # clean shutout rather than let it reach _decompose_score.
    home_score = max(0, round(random.gauss(home_expected, home_std)))
    away_score = max(0, round(random.gauss(away_expected, away_std)))
    if home_score == 1:
        home_score = 0
    if away_score == 1:
        away_score = 0

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
