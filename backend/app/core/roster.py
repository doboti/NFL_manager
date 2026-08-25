from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.game_data import player_market_value
from app.core.injuries import injured_player_ids
from app.core.training import training_player_ids
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
    qb_id: int | None,
    rb_ids: list[int | None],
    wr_ids: list[int | None],
    te_id: int | None,
    def_id: int | None,
    k_id: int | None,
) -> list[Player]:
    """Any slot left as None gets auto-filled with the best-OVR available
    (not already used, not currently training) player at that position --
    matching what the UI has always told players would happen, which
    previously only applied at simulation time, not at save time: the form
    actually required every slot filled in before the button would even
    enable, so a single-slot change was often impossible to save at all."""
    if len(rb_ids) != 2 or len(wr_ids) != 2:
        raise RosterError("Exactly 2 RB and 2 WR slots are required")

    slots: list[tuple[int | None, Position]] = [
        (qb_id, Position.QB),
        (rb_ids[0], Position.RB),
        (rb_ids[1], Position.RB),
        (wr_ids[0], Position.WR),
        (wr_ids[1], Position.WR),
        (te_id, Position.TE),
        (def_id, Position.DEF),
        (k_id, Position.K),
    ]

    explicit_ids = [pid for pid, _ in slots if pid is not None]
    if len(set(explicit_ids)) != len(explicit_ids):
        raise RosterError("A player cannot fill two slots at once")

    roster_players = team.players
    players_by_id = {p.id: p for p in roster_players}
    by_position: dict[Position, list[Player]] = {}
    for p in roster_players:
        by_position.setdefault(p.position, []).append(p)

    now = now_utc(db)
    training_ids = training_player_ids(db, team.id, now)
    injured_ids = injured_player_ids(db, team.id, now)
    unavailable_ids = training_ids | injured_ids

    used_ids: set[int] = set()
    for pid, expected_position in slots:
        if pid is None:
            continue
        player = players_by_id.get(pid)
        if player is None:
            raise RosterError("Player not found on this team")
        if player.position != expected_position:
            raise RosterError(f"{player.first_name} {player.last_name} is not a {expected_position.value}")
        if pid in training_ids:
            raise RosterError(f"{player.first_name} {player.last_name} is currently training and can't start")
        if pid in injured_ids:
            raise RosterError(f"{player.first_name} {player.last_name} is injured and can't start")
        used_ids.add(pid)

    for pid, expected_position in slots:
        if pid is not None:
            continue
        candidates = [
            p for p in by_position.get(expected_position, []) if p.id not in used_ids and p.id not in unavailable_ids
        ]
        if not candidates:
            raise RosterError(f"No available {expected_position.value} player to auto-fill that slot")
        used_ids.add(max(candidates, key=lambda p: p.overall).id)

    for player in team.players:
        player.is_starter = player.id in used_ids

    db.commit()
    return [p for p in team.players if p.is_starter]
