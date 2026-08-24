from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SponsorType


class SponsorTemplate(BaseModel):
    key: str
    name: str
    sponsor_type: SponsorType
    daily_amount: int
    win_bonus: int
    duration_days: int


class SponsorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_key: str
    name: str
    sponsor_type: SponsorType
    daily_amount: int
    win_bonus: int
    signed_at: datetime
    expires_at: datetime


class SignSponsorRequest(BaseModel):
    template_key: str
