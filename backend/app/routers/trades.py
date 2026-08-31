from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.bots import resolve_bot_trade_offers
from app.core.clock import now_utc
from app.core.database import get_db
from app.core.deps import get_current_user, resolve_active_team
from app.core.trades import TradeError, accept_offer, cancel_offer, create_offer, expire_stale_offers, reject_offer
from app.models.player import Player
from app.models.team import Team
from app.models.trade_offer import TradeOffer
from app.models.user import User
from app.schemas.trade import CreateTradeOfferRequest, PlayerSearchResult, TradeOfferOut

router = APIRouter(prefix="/trades", tags=["trades"])


def _get_team(current_user: User, db: Session) -> Team:
    team = resolve_active_team(db, current_user)
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
    # Belt-and-suspenders alongside the background scheduler (which resolves
    # due bot offers every 15 min): also resolve opportunistically on every
    # page load, so a manager sees up-to-date replies even if the scheduled
    # job hasn't fired yet for whatever reason.
    now = now_utc(db)
    resolve_bot_trade_offers(db, now)
    expire_stale_offers(db, now)
    query = db.query(TradeOffer).filter(
        or_(TradeOffer.from_team_id == team.id, TradeOffer.to_team_id == team.id)
    )
    return _query_options(query).order_by(TradeOffer.created_at.desc()).all()


@router.get("/search", response_model=list[PlayerSearchResult])
def search_players(
    name: str = Query(..., min_length=1, max_length=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """#22: find a player by name anywhere in your own league (any team, or
    a free agent) and see who currently has them and their overall --
    scoped to your own league so this can't leak players from other
    leagues (college into an NFL search, etc.), same concern as #24."""
    team = _get_team(current_user, db)
    pattern = f"%{name}%"
    players = (
        db.query(Player)
        .options(joinedload(Player.team))
        .filter(
            Player.league_id == team.league_id,
            (Player.first_name.ilike(pattern)) | (Player.last_name.ilike(pattern)),
        )
        .order_by(Player.overall.desc())
        .limit(30)
        .all()
    )
    return [
        PlayerSearchResult(
            id=p.id,
            first_name=p.first_name,
            last_name=p.last_name,
            position=p.position,
            overall=p.overall,
            potential=p.potential,
            team_id=p.team_id,
            team_name=p.team.name if p.team is not None else None,
        )
        for p in players
    ]


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
