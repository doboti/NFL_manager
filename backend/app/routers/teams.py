from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.game_data import NFL_TEAM_NAMES_BY_CODE, NFL_TEAMS
from app.core.team_setup import TeamClaimError, avg_overall_by_team, claim_team as claim_team_core
from app.models.team import Team
from app.models.user import User
from app.schemas.team import (
    ClaimTeamRequest,
    NFLTeamOption,
    SetTacticRequest,
    TeamOut,
    TeamRosterOut,
    TeamSummary,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/available", response_model=list[NFLTeamOption])
def list_available_teams(db: Session = Depends(get_db)):
    teams_by_code = {t.nfl_team_code: t for t in db.query(Team).filter(Team.nfl_team_code.isnot(None))}
    return [
        NFLTeamOption(
            code=t["code"],
            name=t["name"],
            taken=t["code"] in teams_by_code and not teams_by_code[t["code"]].is_bot,
            controlled_by_bot=t["code"] in teams_by_code and teams_by_code[t["code"]].is_bot,
        )
        for t in NFL_TEAMS
    ]


@router.get("/", response_model=list[TeamSummary])
def list_teams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    teams = db.query(Team).filter(Team.owner_id != current_user.id).order_by(Team.name).all()
    avg_overall = avg_overall_by_team(db)
    return [
        TeamSummary(
            id=t.id,
            name=t.name,
            nfl_team_code=t.nfl_team_code,
            is_bot=t.is_bot,
            avg_overall=avg_overall.get(t.id),
        )
        for t in teams
    ]


@router.get("/me", response_model=TeamOut)
def get_my_team(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = (
        db.query(Team)
        .options(joinedload(Team.players))
        .filter(Team.owner_id == current_user.id)
        .first()
    )
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team yet")
    return team


@router.get("/{team_id}/roster", response_model=TeamRosterOut)
def get_team_roster(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).options(joinedload(Team.players)).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.post("/claim", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def claim_team(
    payload: ClaimTeamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = payload.nfl_team_code.upper()
    team_name = NFL_TEAM_NAMES_BY_CODE.get(code)
    if team_name is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown NFL team")

    try:
        team = claim_team_core(db, current_user, code, team_name)
        db.commit()
    except TeamClaimError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This NFL team has already been claimed")

    db.refresh(team)
    return team


@router.put("/tactic", response_model=TeamOut)
def set_tactic(
    payload: SetTacticRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = (
        db.query(Team)
        .options(joinedload(Team.players))
        .filter(Team.owner_id == current_user.id)
        .first()
    )
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    team.tactic = payload.tactic
    db.commit()
    db.refresh(team)
    return team
