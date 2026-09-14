from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.models.common import ErrorResponse
from app.routers import (
    auth_router,
    leagues_router,
    teams_router,
    matches_router,
    scorekeeper_router,
    standings_router,
    stream_router,
    dev_router,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Backend for Sports League Scoreboard application.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration for pitchside scorekeeper frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers for unified error shape
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            statusCode=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation error in request payload.",
            error="Unprocessable Entity",
            details=details
        ).model_dump()
    )

# Mount Routers under API Prefix
api_prefix = settings.API_PREFIX
app.include_router(auth_router, prefix=api_prefix)
app.include_router(leagues_router, prefix=api_prefix)
app.include_router(teams_router, prefix=api_prefix)
app.include_router(matches_router, prefix=api_prefix)
app.include_router(scorekeeper_router, prefix=api_prefix)
app.include_router(standings_router, prefix=api_prefix)
app.include_router(stream_router, prefix=api_prefix)
app.include_router(dev_router, prefix=api_prefix)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
