from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Tactic


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    home_score: int | None
    away_score: int | None
    home_tactic: Tactic
    away_tactic: Tactic
    play_log: list[str] | None
    played: bool
    played_at: datetime | None
    is_playoff: bool
    playoff_round: str | None


class PracticeMatchResult(BaseModel):
    opponent_name: str
    home_score: int
    away_score: int
    play_log: list[str]


class DailyCycleSummary(BaseModel):
    matches: list[dict]
    economy: list[dict]
    new_market_players: int
    bot_trades: dict
    seasons: list[dict]
    playoff_events: dict
    bot_progression_count: int
