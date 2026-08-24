from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StartTrainingRequest(BaseModel):
    player_id: int


class TrainingSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    started_at: datetime
    ends_at: datetime
    xp_awarded: int
    completed: bool
    collected: bool
