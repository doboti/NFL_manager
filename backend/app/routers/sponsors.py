from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.game_data import MAX_ACTIVE_SPONSORS, SPONSOR_TEMPLATES, SPONSOR_TEMPLATES_BY_KEY
from app.models.enums import SponsorType
from app.models.sponsor import Sponsor
from app.models.team import Team
from app.models.user import User
from app.schemas.sponsor import SignSponsorRequest, SponsorOut, SponsorTemplate

router = APIRouter(prefix="/sponsors", tags=["sponsors"])


def _get_team(current_user: User, db: Session) -> Team:
    team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.get("/", response_model=list[SponsorOut])
def list_sponsors(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    return team.sponsors


@router.get("/templates", response_model=list[SponsorTemplate])
def get_templates():
    return SPONSOR_TEMPLATES


@router.post("/sign", response_model=SponsorOut, status_code=status.HTTP_201_CREATED)
def sign_sponsor(
    payload: SignSponsorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = _get_team(current_user, db)
    if len(team.sponsors) >= MAX_ACTIVE_SPONSORS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 3 active sponsors")

    template = SPONSOR_TEMPLATES_BY_KEY.get(payload.template_key)
    if template is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown sponsor template")

    if any(s.template_key == payload.template_key for s in team.sponsors):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This sponsor is already signed")

    now = now_utc(db)
    sponsor = Sponsor(
        team_id=team.id,
        template_key=template["key"],
        name=template["name"],
        sponsor_type=SponsorType(template["sponsor_type"]),
        daily_amount=template["daily_amount"],
        win_bonus=template["win_bonus"],
        signed_at=now,
        expires_at=now + timedelta(days=template["duration_days"]),
    )
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return sponsor
