"""Dev/testing utility: wipes all users, teams, and everything tied to a
franchise (sponsors, training, stadium upgrades, trade offers, matches,
season/playoff state), so the app can be tried from a clean slate.

Imported real players (NFL and college) are NOT deleted -- they're just
returned to the free-agent pool (team_id cleared) so re-claiming a team
works normally.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.reset_test_data
"""

from sqlalchemy.orm import Session

from app.core.bots import seed_bot_teams
from app.core.clock import list_leagues
from app.core.database import SessionLocal
from app.core.game_data import player_market_value
from app.models.enums import SeasonPhase
from app.models.game_clock import GameClock
from app.models.match import Match
from app.models.player import Player
from app.models.season_history import SeasonHistory
from app.models.sponsor import Sponsor
from app.models.stadium_upgrade import StadiumUpgrade
from app.models.team import Team
from app.models.trade_offer import TradeOffer
from app.models.training import TrainingSession
from app.models.user import User


def reset_test_data(db: Session) -> dict:
    counts = {
        "trade_offers": db.query(TradeOffer).delete(),
        "matches": db.query(Match).delete(),
        "stadium_upgrades": db.query(StadiumUpgrade).delete(),
        "training_sessions": db.query(TrainingSession).delete(),
        "sponsors": db.query(Sponsor).delete(),
        "season_history": db.query(SeasonHistory).delete(),
        "game_clock_reset": db.query(GameClock).delete(),
    }

    # Leagues themselves aren't deleted -- every real player permanently
    # belongs to one (Player.league_id), so recreating the rows would just
    # orphan that FK. Reset each one's season/playoff state back to day one
    # instead, which is what "clean slate" actually means here.
    leagues = list_leagues(db)
    for league in leagues:
        league.season = 1
        league.phase = SeasonPhase.REGULAR
        league.season_day = 0
        league.current_playoff_round = None
    counts["leagues_reset"] = len(leagues)

    owned_players = db.query(Player).filter(Player.team_id.isnot(None)).all()
    for player in owned_players:
        player.team_id = None
        player.listed_for_transfer = False
        player.asking_price = None
        player.market_price = max(1, round(player_market_value(1000, player.overall, player.age)))
    counts["players_freed"] = len(owned_players)
    db.flush()

    counts["teams"] = db.query(Team).delete()
    counts["users"] = db.query(User).delete()

    db.commit()

    bot_teams_seeded = 0
    for league in leagues:
        bot_teams_seeded += seed_bot_teams(db, league)
    counts["bot_teams_seeded"] = bot_teams_seeded
    return counts


if __name__ == "__main__":
    session = SessionLocal()
    try:
        summary = reset_test_data(session)
        print(summary)
    finally:
        session.close()
