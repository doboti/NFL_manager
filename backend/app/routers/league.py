from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.clock import get_or_create_default_league
from app.core.database import get_db
from app.core.game_data import NFL_DIVISIONS, REGULAR_SEASON_DAYS
from app.core.team_setup import avg_overall_by_team
from app.models.match import Match
from app.models.team import Team
from app.schemas.league import DivisionStandings, ScheduledMatch, SeasonStatus, TeamStanding

router = APIRouter(prefix="/league", tags=["league"])


@router.get("/season", response_model=SeasonStatus)
def get_season_status(db: Session = Depends(get_db)):
    league = get_or_create_default_league(db)
    db.commit()
    return SeasonStatus(
        season=league.season,
        phase=league.phase.value,
        season_day=league.season_day,
        regular_season_days=REGULAR_SEASON_DAYS,
        current_playoff_round=league.current_playoff_round,
    )


@router.get("/standings", response_model=list[DivisionStandings])
def get_standings(db: Session = Depends(get_db)):
    teams_by_code = {t.nfl_team_code: t for t in db.query(Team).filter(Team.nfl_team_code.isnot(None))}
    avg_overall = avg_overall_by_team(db)

    standings = []
    for division, codes in NFL_DIVISIONS.items():
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
def get_schedule(limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    return (
        db.query(Match)
        .options(joinedload(Match.home_team), joinedload(Match.away_team))
        .filter(Match.played.is_(False))
        .order_by(Match.scheduled_at.asc())
        .limit(limit)
        .all()
    )
