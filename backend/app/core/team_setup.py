from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.team import Team
from app.models.user import User


class TeamClaimError(Exception):
    pass


def avg_overall_by_team(db: Session) -> dict[int, float]:
    """One aggregate query -- avoids loading every team's full roster just to
    show a lightweight average rating in list/standings views."""
    rows = (
        db.query(Player.team_id, func.avg(Player.overall))
        .filter(Player.team_id.isnot(None))
        .group_by(Player.team_id)
        .all()
    )
    return {team_id: round(float(avg), 1) for team_id, avg in rows}


def get_team_by_code(db: Session, code: str) -> Team | None:
    return db.query(Team).filter(Team.nfl_team_code == code).first()


def is_team_code_taken_by_human(db: Session, code: str) -> bool:
    team = get_team_by_code(db, code)
    return team is not None and not team.is_bot


def assign_real_roster(db: Session, team: Team, code: str) -> int:
    """Hands the team every currently-unclaimed real player on that NFL roster."""
    players = db.query(Player).filter(Player.nfl_team == code, Player.team_id.is_(None)).all()
    for player in players:
        player.team_id = team.id
    return len(players)


def claim_team(db: Session, user: User, code: str, team_name: str) -> Team:
    """Creates a fresh franchise for `code`, or -- if an AI bot currently runs that
    team -- hands the human the reins of that same (already-populated) franchise."""
    if db.query(Team).filter(Team.owner_id == user.id).first() is not None:
        raise TeamClaimError("You already have a team")

    existing = get_team_by_code(db, code)

    if existing is not None and not existing.is_bot:
        raise TeamClaimError("This NFL team has already been claimed")

    if existing is not None and existing.is_bot:
        old_owner_id = existing.owner_id
        existing.owner_id = user.id
        existing.is_bot = False
        db.flush()
        db.query(User).filter(User.id == old_owner_id, User.is_bot.is_(True)).delete()
        return existing

    team = Team(owner_id=user.id, name=team_name, nfl_team_code=code)
    db.add(team)
    db.flush()
    assign_real_roster(db, team, code)
    return team
