from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.stadium import StadiumError, collect_upgrade, get_pending_upgrade, start_upgrade
from app.models.team import Team
from app.models.user import User
from app.schemas.stadium import StadiumUpgradeOut

router = APIRouter(prefix="/stadium", tags=["stadium"])


def _get_team(current_user: User, db: Session) -> Team:
    team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.get("/upgrade", response_model=StadiumUpgradeOut | None)
def get_upgrade_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    return get_pending_upgrade(db, team.id)


@router.post("/upgrade/start", response_model=StadiumUpgradeOut, status_code=status.HTTP_201_CREATED)
def start(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    try:
        return start_upgrade(db, team)
    except StadiumError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/upgrade/collect", response_model=StadiumUpgradeOut)
def collect(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    try:
        return collect_upgrade(db, team)
    except StadiumError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
