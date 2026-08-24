from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.training import TrainingError, collect_training, start_training
from app.models.player import Player
from app.models.team import Team
from app.models.training import TrainingSession
from app.models.user import User
from app.schemas.training import StartTrainingRequest, TrainingSessionOut

router = APIRouter(prefix="/training", tags=["training"])


def _get_team_id(current_user: User, db: Session) -> int:
    team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team.id


@router.get("/", response_model=list[TrainingSessionOut])
def list_training(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team_id = _get_team_id(current_user, db)
    return (
        db.query(TrainingSession)
        .join(Player, Player.id == TrainingSession.player_id)
        .filter(Player.team_id == team_id, TrainingSession.collected.is_(False))
        .all()
    )


@router.post("/start", response_model=TrainingSessionOut, status_code=status.HTTP_201_CREATED)
def start(
    payload: StartTrainingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_team_id(current_user, db)
    try:
        return start_training(db, team_id, payload.player_id)
    except TrainingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{session_id}/collect", response_model=TrainingSessionOut)
def collect(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_team_id(current_user, db)
    try:
        return collect_training(db, team_id, session_id)
    except TrainingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
