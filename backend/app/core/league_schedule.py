import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.clock import now_utc
from app.core.game_data import MATCH_HOUR
from app.core.schedule import LEAGUE_TZ, next_match_time
from app.models.enums import SeasonPhase
from app.models.league import League
from app.models.match import Match
from app.models.team import Team


def _has_pending_match(db: Session, team_id: int) -> bool:
    return (
        db.query(Match)
        .filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.played.is_(False),
        )
        .first()
        is not None
    )


def _has_played_before(db: Session, team_id: int) -> bool:
    return (
        db.query(Match)
        .filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.played.is_(True),
        )
        .first()
        is not None
    )


def _next_eligible_date(db: Session, team: Team, today: date, now: datetime) -> date:
    if not _has_played_before(db, team.id):
        return next_match_time(team.created_at, now).date()
    return today + timedelta(days=1)


def ensure_fixtures_scheduled(db: Session, league: League) -> int:
    """Guarantees every team without a pending fixture gets its next match
    scheduled, paired up by the date each one becomes eligible to play.

    A no-op during the playoffs -- eliminated teams' seasons are over, and the
    bracket (app/core/season_manager.py) schedules the surviving teams itself."""
    if league.phase != SeasonPhase.REGULAR:
        return 0

    now = now_utc(db).astimezone(LEAGUE_TZ)
    today = now.date()

    teams = db.query(Team).all()
    unscheduled = [t for t in teams if not _has_pending_match(db, t.id)]

    by_date: dict[date, list[Team]] = {}
    for team in unscheduled:
        target_date = _next_eligible_date(db, team, today, now)
        by_date.setdefault(target_date, []).append(team)

    created = 0
    for target_date, group in by_date.items():
        random.shuffle(group)
        scheduled_at = datetime.combine(target_date, time(hour=MATCH_HOUR), tzinfo=LEAGUE_TZ)
        for home, away in zip(group[0::2], group[1::2]):
            db.add(
                Match(
                    league_id=league.id,
                    season=league.season,
                    home_team_id=home.id,
                    away_team_id=away.id,
                    played=False,
                    scheduled_at=scheduled_at,
                )
            )
            created += 1

    if created:
        db.flush()

    return created
