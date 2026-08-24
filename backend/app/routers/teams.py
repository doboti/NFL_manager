from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.clock import get_or_create_league
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.game_data import LEAGUES
from app.core.team_setup import TeamClaimError, avg_overall_by_team, claim_team as claim_team_core, release_team as release_team_core
from app.models.season_history import SeasonHistory
from app.models.team import Team
from app.models.user import User
from app.schemas.team import (
    ClaimTeamRequest,
    NFLTeamOption,
    SeasonHistoryOut,
    SetTacticRequest,
    TeamOut,
    TeamRosterOut,
    TeamSummary,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/available", response_model=list[NFLTeamOption])
def list_available_teams(league_key: str, db: Session = Depends(get_db)):
    if league_key not in LEAGUES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown league")

    league = get_or_create_league(db, league_key)
    db.commit()

    teams_by_code = {
        t.nfl_team_code: t
        for t in db.query(Team).filter(Team.league_id == league.id, Team.nfl_team_code.isnot(None))
    }
    return [
        NFLTeamOption(
            code=t["code"],
            name=t["name"],
            taken=t["code"] in teams_by_code and not teams_by_code[t["code"]].is_bot,
            controlled_by_bot=t["code"] in teams_by_code and teams_by_code[t["code"]].is_bot,
        )
        for t in LEAGUES[league_key]["teams"]
    ]


@router.get("/", response_model=list[TeamSummary])
def list_teams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    my_team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if my_team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team yet")

    teams = (
        db.query(Team)
        .filter(Team.league_id == my_team.league_id, Team.owner_id != current_user.id)
        .order_by(Team.name)
        .all()
    )
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


@router.get("/me/history", response_model=list[SeasonHistoryOut])
def get_my_season_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team yet")
    return (
        db.query(SeasonHistory)
        .filter(SeasonHistory.team_id == team.id)
        .order_by(SeasonHistory.season.desc())
        .all()
    )


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
    if payload.league_key not in LEAGUES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown league")

    league = get_or_create_league(db, payload.league_key)
    code = payload.nfl_team_code.upper()
    team_name = LEAGUES[payload.league_key]["team_names_by_code"].get(code)
    if team_name is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown team")

    try:
        team = claim_team_core(db, current_user, league, code, team_name)
        db.commit()
    except TeamClaimError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This team has already been claimed")

    db.refresh(team)
    return team


@router.post("/release", status_code=status.HTTP_204_NO_CONTENT)
def release_team(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Hands the player's current team to an AI bot so they can pick a
    different one -- an AI immediately takes over so the league stays full."""
    try:
        release_team_core(db, current_user)
        db.commit()
    except TeamClaimError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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
