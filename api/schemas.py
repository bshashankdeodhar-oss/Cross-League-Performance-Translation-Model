"""Pydantic models — request/response contracts for the API."""

from pydantic import BaseModel, Field
from typing import Optional


class PredictRequest(BaseModel):
    player: str = Field(..., examples=["Florian Wirtz"])
    source_league: str = Field(..., examples=["Bundesliga"])
    target_league: str = Field(..., examples=["Premier League"])
    target_team: Optional[str] = Field(None, examples=["Manchester City"])


class TopFactor(BaseModel):
    feature: str
    value: float
    impact: float


class PredictResponse(BaseModel):
    player: str
    source_league: str
    target_league: str
    target_team: Optional[str] = None
    target_team_strength_ratio: Optional[float] = None
    source_lsc: float
    target_lsc: float
    projected_goals_p90: Optional[float]
    projected_assists_p90: Optional[float]
    projected_xg_p90: Optional[float]
    projected_xag_p90: Optional[float]
    projected_prog_passes_p90: Optional[float] = None
    projected_key_passes_p90: Optional[float] = None
    projected_prog_carries_p90: Optional[float] = None
    projected_tackles_won_p90: Optional[float] = None
    projected_interceptions_p90: Optional[float] = None
    projected_clearances_p90: Optional[float] = None
    ci_low_goals: Optional[float]
    ci_high_goals: Optional[float]
    minutes_expectation: Optional[float]
    adaptation_score_pct: float
    risk_score_pct: float
    top_5_factors: list
    tactical_fit: Optional[dict] = None


class TeamSummary(BaseModel):
    team: str
    league: str
    team_strength_ratio: Optional[float] = 1.0


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    username: str
    password: str


class PlayerSummary(BaseModel):
    player: str
    team: str
    league: str
    position: str
    age: float
