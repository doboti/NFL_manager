from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.daily_cycle import run_daily_cycle
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.player_generator import generate_starting_roster, random_name
from app.core.simulation import simulate_match
from app.models.match import Match
from app.models.team import Team
from app.models.user import User
from app.schemas.league import ScheduledMatch
from app.schemas.match import DailyCycleSummary, MatchOut, PracticeMatchResult

router = APIRouter(prefix="/matches", tags=["matches"])


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


@router.get("/", response_model=list[MatchOut])
def list_matches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    return (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .filter(
            or_(Match.home_team_id == team.id, Match.away_team_id == team.id),
            Match.played.is_(True),
        )
        .order_by(Match.played_at.desc())
        .limit(20)
        .all()
    )


@router.get("/upcoming", response_model=ScheduledMatch | None)
def get_upcoming_match(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = _get_team(current_user, db)
    return (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .filter(
            or_(Match.home_team_id == team.id, Match.away_team_id == team.id),
            Match.played.is_(False),
        )
        .order_by(Match.scheduled_at.asc())
        .first()
    )


@router.post("/practice", response_model=PracticeMatchResult)
def practice_match(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ephemeral friendly match against a generated AI opponent. Not saved, no economy effect."""
    team = _get_team(current_user, db)
    if not team.players:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No players in roster")

    opponent_players = generate_starting_roster()
    first, last = random_name()
    opponent_name = f"{first} {last} All-Stars"

    result = simulate_match(
        team.name, opponent_name, team.players, opponent_players, team.tactic, team.tactic
    )

    return PracticeMatchResult(
        opponent_name=opponent_name,
        home_score=result["home_score"],
        away_score=result["away_score"],
        play_log=result["play_log"],
    )


@router.post("/run-daily-cycle", response_model=DailyCycleSummary)
def trigger_daily_cycle(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dev/testing endpoint: manually runs the same cycle the 02:00 scheduler runs for all teams."""
    return run_daily_cycle(db)
