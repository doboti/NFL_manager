from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.clock import create_league_instance
from app.core.database import get_db
from app.core.deps import get_current_user, resolve_active_team
from app.core.game_data import LEAGUES, REGULAR_SEASON_DAYS
from app.core.progression import compute_level, unlocked_slots
from app.core.team_setup import avg_overall_by_team
from app.models.league import League
from app.models.match import Match
from app.models.season_history import SeasonHistory
from app.models.team import Team
from app.models.user import User
from app.schemas.league import (
    CreateLeagueInstanceRequest,
    DivisionStandings,
    LeagueInstanceOut,
    LeagueOption,
    PlayoffMatchOut,
    ScheduledMatch,
    SeasonStatus,
    TeamStanding,
)

router = APIRouter(prefix="/league", tags=["league"])


def _current_users_league(current_user: User, db: Session) -> League:
    team = resolve_active_team(db, current_user)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team yet")
    return db.query(League).filter(League.id == team.league_id).first()


@router.get("/season", response_model=SeasonStatus)
def get_season_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = _current_users_league(current_user, db)
    return SeasonStatus(
        season=league.season,
        phase=league.phase.value,
        season_day=league.season_day,
        regular_season_days=REGULAR_SEASON_DAYS,
        current_playoff_round=league.current_playoff_round,
    )


@router.get("/standings", response_model=list[DivisionStandings])
def get_standings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = _current_users_league(current_user, db)
    divisions = LEAGUES[league.sport]["divisions"]

    teams_by_code = {
        t.nfl_team_code: t
        for t in db.query(Team).filter(Team.league_id == league.id, Team.nfl_team_code.isnot(None))
    }
    avg_overall = avg_overall_by_team(db)

    standings = []
    for division, codes in divisions.items():
        conference = division.split(" ")[0]
        division_teams = [
            TeamStanding(
                id=team.id,
                name=team.name,
                nfl_team_code=team.nfl_team_code,
                is_bot=team.is_bot,
                wins=team.wins,
                losses=team.losses,
                ties=team.ties,
                avg_overall=avg_overall.get(team.id),
            )
            for code in codes
            if (team := teams_by_code.get(code)) is not None
        ]
        division_teams.sort(key=lambda t: (-t.wins, t.losses))
        standings.append(DivisionStandings(conference=conference, division=division, teams=division_teams))

    return standings


@router.get("/schedule", response_model=list[ScheduledMatch])
def get_schedule(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    league = _current_users_league(current_user, db)
    return (
        db.query(Match)
        .join(Team, Match.home_team_id == Team.id)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .filter(Match.played.is_(False), Team.league_id == league.id)
        .order_by(Match.scheduled_at.asc())
        .limit(limit)
        .all()
    )


@router.get("/playoffs", response_model=list[PlayoffMatchOut])
def get_playoff_bracket(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    league = _current_users_league(current_user, db)
    return (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .filter(Match.league_id == league.id, Match.season == league.season, Match.is_playoff.is_(True))
        .order_by(Match.scheduled_at.asc())
        .all()
    )


@router.get("/available", response_model=list[LeagueOption])
def list_available_leagues():
    return [LeagueOption(key=key, name=data["name"]) for key, data in LEAGUES.items()]


def _is_league_full(db: Session, league: League) -> bool:
    total_codes = len(LEAGUES[league.sport]["teams"])
    human_held = (
        db.query(Team)
        .filter(Team.league_id == league.id, Team.is_bot.is_(False))
        .count()
    )
    return human_held >= total_codes


@router.get("/instances", response_model=list[LeagueInstanceOut])
def list_league_instances(sport: str, db: Session = Depends(get_db)):
    """Every existing instance of a sport (there's normally just one, but a
    manager with a free league slot can spin up another once all existing
    ones are full -- see POST below) -- powers the league-instance picker
    in team selection."""
    if sport not in LEAGUES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown sport")

    instances = db.query(League).filter(League.sport == sport).order_by(League.id).all()
    return [
        LeagueInstanceOut(key=l.key, name=l.name, sport=l.sport, is_full=_is_league_full(db, l))
        for l in instances
    ]


@router.post("/instances", response_model=LeagueInstanceOut, status_code=status.HTTP_201_CREATED)
def create_new_league_instance(
    payload: CreateLeagueInstanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Self-service: any player can start a new instance of a sport, but
    only once every existing instance of it is full and they still have a
    free league slot -- otherwise there's nothing stopping endless empty
    instances from piling up."""
    sport = payload.sport
    if sport not in LEAGUES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown sport")

    existing = db.query(League).filter(League.sport == sport).all()
    if existing and not all(_is_league_full(db, l) for l in existing):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An existing league instance of this sport still has room",
        )

    owned = db.query(Team).filter(Team.owner_id == current_user.id).count()
    completed_seasons = db.query(SeasonHistory).filter(SeasonHistory.owner_id == current_user.id).count()
    if owned >= unlocked_slots(compute_level(completed_seasons)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No free league slot at your current level")

    league = create_league_instance(db, sport)
    db.commit()
    return LeagueInstanceOut(key=league.key, name=league.name, sport=league.sport, is_full=False)
