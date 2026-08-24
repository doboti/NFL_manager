from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.trades import TradeError, accept_offer, cancel_offer, create_offer, reject_offer
from app.models.team import Team
from app.models.trade_offer import TradeOffer
from app.models.user import User
from app.schemas.trade import CreateTradeOfferRequest, TradeOfferOut

router = APIRouter(prefix="/trades", tags=["trades"])


def _get_team(current_user: User, db: Session) -> Team:
    team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


def _query_options(db_query):
    return db_query.options(
        joinedload(TradeOffer.from_team),
        joinedload(TradeOffer.to_team),
        joinedload(TradeOffer.target_player),
        joinedload(TradeOffer.offered_player),
    )


@router.get("/", response_model=list[TradeOfferOut])
def list_offers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    query = db.query(TradeOffer).filter(
        or_(TradeOffer.from_team_id == team.id, TradeOffer.to_team_id == team.id)
    )
    return _query_options(query).order_by(TradeOffer.created_at.desc()).all()


@router.post("/offer", response_model=TradeOfferOut, status_code=status.HTTP_201_CREATED)
def offer(
    payload: CreateTradeOfferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        created = create_offer(
            db,
            team,
            payload.to_team_id,
            payload.target_player_id,
            payload.offered_player_id,
            payload.cash_offer,
        )
    except TradeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _query_options(db.query(TradeOffer).filter(TradeOffer.id == created.id)).first()


@router.post("/{offer_id}/accept", response_model=TradeOfferOut)
def accept(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        accepted = accept_offer(db, team, offer_id)
    except TradeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _query_options(db.query(TradeOffer).filter(TradeOffer.id == accepted.id)).first()


@router.post("/{offer_id}/reject", response_model=TradeOfferOut)
def reject(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        rejected = reject_offer(db, team, offer_id)
    except TradeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _query_options(db.query(TradeOffer).filter(TradeOffer.id == rejected.id)).first()


@router.post("/{offer_id}/cancel", response_model=TradeOfferOut)
def cancel(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        cancelled = cancel_offer(db, team, offer_id)
    except TradeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _query_options(db.query(TradeOffer).filter(TradeOffer.id == cancelled.id)).first()
