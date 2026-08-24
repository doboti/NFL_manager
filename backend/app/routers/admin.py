from fastapi import APIRouter, Depends

from app.core.clock import advance_time, get_offset_seconds, now_utc, reset_time
from app.core.daily_cycle import run_daily_cycle
from app.core.database import get_db
from app.core.deps import require_admin
from app.schemas.admin import AdvanceTimeRequest, AdvanceTimeResponse, TimeStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/time", response_model=TimeStatus)
def get_time(db=Depends(get_db), current_user=Depends(require_admin)):
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
