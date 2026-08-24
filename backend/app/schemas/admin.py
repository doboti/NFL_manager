from datetime import datetime

from pydantic import BaseModel, Field


class TimeStatus(BaseModel):
    offset_seconds: int
    virtual_now: datetime


class AdvanceTimeRequest(BaseModel):
    hours: float = Field(gt=0, le=24 * 30)


class AdvanceTimeResponse(BaseModel):
    time: TimeStatus
    daily_cycle: dict | None


class AdminUserOut(BaseModel):
    id: int
    email: str
    display_name: str
    is_bot: bool
    is_admin: bool
    team_name: str | None
