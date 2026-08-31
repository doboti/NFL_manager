from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Position, TradeStatus
from app.schemas.player import PlayerOut


class CreateTradeOfferRequest(BaseModel):
    to_team_id: int
    target_player_id: int
    offered_player_id: int | None = None
    cash_offer: int = Field(default=0, ge=0)


class TradeOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_team_id: int
    to_team_id: int
    from_team_name: str
    to_team_name: str
    to_team_is_bot: bool
    target_player: PlayerOut
    offered_player: PlayerOut | None
    cash_offer: int
    status: TradeStatus
    created_at: datetime
    resolved_at: datetime | None
    respond_at: datetime | None
    expires_at: datetime | None


class PlayerSearchResult(BaseModel):
    id: int
    first_name: str
    last_name: str
    position: Position
    overall: int
    potential: int | None
    team_id: int | None
    team_name: str | None
