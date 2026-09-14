from typing import Any, List, Optional
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    statusCode: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Human-readable error description")
    error: Optional[str] = Field(None, description="Error category name")
    details: Optional[List[str]] = Field(default=None, description="Detailed validation notes")

class ServiceEvent(BaseModel):
    type: str = Field(..., description="Type of event broadcasted")
    payload: Any = Field(..., description="Associated event data")
