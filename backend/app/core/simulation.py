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


def _prefer_pass(tactic: Tactic) -> bool:
    """Same tendency every drive/play uses to pick pass vs. run, so the
    approach plays and the final scoring play stay tactic-consistent."""
    if tactic == Tactic.RUN_HEAVY:
        return False
    return tactic == Tactic.PASS_HEAVY or random.random() < 0.55


def _player_ref(player: Player | None) -> dict | None:
    if player is None:
        return None
    return {"first_name": player.first_name, "last_name": player.last_name, "photo_url": player.photo_url}


def _approach_play(
    quarter: int,
    offense_side: str,
    team_name: str,
    lineup: dict[Position, list[Player]],
    tactic: Tactic,
    current_yard: int,
    direction: int,
) -> tuple[dict, int]:
    """One non-scoring play inside a drive -- pass or run, for pacing and
    visual variety (including the occasional incomplete pass) before the
    drive's outcome (a score, or a punt for filler drives)."""
    qb = lineup[Position.QB][0] if lineup[Position.QB] else None
    rb = lineup[Position.RB][0] if lineup[Position.RB] else None
    wr = lineup[Position.WR][0] if lineup[Position.WR] else None

    if _prefer_pass(tactic) and qb and wr:
        success = random.random() < 0.68
        yards = random.randint(3, 22) if success else 0
        new_yard = current_yard + direction * yards
        if success:
            text = f"[{team_name}] {quarter}. negyed: {qb.first_name} {qb.last_name} passza {wr.first_name} {wr.last_name}-hez, {yards} yard"
        else:
            text = f"[{team_name}] {quarter}. negyed: {qb.first_name} {qb.last_name} passza {wr.first_name} {wr.last_name} felé -- labdaszerzés nélkül"
        return (
            {
                "quarter": quarter,
                "offense": offense_side,
                "play_type": "pass",
                "success": success,
                "start_yard": current_yard,
                "end_yard": new_yard,
                "yards": yards if success else 0,
                "result": "gain" if success else "incomplete",
                "points": 0,
                "primary_player": _player_ref(qb),
                "secondary_player": _player_ref(wr),
                "text": text,
            },
            new_yard,
        )

    if rb:
        yards = random.randint(1, 12)
        new_yard = current_yard + direction * yards
        text = f"[{team_name}] {quarter}. negyed: {rb.first_name} {rb.last_name} fut {yards} yardot"
        return (
            {
                "quarter": quarter,
                "offense": offense_side,
                "play_type": "run",
                "success": True,
                "start_yard": current_yard,
                "end_yard": new_yard,
                "yards": yards,
                "result": "gain",
                "points": 0,
                "primary_player": _player_ref(rb),
                "secondary_player": None,
                "text": text,
            },
            new_yard,
        )

    # Degenerate roster (no usable QB/WR/RB) -- shouldn't happen with a real
    # imported roster, but never crash a match over it.
    return (
        {
            "quarter": quarter,
            "offense": offense_side,
            "play_type": "run",
            "success": True,
            "start_yard": current_yard,
            "end_yard": current_yard,
            "yards": 0,
            "result": "gain",
            "points": 0,
            "primary_player": None,
            "secondary_player": None,
            "text": f"[{team_name}] {quarter}. negyed: rövid játék",
        },
        current_yard,
    )


def _final_scoring_play(
    quarter: int,
    offense_side: str,
    team_name: str,
    lineup: dict[Position, list[Player]],
    tactic: Tactic,
    current_yard: int,
    points: int,
) -> dict:
    """The scoring play itself -- same wording/decision logic the old
    _play_description used (kept byte-for-byte compatible so `play_log`
    reads exactly as it did before), now also emitting the structured
    fields the animated replay needs."""
    qb = lineup[Position.QB][0] if lineup[Position.QB] else None
    rb = lineup[Position.RB][0] if lineup[Position.RB] else None
    wr = lineup[Position.WR][0] if lineup[Position.WR] else None
    k = lineup[Position.K][0] if lineup[Position.K] else None

    goal_yard = 100 if offense_side == "home" else 0
    primary: Player | None = None
    secondary: Player | None = None

    if points in (6, 7, 8):
        prefer_pass = _prefer_pass(tactic)
        if prefer_pass and qb and wr:
            yards = abs(goal_yard - current_yard)
            play = f"{qb.first_name} {qb.last_name} egy {yards} yardos passzt ad {wr.first_name} {wr.last_name}-nek -> Touchdown"
            primary, secondary, play_type = qb, wr, "pass"
        elif rb:
            yards = abs(goal_yard - current_yard)
            play = f"{rb.first_name} {rb.last_name} {yards} yardos futással pontszerez -> Touchdown"
            primary, play_type = rb, "run"
        else:
            play = "Touchdown"
            play_type = "run"
        if points == 6:
            play += " (a mezőnygól kísérlet kimarad)"
        elif points == 8:
            play += " (sikeres 2 pontos extra próbával)"
        result = "touchdown"
        end_yard = goal_yard
    elif points == 3 and k:
        play = f"{k.first_name} {k.last_name} mezőnygólt értékesít"
        primary, play_type = k, "field_goal"
        result = "field_goal"
        end_yard = current_yard
    elif points == 2:
        play = "Biztonsági pont (safety)"
        play_type = "safety"
        result = "safety"
        end_yard = current_yard
    else:
        play = f"{points} pontos pontszerzés"
        play_type = "run"
        result = "gain"
        end_yard = current_yard

    text = f"[{team_name}] {quarter}. negyed: {play} (+{points})"

    return {
        "quarter": quarter,
        "offense": offense_side,
        "play_type": play_type,
        "success": True,
        "start_yard": current_yard,
        "end_yard": end_yard,
        "yards": abs(end_yard - current_yard),
        "result": result,
        "points": points,
        "primary_player": _player_ref(primary),
        "secondary_player": _player_ref(secondary),
        "text": text,
    }


