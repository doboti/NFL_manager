from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Position


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int | None
    first_name: str
    last_name: str
    position: Position
    age: int
    overall: int
    xp: int
    xp_to_next_level: int
    market_price: int | None
    photo_url: str | None
    nfl_team: str | None
    listed_for_transfer: bool
    asking_price: int | None
    is_starter: bool
    injured_until: datetime | None
