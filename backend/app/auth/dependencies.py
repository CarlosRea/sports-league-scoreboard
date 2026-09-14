from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decode_access_token
from app.models.auth import User, UserRole
from app.store import store

# Optional HTTPBearer so endpoints that allow both Cookie and Header don't fail immediately
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer)
) -> User:
    """Extract and validate user from Bearer header or session_id cookie."""
    token: str | None = None

    if credentials:
        token = credentials.credentials
    elif "session_id" in request.cookies:
        token = request.cookies.get("session_id")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = store.users.get(username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Ensure current user has the Admin role."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permissions are required for this action.",
        )
    return user


async def require_scorekeeper_or_admin(user: User = Depends(get_current_user)) -> User:
    """Ensure current user has either Scorekeeper or Admin role."""
    if user.role not in (UserRole.ADMIN, UserRole.SCOREKEEPER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scorekeeper or Administrator permissions are required for this action.",
        )
    return user
