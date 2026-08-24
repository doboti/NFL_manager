from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.clock import advance_time, get_offset_seconds, now_utc, reset_time
from app.core.daily_cycle import run_daily_cycle
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.admin import AdminUserOut, AdvanceTimeRequest, AdvanceTimeResponse, TimeStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/time", response_model=TimeStatus)
def get_time(db=Depends(get_db), current_user=Depends(get_current_user)):
    """Read-only, so any logged-in user can call it -- the frontend needs the
    current offset to render training/match countdowns correctly for
    everyone, not just admins. Only *changing* the clock is admin-gated."""
    return TimeStatus(offset_seconds=get_offset_seconds(db), virtual_now=now_utc(db))


@router.post("/advance-time", response_model=AdvanceTimeResponse)
def post_advance_time(payload: AdvanceTimeRequest, db=Depends(get_db), current_user=Depends(require_admin)):
    """Dev/test only: fast-forwards the virtual clock and immediately runs the
    daily cycle, so any training/upgrade/match that just became due resolves
    right away -- no need to wait in real time to see progress."""
    advance_time(db, payload.hours)
    daily_cycle_result = run_daily_cycle(db)
    return AdvanceTimeResponse(
        time=TimeStatus(offset_seconds=get_offset_seconds(db), virtual_now=now_utc(db)),
        daily_cycle=daily_cycle_result,
    )


@router.post("/reset-time", response_model=TimeStatus)
def post_reset_time(db=Depends(get_db), current_user=Depends(require_admin)):
    reset_time(db)
    return TimeStatus(offset_seconds=get_offset_seconds(db), virtual_now=now_utc(db))


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(User).options(joinedload(User.team)).order_by(User.id).all()
    return [
        AdminUserOut(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            is_bot=u.is_bot,
            is_admin=u.is_admin,
            team_name=u.team.name if u.team else None,
        )
        for u in users
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nem törölheted a saját fiókodat")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ez a felhasználó csapata már játszott meccset / rendelkezik történettel, így nem törölhető.",
        )
