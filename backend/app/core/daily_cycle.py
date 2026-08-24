from sqlalchemy.orm import Session, joinedload

from app.core.bots import apply_bot_progression, resolve_bot_trade_offers
from app.core.clock import get_or_create_default_league, now_utc
from app.core.economy import apply_sponsor_payouts, apply_stadium_revenue
from app.core.league_schedule import ensure_fixtures_scheduled
from app.core.market import refill_market
from app.core.season_manager import advance_playoffs, advance_regular_season_day
from app.core.simulation import simulate_match
from app.models.enums import SeasonPhase
from app.models.match import Match
from app.models.team import Team


def run_daily_cycle(db: Session) -> dict:
    league = get_or_create_default_league(db)

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

        result = simulate_match(home.name, away.name, home.players, away.players, home.tactic, away.tactic)

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

    teams = db.query(Team).options(joinedload(Team.sponsors)).all()
    economy_summary = []
    for team in teams:
        stadium_revenue = apply_stadium_revenue(team)
        sponsor_revenue = apply_sponsor_payouts(db, team, won_today.get(team.id))
        economy_summary.append(
            {
                "team": team.name,
                "stadium_revenue": stadium_revenue,
                "sponsor_revenue": sponsor_revenue,
                "new_balance": team.franchise_capital,
            }
        )

    new_market_players = refill_market(db)

    if league.phase == SeasonPhase.REGULAR:
        advance_regular_season_day(db, league, now)

    playoff_event = None
    if league.phase == SeasonPhase.PLAYOFFS:
        playoff_event = advance_playoffs(db, league, now)

    bot_progression_count = apply_bot_progression(db, league)

    ensure_fixtures_scheduled(db, league)

    db.commit()

    bot_trades = resolve_bot_trade_offers(db)

    return {
        "matches": match_results,
        "economy": economy_summary,
        "new_market_players": new_market_players,
        "bot_trades": bot_trades,
        "season": {"season": league.season, "phase": league.phase.value, "day": league.season_day},
        "playoff_event": playoff_event,
        "bot_progression_count": bot_progression_count,
    }
