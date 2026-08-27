from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Tactic
from app.schemas.player import PlayerOut


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nfl_team_code: str | None
    franchise_capital: int
    stadium_level: int
    tactic: Tactic
    wins: int
    losses: int
    ties: int
    created_at: datetime
    next_match_at: datetime
    daily_salary_cost: int
    primary_color: str
    secondary_color: str
    logo_url: str | None
    players: list[PlayerOut] = []


class SetTacticRequest(BaseModel):
    tactic: Tactic


class NFLTeamOption(BaseModel):
    code: str
    name: str
    taken: bool
    controlled_by_bot: bool = False
    logo_url: str | None = None


class ClaimTeamRequest(BaseModel):
    league_key: str
    nfl_team_code: str


class TeamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nfl_team_code: str | None
    is_bot: bool
    avg_overall: float | None = None


class MyTeamOut(BaseModel):
    id: int
    name: str
    league_id: int
    league_key: str
    league_name: str
    is_active: bool


class TeamRosterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nfl_team_code: str | None
    players: list[PlayerOut] = []


class AchievementOut(BaseModel):
    code: str
    name: str
    description: str
    earned: bool
    progress_text: str | None = None
