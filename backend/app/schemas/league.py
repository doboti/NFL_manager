from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamStanding(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nfl_team_code: str | None
    is_bot: bool
    wins: int
    losses: int
    ties: int
    avg_overall: float | None = None


class DivisionStandings(BaseModel):
    conference: str
    division: str
    teams: list[TeamStanding]


class SeasonStatus(BaseModel):
    season: int
    phase: str
    season_day: int
    regular_season_days: int
    current_playoff_round: str | None


class ScheduledMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    home_team_logo_url: str | None
    away_team_logo_url: str | None
    scheduled_at: datetime
    is_playoff: bool
    playoff_round: str | None


class LeagueOption(BaseModel):
    key: str
    name: str


class PlayoffMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playoff_round: str
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    home_score: int | None
    away_score: int | None
    played: bool
    scheduled_at: datetime
