from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    SCOREKEEPER = "scorekeeper"
    VIEWER = "viewer"


class User(BaseModel):
    username: str
    role: UserRole
    hashed_password: str
    is_active: bool = True


class UserOut(BaseModel):
    username: str
    role: UserRole
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
