from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.team import Team
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_error

    user = db.query(User).filter(User.id == int(subject)).first()
    if user is None:
        raise credentials_error

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def resolve_active_team(db: Session, user: User) -> Team | None:
    """A user can now own up to 3 teams at once (one per league instance) --
    this resolves which one every single-team-scoped endpoint means by "my
    team": the one they last activated, falling back to any owned team if
    that pointer is unset or stale (e.g. just released). Plain function (not
    a FastAPI dependency) so each router's existing local team-lookup
    helper can delegate to it directly and keep its own error message."""
    team = None
    if user.active_team_id is not None:
        team = db.query(Team).filter(Team.id == user.active_team_id, Team.owner_id == user.id).first()
    if team is None:
        team = db.query(Team).filter(Team.owner_id == user.id).first()
    return team


def get_active_team(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Team:
    team = resolve_active_team(db, current_user)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No team yet")
    return team
