from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_admin
from app.models.auth import User
from app.models.league import CreateLeagueDto, League
from app.store import store
from app.telemetry import record_match_created

router = APIRouter(tags=["Leagues"])


@router.get("/leagues", response_model=list[League])
async def get_leagues():
    """List all available leagues and tournaments."""
    return store.get_leagues()


@router.post("/leagues", response_model=League, status_code=status.HTTP_201_CREATED)
async def create_league(dto: CreateLeagueDto, admin_user: User = Depends(require_admin)):
    """Create and configure a new league. Requires Administrator role."""
    new_league = store.create_league(dto)
    record_match_created(entity_type="league")
    return new_league


@router.get("/leagues/{leagueId}", response_model=League)
async def get_league(leagueId: str):
    """Retrieve details for a specific league."""
    league = store.get_league(leagueId)
    if not league:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"League '{leagueId}' not found."
        )
    return league
