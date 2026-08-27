from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, resolve_active_team
from app.core.market import MarketError, buy_player
from app.models.enums import Position
from app.models.player import Player
from app.models.user import User
from app.schemas.player import PlayerOut
from app.schemas.team import TeamOut

router = APIRouter(prefix="/market", tags=["market"])

# A pure OVR-descending default made every visit to the market look like a
# wall of elites -- the rarest tier by construction, but also the only
# thing shown first (#20 follow-up). Grouping by position first means the
# opening view is a realistic cross-section of the roster instead of just
# the single overall-richest position group (DEF, being ~10 real positions
# merged into one, dominated a pure OVR sort).
_POSITION_ORDER = case(
    {pos: i for i, pos in enumerate([Position.QB, Position.RB, Position.WR, Position.TE, Position.K, Position.DEF])},
    value=Player.position,
)


@router.get("/", response_model=list[PlayerOut])
def list_market(
    response: Response,
    position: Position | None = Query(None),
    search: str | None = Query(None, max_length=50),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = resolve_active_team(db, current_user)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    query = db.query(Player).filter(Player.league_id == team.league_id, Player.team_id.is_(None))

    if position is not None:
        query = query.filter(Player.position == position)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Player.first_name.ilike(pattern)) | (Player.last_name.ilike(pattern))
        )

    response.headers["X-Total-Count"] = str(query.order_by(None).count())

    return (
        query.order_by(_POSITION_ORDER, Player.overall.desc(), Player.market_price.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post("/{player_id}/buy", response_model=TeamOut)
def buy(
    player_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = resolve_active_team(db, current_user)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    try:
        buy_player(db, team, player_id)
    except MarketError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.refresh(team)
    return team
