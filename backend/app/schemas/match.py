from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.enums import Tactic


class PlayerRef(BaseModel):
    first_name: str
    last_name: str
    photo_url: str | None


class PlayEventOut(BaseModel):
    quarter: int
    offense: Literal["home", "away"]
    play_type: Literal["pass", "run", "field_goal", "punt", "safety"]
    success: bool
    start_yard: int
    end_yard: int
    yards: int
    result: str
    points: int
    primary_player: PlayerRef | None
    secondary_player: PlayerRef | None
    text: str
    # Decorative game-context fields for the animated replay (down/distance,
    # game clock, timeouts) -- generated alongside the drive purely for
    # visual flavor, never fed back into how the score is decided. Optional
    # since matches simulated before this was added have play_events blobs
    # in the database that predate these keys.
    down: int | None = None
    distance: int | None = None
    clock: str | None = None
    home_timeouts: int | None = None
    away_timeouts: int | None = None


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    home_team_logo_url: str | None
    away_team_logo_url: str | None
    home_team_primary_color: str
    away_team_primary_color: str
    home_score: int | None
    away_score: int | None
    home_tactic: Tactic
    away_tactic: Tactic
    play_log: list[str] | None
    play_events: list[PlayEventOut] | None
    played: bool
    played_at: datetime | None
    is_playoff: bool
    playoff_round: str | None


class PracticeMatchResult(BaseModel):
    opponent_name: str
    home_team_logo_url: str | None = None
    home_team_primary_color: str | None = None
    home_score: int
    away_score: int
    play_log: list[str]
    play_events: list[PlayEventOut]


class DailyCycleSummary(BaseModel):
    matches: list[dict]
    economy: list[dict]
    new_market_players: int
    bot_trades: dict
    seasons: list[dict]
    playoff_events: dict
    bot_progression_count: int
