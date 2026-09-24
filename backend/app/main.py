import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.common import ErrorResponse
from app.routers import (
    auth_router,
    dev_router,
    leagues_router,
    matches_router,
    scorekeeper_router,
    standings_router,
    stream_router,
    teams_router,
)
from app.store.sql_store import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schema and ensure initial seed data is present
    store.init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Backend for Sports League Scoreboard application.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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
            details=details,
        ).model_dump(),
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


# Serve Frontend Static Assets and SPA fallback if available
static_dir = settings.STATIC_DIR
if static_dir and os.path.isdir(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_frontend(full_path: str):
    # Exclude API endpoints, docs, and health checks
    if (
        full_path.startswith("api")
        or full_path.startswith("docs")
        or full_path.startswith("redoc")
        or full_path == "openapi.json"
        or full_path == "health"
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Not Found"},
        )

    current_static = settings.STATIC_DIR
    if not current_static or not os.path.isdir(current_static):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Frontend static assets not configured or not found"},
        )

    # Secure path traversal verification
    resolved_static = os.path.abspath(current_static)
    requested_file = os.path.abspath(os.path.join(current_static, full_path))
    if os.path.isfile(requested_file) and (
        requested_file == resolved_static or requested_file.startswith(resolved_static + os.sep)
    ):
        return FileResponse(requested_file)

    # Fallback to SPA index.html for client-side routing
    index_file = os.path.join(current_static, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not Found"},
    )
