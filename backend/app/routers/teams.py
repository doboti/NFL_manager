from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.achievements import compute_achievements
from app.core.database import get_db
from app.core.deps import get_active_team, get_current_user
from app.core.game_data import LEAGUES, team_logo_url
from app.core.team_setup import TeamClaimError, avg_overall_by_team, claim_team as claim_team_core, release_team as release_team_core
from app.models.league import League
from app.models.season_history import SeasonHistory
from app.models.team import Team
from app.models.user import User
from app.schemas.team import (
    AchievementOut,
    ClaimTeamRequest,
    MyTeamOut,
    NFLTeamOption,
    SetTacticRequest,
    TeamOut,
    TeamRosterOut,
    TeamSummary,
)

router = APIRouter(prefix="/teams", tags=["teams"])


def _resolve_league(db: Session, league_key: str) -> League:
    league = db.query(League).filter(League.key == league_key).first()
    if league is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown league")
    return league


@router.get("/available", response_model=list[NFLTeamOption])
def list_available_teams(league_key: str, db: Session = Depends(get_db)):
    league = _resolve_league(db, league_key)

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
            logo_url=team_logo_url(league.sport, t["code"]),
        )
        for t in LEAGUES[league.sport]["teams"]
    ]


@router.get("/", response_model=list[TeamSummary])
def list_teams(current_user: User = Depends(get_current_user), team: Team = Depends(get_active_team), db: Session = Depends(get_db)):
    teams = (
        db.query(Team)
        .filter(Team.league_id == team.league_id, Team.owner_id != current_user.id)
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
def get_my_team(team: Team = Depends(get_active_team)):
    return team


@router.get("/mine", response_model=list[MyTeamOut])
def list_my_teams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Every team the user currently owns, across any league instance --
    powers the Profile page's per-slot display."""
    teams = (
        db.query(Team)
        .options(joinedload(Team.league))
        .filter(Team.owner_id == current_user.id)
        .all()
    )
    return [
        MyTeamOut(
            id=t.id,
            name=t.name,
            league_id=t.league_id,
            league_key=t.league.key,
            league_name=t.league.name,
            is_active=t.id == current_user.active_team_id,
        )
        for t in teams
    ]


@router.get("/me/achievements", response_model=list[AchievementOut])
def get_my_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(SeasonHistory).filter(SeasonHistory.owner_id == current_user.id).all()
    return compute_achievements(history)


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
    league = _resolve_league(db, payload.league_key)
    code = payload.nfl_team_code.upper()
    team_name = LEAGUES[league.sport]["team_names_by_code"].get(code)
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


@router.post("/{team_id}/release", status_code=status.HTTP_204_NO_CONTENT)
def release_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hands the given team to an AI bot so the player can pick a
    different one -- an AI immediately takes over so the league stays full."""
    try:
        release_team_core(db, current_user, team_id)
        db.commit()
    except TeamClaimError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{team_id}/activate", response_model=TeamOut)
def activate_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Switches which of the user's owned teams every single-team-scoped
    endpoint resolves as "my team" (core/deps.py: get_active_team)."""
    team = (
        db.query(Team)
        .options(joinedload(Team.players))
        .filter(Team.id == team_id, Team.owner_id == current_user.id)
        .first()
    )
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have this team")

    current_user.active_team_id = team.id
    db.commit()
    db.refresh(team)
    return team


@router.put("/tactic", response_model=TeamOut)
def set_tactic(
    payload: SetTacticRequest,
    team: Team = Depends(get_active_team),
    db: Session = Depends(get_db),
):
    team.tactic = payload.tactic
    db.commit()
    db.refresh(team)
    return team
