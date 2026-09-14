from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class MatchResultChar(str, Enum):
    W = "W"
    D = "D"
    L = "L"

class TeamStanding(BaseModel):
    rank: int = Field(..., ge=1, examples=[1])
    teamId: str = Field(..., examples=["team-riverside"])
    teamName: str = Field(..., examples=["Riverside FC"])
    shortName: str = Field(..., examples=["RFC"])
    logoColor: str = Field(..., examples=["#10b981"])
    played: int = Field(default=0, ge=0, examples=[3])
    won: int = Field(default=0, ge=0, examples=[2])
    drawn: int = Field(default=0, ge=0, examples=[1])
    lost: int = Field(default=0, ge=0, examples=[0])
    goalsFor: int = Field(default=0, ge=0, examples=[9])
    goalsAgainst: int = Field(default=0, ge=0, examples=[3])
    goalDifference: int = Field(default=0, examples=[6])
    points: int = Field(default=0, ge=0, examples=[7])
    form: List[MatchResultChar] = Field(default_factory=list, description="Outcomes of last 5 completed matches, newest first")

class StandingsResponse(BaseModel):
    leagueId: str = Field(..., examples=["league-metro-2026"])
    leagueName: str = Field(..., examples=["Metropolitan Amateur Premier League"])
    calculatedAt: str
    isLiveProvisional: bool = Field(default=False)
    standings: List[TeamStanding]
