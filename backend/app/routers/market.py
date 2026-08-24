from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.market import MarketError, buy_player
from app.models.enums import Position
from app.models.player import Player
from app.models.team import Team
from app.models.user import User
from app.schemas.player import PlayerOut
from app.schemas.team import TeamOut

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/", response_model=list[PlayerOut])
def list_market(
    response: Response,
    position: Position | None = Query(None),
    search: str | None = Query(None, max_length=50),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Player).filter(Player.team_id.is_(None))

    if position is not None:
        query = query.filter(Player.position == position)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Player.first_name.ilike(pattern)) | (Player.last_name.ilike(pattern))
        )

    response.headers["X-Total-Count"] = str(query.order_by(None).count())

    return (
        query.order_by(Player.overall.desc(), Player.market_price.desc())
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
    team = (
        db.query(Team)
        .options(joinedload(Team.players))
        .filter(Team.owner_id == current_user.id)
        .first()
    )
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    try:
        buy_player(db, team, player_id)
    except MarketError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.refresh(team)
    return team
