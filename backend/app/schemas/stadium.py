from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StadiumUpgradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_level: int
    started_at: datetime
    ends_at: datetime
    collected: bool
