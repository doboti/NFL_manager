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
    players: list[PlayerOut] = []


class SetTacticRequest(BaseModel):
    tactic: Tactic


class NFLTeamOption(BaseModel):
    code: str
    name: str
    taken: bool
    controlled_by_bot: bool = False


class ClaimTeamRequest(BaseModel):
    nfl_team_code: str


class TeamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nfl_team_code: str | None
    is_bot: bool
    avg_overall: float | None = None


class TeamRosterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nfl_team_code: str | None
    players: list[PlayerOut] = []
