from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    statusCode: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Human-readable error description")
    error: str | None = Field(None, description="Error category name")
    details: list[str] | None = Field(default=None, description="Detailed validation notes")


class ServiceEvent(BaseModel):
    type: str = Field(..., description="Type of event broadcasted")
    payload: Any = Field(..., description="Associated event data")
