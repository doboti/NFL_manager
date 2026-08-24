from sqlalchemy.orm import Session

from app.core.game_data import player_market_value
from app.models.enums import Position
from app.models.player import Player
from app.models.team import Team

BASE_MARKET_PRICE = 1000


class RosterError(Exception):
    pass


def _get_own_player(db: Session, team: Team, player_id: int) -> Player:
    player = db.query(Player).filter(Player.id == player_id, Player.team_id == team.id).first()
    if player is None:
        raise RosterError("Player not found on this team")
    return player


def release_player(db: Session, team: Team, player_id: int) -> Player:
    player = _get_own_player(db, team, player_id)

    player.team_id = None
    player.listed_for_transfer = False
    player.asking_price = None
    player.market_price = max(
        1, round(player_market_value(BASE_MARKET_PRICE, player.overall, player.age))
    )

    db.commit()
    db.refresh(player)
    return player


def list_for_transfer(db: Session, team: Team, player_id: int, asking_price: int) -> Player:
    if asking_price < 1:
        raise RosterError("Asking price must be positive")

    player = _get_own_player(db, team, player_id)
    player.listed_for_transfer = True
    player.asking_price = asking_price

    db.commit()
    db.refresh(player)
    return player


def unlist_from_transfer(db: Session, team: Team, player_id: int) -> Player:
    player = _get_own_player(db, team, player_id)
    player.listed_for_transfer = False

    db.commit()
    db.refresh(player)
    return player


def buy_transfer_listed_player(db: Session, buyer_team: Team, player_id: int) -> Player:
    player = (
        db.query(Player)
        .filter(Player.id == player_id, Player.listed_for_transfer.is_(True))
        .first()
    )
    if player is None:
        raise RosterError("Player is not listed for transfer")

    if player.team_id == buyer_team.id:
        raise RosterError("You already own this player")

    price = player.asking_price or 0
    if buyer_team.franchise_capital < price:
        raise RosterError("Not enough Franchise Tőke")

    seller_team = player.team

    buyer_team.franchise_capital -= price
    if seller_team is not None:
        seller_team.franchise_capital += price

    player.team_id = buyer_team.id
    player.listed_for_transfer = False
    player.asking_price = None

    db.commit()
    db.refresh(player)
    return player


def set_starting_lineup(
    db: Session,
    team: Team,
    qb_id: int,
    rb_ids: list[int],
    wr_ids: list[int],
    te_id: int,
    def_id: int,
) -> list[Player]:
    required: list[tuple[int, Position]] = [
        (qb_id, Position.QB),
        *[(pid, Position.RB) for pid in rb_ids],
        *[(pid, Position.WR) for pid in wr_ids],
        (te_id, Position.TE),
        (def_id, Position.DEF),
    ]

    if len(rb_ids) != 2 or len(wr_ids) != 2:
        raise RosterError("Exactly 2 RB and 2 WR are required")

    ids = [pid for pid, _ in required]
    if len(set(ids)) != len(ids):
        raise RosterError("A player cannot fill two slots at once")

    players = db.query(Player).filter(Player.id.in_(ids), Player.team_id == team.id).all()
    players_by_id = {p.id: p for p in players}

    for pid, expected_position in required:
        player = players_by_id.get(pid)
        if player is None:
            raise RosterError("Player not found on this team")
        if player.position != expected_position:
            raise RosterError(f"{player.first_name} {player.last_name} is not a {expected_position.value}")

    for player in team.players:
        player.is_starter = player.id in players_by_id

    db.commit()
    return [p for p in team.players if p.is_starter]
