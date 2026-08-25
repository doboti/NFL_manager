from pydantic import BaseModel, EmailStr, Field

from app.schemas.team import AchievementOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: str
    display_name: str
    is_admin: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class SlotInfo(BaseModel):
    slot: int
    required_level: int


class ProfileOut(BaseModel):
    id: int
    email: str
    display_name: str
    level: int
    completed_seasons: int
    unlocked_slots: int
    total_slots: int
    next_slot: SlotInfo | None
    achievements: list[AchievementOut]