def _generate_drive(
    quarter: int,
    offense_side: str,
    team_name: str,
    lineup: dict[Position, list[Player]],
    tactic: Tactic,
    points: int | None,
) -> list[dict]:
    """Builds one possession as a list of structured play events: a few
    approach plays advancing the ball, ending either in the scoring play
    matching `points` (already decided by _decompose_score -- this never
    changes the score, only decorates how it happened) or, for a filler
    drive (points=None), a punt. Field position uses a 0-100 scale where 0
    is the home team's own goal line and 100 is the away team's."""
    if points == 2:
        # A safety is scored by the *defense* in the offense's own end
        # zone -- it doesn't fit the normal advancing-drive shape, so it's
        # just the one event.
        own_goal = 0 if offense_side == "home" else 100
        return [_final_scoring_play(quarter, offense_side, team_name, lineup, tactic, own_goal, points)]

    direction = 1 if offense_side == "home" else -1
    own_goal = 0 if offense_side == "home" else 100
    goal_yard = 100 - own_goal
    current = own_goal + direction * random.randint(20, 40)

    # Leave enough room before the goal line for the final play to still
    # make sense (a field goal needs to stop short of the end zone).
    safety_margin = 8 if points == 3 else 3

    events: list[dict] = []
    for _ in range(random.randint(1, 3)):
        remaining = abs(goal_yard - current)
        if remaining <= safety_margin + 5:
            break
        event, current = _approach_play(quarter, offense_side, team_name, lineup, tactic, current, direction)
        limit = goal_yard - direction * safety_margin
        overshot = (direction == 1 and current > limit) or (direction == -1 and current < limit)
        if overshot:
            current = limit
            event["end_yard"] = current
            event["yards"] = abs(event["end_yard"] - event["start_yard"])
        events.append(event)

    if points is None:
        k = lineup[Position.K][0] if lineup[Position.K] else None
        punter_text = f"{k.first_name} {k.last_name} rúgása" if k else "Rúgás"
        events.append(
            {
                "quarter": quarter,
                "offense": offense_side,
                "play_type": "punt",
                "success": True,
                "start_yard": current,
                "end_yard": current,
                "yards": 0,
                "result": "punt",
                "points": 0,
                "primary_player": _player_ref(k),
                "secondary_player": None,
                "text": f"[{team_name}] {quarter}. negyed: {punter_text} -- labdaátadás",
            }
        )
    else:
        events.append(_final_scoring_play(quarter, offense_side, team_name, lineup, tactic, current, points))

    return events


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

    # (quarter, points, side) -- points=None marks a non-scoring filler
    # drive, added purely for pacing/watchability in the animated replay
    # and never affecting the final score above.
    drives: list[tuple[int, int | None, str]] = []
    for pts in _decompose_score(home_score):
        drives.append((random.randint(1, 4), pts, "home"))
    for pts in _decompose_score(away_score):
        drives.append((random.randint(1, 4), pts, "away"))
    for _ in range(random.randint(2, 4)):
        drives.append((random.randint(1, 4), None, random.choice(["home", "away"])))
    drives.sort(key=lambda d: d[0])

    events: list[dict] = []
    log: list[str] = []
    for quarter, pts, side in drives:
        team_name = home_name if side == "home" else away_name
        lineup = home.lineup if side == "home" else away.lineup
        tactic = home_tactic if side == "home" else away_tactic
        drive_events = _generate_drive(quarter, side, team_name, lineup, tactic, pts)
        events.extend(drive_events)
        if pts is not None:
            log.append(drive_events[-1]["text"])

    return {
        "home_score": home_score,
        "away_score": away_score,
        "home_power": round(home.offense),
        "away_power": round(away.offense),
        "play_log": log,
        "play_events": events,
    }
