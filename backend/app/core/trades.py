from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import TradeStatus
from app.models.player import Player
from app.models.team import Team
from app.models.trade_offer import TradeOffer


class TradeError(Exception):
    pass


def create_offer(
    db: Session,
    from_team: Team,
    to_team_id: int,
    target_player_id: int,
    offered_player_id: int | None,
    cash_offer: int,
) -> TradeOffer:
    if to_team_id == from_team.id:
        raise TradeError("Cannot trade with yourself")

    to_team = db.query(Team).filter(Team.id == to_team_id).first()
    if to_team is None:
        raise TradeError("Target team not found")

    if to_team.league_id != from_team.league_id:
        raise TradeError("Cannot trade with a team from a different league")

    target_player = db.query(Player).filter(Player.id == target_player_id, Player.team_id == to_team_id).first()
    if target_player is None:
        raise TradeError("Target player not found on that team")

    if offered_player_id is not None:
        offered_player = (
            db.query(Player).filter(Player.id == offered_player_id, Player.team_id == from_team.id).first()
        )
        if offered_player is None:
            raise TradeError("Offered player not found on your team")

    if cash_offer < 0:
        raise TradeError("Cash offer cannot be negative")

    if cash_offer > from_team.franchise_capital:
        raise TradeError("Not enough Franchise Tőke for this offer")

    offer = TradeOffer(
        from_team_id=from_team.id,
        to_team_id=to_team_id,
        target_player_id=target_player_id,
        offered_player_id=offered_player_id,
        cash_offer=cash_offer,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def _get_pending_offer(db: Session, offer_id: int) -> TradeOffer:
    offer = db.query(TradeOffer).filter(TradeOffer.id == offer_id).first()
    if offer is None:
        raise TradeError("Offer not found")
    if offer.status != TradeStatus.PENDING:
        raise TradeError("Offer is no longer pending")
    return offer


def accept_offer(db: Session, to_team: Team, offer_id: int) -> TradeOffer:
    offer = _get_pending_offer(db, offer_id)
    if offer.to_team_id != to_team.id:
        raise TradeError("This offer is not addressed to your team")

    target_player = db.query(Player).filter(Player.id == offer.target_player_id).first()
    if target_player is None or target_player.team_id != to_team.id:
        raise TradeError("Target player is no longer on your team")

    from_team = db.query(Team).filter(Team.id == offer.from_team_id).first()
    if from_team is None:
        raise TradeError("Offering team no longer exists")

    offered_player = None
    if offer.offered_player_id is not None:
        offered_player = db.query(Player).filter(Player.id == offer.offered_player_id).first()
        if offered_player is None or offered_player.team_id != from_team.id:
            raise TradeError("Offered player is no longer available")

    if offer.cash_offer > from_team.franchise_capital:
        raise TradeError("The offering team no longer has enough Franchise Tőke")

    target_player.team_id = from_team.id
    if offered_player is not None:
        offered_player.team_id = to_team.id
    if offer.cash_offer:
        from_team.franchise_capital -= offer.cash_offer
        to_team.franchise_capital += offer.cash_offer

    offer.status = TradeStatus.ACCEPTED
    offer.resolved_at = datetime.now(timezone.utc)

    _cancel_conflicting_offers(db, offer)

    db.commit()
    db.refresh(offer)
    return offer


def _cancel_conflicting_offers(db: Session, accepted_offer: TradeOffer) -> None:
    involved_player_ids = [accepted_offer.target_player_id]
    if accepted_offer.offered_player_id is not None:
        involved_player_ids.append(accepted_offer.offered_player_id)

    conflicting = (
        db.query(TradeOffer)
        .filter(
            TradeOffer.id != accepted_offer.id,
            TradeOffer.status == TradeStatus.PENDING,
            (
                TradeOffer.target_player_id.in_(involved_player_ids)
                | TradeOffer.offered_player_id.in_(involved_player_ids)
            ),
        )
        .all()
    )
    for offer in conflicting:
        offer.status = TradeStatus.CANCELLED
        offer.resolved_at = datetime.now(timezone.utc)


def reject_offer(db: Session, to_team: Team, offer_id: int) -> TradeOffer:
    offer = _get_pending_offer(db, offer_id)
    if offer.to_team_id != to_team.id:
        raise TradeError("This offer is not addressed to your team")

    offer.status = TradeStatus.REJECTED
    offer.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(offer)
    return offer


def cancel_offer(db: Session, from_team: Team, offer_id: int) -> TradeOffer:
    offer = _get_pending_offer(db, offer_id)
    if offer.from_team_id != from_team.id:
        raise TradeError("This is not your offer")

    offer.status = TradeStatus.CANCELLED
    offer.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(offer)
    return offer
