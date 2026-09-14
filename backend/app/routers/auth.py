from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, verify_password
from app.models.auth import LoginRequest, Token, User, UserOut
from app.store import store

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
async def login_json(payload: LoginRequest, response: Response):
    """Log in with username and password, returning a JWT token and setting session_id cookie."""
    user = store.users.get(payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})

    # Set secure HttpOnly session cookie
    response.set_cookie(
        key="session_id",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production
    )

    return Token(
        access_token=access_token, token_type="bearer", role=user.role, username=user.username
    )


@router.post("/token", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible form login endpoint for Swagger UI."""
    user = store.users.get(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return Token(
        access_token=access_token, token_type="bearer", role=user.role, username=user.username
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    """Retrieve details of the currently authenticated user."""
    return UserOut(username=user.username, role=user.role, is_active=user.is_active)
