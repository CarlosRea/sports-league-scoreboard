from enum import Enum

from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class MatchPeriod(str, Enum):
    NOT_STARTED = "Not Started"
    FIRST_HALF = "1st Half"
    HALF_TIME = "Half Time"
    SECOND_HALF = "2nd Half"
    FULL_TIME = "Full Time"


class MatchEventType(str, Enum):
    GOAL_HOME = "GOAL_HOME"
    GOAL_AWAY = "GOAL_AWAY"
    SCORE_ADJUST = "SCORE_ADJUST"
    PERIOD_CHANGE = "PERIOD_CHANGE"
    MATCH_STARTED = "MATCH_STARTED"
    MATCH_FINISHED = "MATCH_FINISHED"


class MatchEvent(BaseModel):
    id: str = Field(..., examples=["ev-1"])
    matchId: str = Field(..., examples=["match-301"])
    type: MatchEventType
    minute: int = Field(default=0, ge=0, examples=[18])
    homeScoreAfter: int = Field(default=0, ge=0, examples=[1])
    awayScoreAfter: int = Field(default=0, ge=0, examples=[0])
    note: str | None = Field(default=None, examples=["Goal scored by Riverside FC"])
    recordedAt: str


class Match(BaseModel):
    id: str = Field(..., examples=["match-301"])
    leagueId: str = Field(..., examples=["league-metro-2026"])
    homeTeamId: str = Field(..., examples=["team-riverside"])
    awayTeamId: str = Field(..., examples=["team-redstar"])
    matchday: int = Field(..., ge=1, examples=[3])
    scheduledAt: str
    status: MatchStatus = Field(default=MatchStatus.SCHEDULED)
    homeScore: int = Field(default=0, ge=0, examples=[2])
    awayScore: int = Field(default=0, ge=0, examples=[1])
    currentPeriod: MatchPeriod = Field(default=MatchPeriod.NOT_STARTED)
    elapsedMinutes: int | None = Field(default=None, ge=0, examples=[68])
    startedAt: str | None = None
    finishedAt: str | None = None
    createdAt: str
    updatedAt: str
    events: list[MatchEvent] = Field(default_factory=list)


class CreateMatchDto(BaseModel):
    leagueId: str | None = None
    homeTeamId: str = Field(..., examples=["team-riverside"])
    awayTeamId: str = Field(..., examples=["team-apex"])
    matchday: int = Field(default=1, ge=1, examples=[3])
    scheduledAt: str = Field(..., examples=["2026-09-18T18:30:00.000Z"])


class UpdateScoreDto(BaseModel):
    homeScore: int = Field(..., ge=0, examples=[2])
    awayScore: int = Field(..., ge=0, examples=[1])
    period: MatchPeriod | None = None
    minute: int | None = Field(default=None, ge=0, le=130, examples=[72])
    note: str | None = Field(default=None, max_length=200, examples=["Goal scored by Riverside FC"])
