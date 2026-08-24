from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.roster import RosterError, buy_transfer_listed_player
from app.models.player import Player
from app.models.team import Team
from app.models.user import User
from app.schemas.player import PlayerOut
from app.schemas.team import TeamOut

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.get("/", response_model=list[PlayerOut])
def list_transfer_listed(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    query = db.query(Player).filter(Player.listed_for_transfer.is_(True))
    if team is not None:
        query = query.filter(Player.team_id != team.id)
    return query.order_by(Player.overall.desc()).all()


@router.post("/{player_id}/buy", response_model=TeamOut)
def buy(
    player_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    try:
        buy_transfer_listed_player(db, team, player_id)
    except RosterError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.refresh(team)
    return team
