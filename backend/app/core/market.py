from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.team import Team

MAX_ROSTER_SIZE = 100  # a full real NFL roster (~70-90 players) plus room for a few free-agent signings


class MarketError(Exception):
    pass


def buy_player(db: Session, team: Team, player_id: int) -> Player:
    player = (
        db.query(Player)
        .filter(Player.id == player_id, Player.league_id == team.league_id, Player.team_id.is_(None))
        .first()
    )
    if player is None:
        raise MarketError("Player not available on the market")

    if len(team.players) >= MAX_ROSTER_SIZE:
        raise MarketError("Roster is full")

    price = player.market_price or 0
    if team.franchise_capital < price:
        raise MarketError("Not enough Franchise Tőke")

    team.franchise_capital -= price
    player.team_id = team.id
    player.market_price = None

    db.commit()
    db.refresh(player)
    return player
