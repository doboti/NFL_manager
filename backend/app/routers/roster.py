from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.roster import (
    RosterError,
    list_for_transfer,
    release_player,
    set_starting_lineup,
    unlist_from_transfer,
)
from app.models.team import Team
from app.models.user import User
from app.schemas.player import PlayerOut
from app.schemas.roster import ListForTransferRequest, SetLineupRequest

router = APIRouter(prefix="/roster", tags=["roster"])


def _get_team(current_user: User, db: Session) -> Team:
    team = (
        db.query(Team)
        .options(joinedload(Team.players))
        .filter(Team.owner_id == current_user.id)
        .first()
    )
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.post("/{player_id}/release", response_model=PlayerOut)
def release(
    player_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        return release_player(db, team, player_id)
    except RosterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{player_id}/list-for-transfer", response_model=PlayerOut)
def list_player(
    player_id: int,
    payload: ListForTransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        return list_for_transfer(db, team, player_id, payload.asking_price)
    except RosterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{player_id}/unlist", response_model=PlayerOut)
def unlist_player(
    player_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        return unlist_from_transfer(db, team, player_id)
    except RosterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/lineup", response_model=list[PlayerOut])
def get_lineup(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    return [p for p in team.players if p.is_starter]


@router.put("/lineup", response_model=list[PlayerOut])
def put_lineup(
    payload: SetLineupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    try:
        return set_starting_lineup(
            db, team, payload.qb_id, payload.rb_ids, payload.wr_ids, payload.te_id, payload.def_id, payload.k_id
        )
    except RosterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
