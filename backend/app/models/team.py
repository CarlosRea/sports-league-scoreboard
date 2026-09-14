from pydantic import BaseModel, Field


class Team(BaseModel):
    id: str = Field(..., examples=["team-riverside"])
    leagueId: str = Field(..., examples=["league-metro-2026"])
    name: str = Field(..., examples=["Riverside FC"])
    shortName: str = Field(..., max_length=4, examples=["RFC"])
    logoColor: str = Field(default="#10b981", examples=["#10b981"])
    logoUrl: str | None = Field(default=None, examples=[None])
    createdAt: str


class CreateTeamDto(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, examples=["Phoenix Rising FC"])
    shortName: str = Field(..., min_length=2, max_length=4, examples=["PHX"])
    logoColor: str | None = Field(
        default="#10b981", pattern=r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", examples=["#10b981"]
    )
    logoUrl: str | None = Field(default=None)
