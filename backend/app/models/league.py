from pydantic import BaseModel, Field


class League(BaseModel):
    id: str = Field(..., examples=["league-metro-2026"])
    name: str = Field(..., examples=["Metropolitan Amateur Premier League"])
    season: str = Field(..., examples=["2026 / 2027"])
    sportType: str = Field(default="Soccer", examples=["Soccer"])
    pointsWin: int = Field(default=3, ge=0, examples=[3])
    pointsDraw: int = Field(default=1, ge=0, examples=[1])
    pointsLoss: int = Field(default=0, ge=0, examples=[0])
    createdAt: str
    updatedAt: str


class CreateLeagueDto(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=80, examples=["Metropolitan Amateur Premier League"]
    )
    season: str = Field(..., min_length=1, max_length=30, examples=["2026 / 2027"])
    sportType: str | None = Field(default="Soccer", max_length=40, examples=["Soccer"])
    pointsWin: int | None = Field(default=3, ge=0, examples=[3])
    pointsDraw: int | None = Field(default=1, ge=0, examples=[1])
    pointsLoss: int | None = Field(default=0, ge=0, examples=[0])
