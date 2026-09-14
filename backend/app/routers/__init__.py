from .auth import router as auth_router
from .dev import router as dev_router
from .leagues import router as leagues_router
from .matches import router as matches_router
from .scorekeeper import router as scorekeeper_router
from .standings import router as standings_router
from .stream import router as stream_router
from .teams import router as teams_router

__all__ = [
    "auth_router",
    "dev_router",
    "leagues_router",
    "matches_router",
    "scorekeeper_router",
    "standings_router",
    "stream_router",
    "teams_router",
]
