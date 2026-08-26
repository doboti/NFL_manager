from sqlalchemy.orm import Session, joinedload

from app.core.bots import apply_bot_progression, bot_initiate_trades, bot_list_for_transfer, resolve_bot_trade_offers
from app.core.clock import list_leagues, now_utc
from app.core.economy import apply_player_salaries, apply_sponsor_payouts, apply_stadium_revenue
from app.core.injuries import maybe_injure_player
from app.core.league_schedule import ensure_fixtures_scheduled
from app.core.season_manager import advance_playoffs, advance_regular_season_day
from app.core.simulation import select_starting_lineup, simulate_match
from app.models.enums import SeasonPhase
from app.models.match import Match
from app.models.team import Team


def run_daily_cycle(db: Session) -> dict:
    leagues = list_leagues(db)

    for league in leagues:
        ensure_fixtures_scheduled(db, league)

    now = now_utc(db)
    due_matches = (
        db.query(Match)
        .options(
            joinedload(Match.home_team).joinedload(Team.players),
            joinedload(Match.away_team).joinedload(Team.players),
        )
        .filter(Match.played.is_(False), Match.scheduled_at <= now)
        .all()
    )

    won_today: dict[int, bool] = {}
    match_results = []

    for match in due_matches:
        home = match.home_team
        away = match.away_team

        home_available = [p for p in home.players if not (p.injured_until and p.injured_until > now)]
        away_available = [p for p in away.players if not (p.injured_until and p.injured_until > now)]

        result = simulate_match(home.name, away.name, home_available, away_available, home.tactic, away.tactic)

        home_lineup = select_starting_lineup(home_available)
        away_lineup = select_starting_lineup(away_available)
        home_in_play = [p for players in home_lineup.values() for p in players]
        away_in_play = [p for players in away_lineup.values() for p in players]
        maybe_injure_player(home_in_play, now)
        maybe_injure_player(away_in_play, now)

        match.home_tactic = home.tactic
        match.away_tactic = away.tactic
        match.home_score = result["home_score"]
        match.away_score = result["away_score"]
        match.play_log = result["play_log"]
        match.played = True
        match.played_at = now

        home_won = result["home_score"] > result["away_score"]
        away_won = result["away_score"] > result["home_score"]

        if not match.is_playoff:
            if home_won:
                home.wins += 1
                away.losses += 1
            elif away_won:
                away.wins += 1
                home.losses += 1
            else:
                home.ties += 1
                away.ties += 1

        won_today[home.id] = home_won
        won_today[away.id] = away_won

        match_results.append(
            {
                "home": home.name,
                "away": away.name,
                "home_score": result["home_score"],
                "away_score": result["away_score"],
            }
        )

    db.flush()

    teams = db.query(Team).options(joinedload(Team.sponsors), joinedload(Team.players)).all()
    economy_summary = []
    for team in teams:
        stadium_revenue = apply_stadium_revenue(team)
        sponsor_revenue = apply_sponsor_payouts(db, team, won_today.get(team.id))
        salary_cost = apply_player_salaries(team)
        economy_summary.append(
            {
                "team": team.name,
                "stadium_revenue": stadium_revenue,
                "sponsor_revenue": sponsor_revenue,
                "salary_cost": salary_cost,
                "new_balance": team.franchise_capital,
            }
        )

    # Real ESPN-imported players are the sole source of free agents now (#24)
    # -- the old synthetic-filler fallback polluted the pool with
    # nonsense-named low-effort players that never cleared out once real
    # data arrived. Kept at a constant 0 for API/schema stability.
    new_market_players = 0
    season_summaries = []
    playoff_events = {}
    bot_progression_total = 0

    for league in leagues:
        if league.phase == SeasonPhase.REGULAR:
            advance_regular_season_day(db, league, now)

        if league.phase == SeasonPhase.PLAYOFFS:
            event = advance_playoffs(db, league, now)
            if event is not None:
                playoff_events[league.key] = event

        bot_progression_total += apply_bot_progression(db, league)
        bot_list_for_transfer(db, league)

        ensure_fixtures_scheduled(db, league)

        season_summaries.append(
            {"league": league.key, "season": league.season, "phase": league.phase.value, "day": league.season_day}
        )

    db.commit()

    for league in leagues:
        bot_initiate_trades(db, league, now)

    bot_trades = resolve_bot_trade_offers(db, now)

    return {
        "matches": match_results,
        "economy": economy_summary,
        "new_market_players": new_market_players,
        "bot_trades": bot_trades,
        "seasons": season_summaries,
        "playoff_events": playoff_events,
        "bot_progression_count": bot_progression_total,
    }
