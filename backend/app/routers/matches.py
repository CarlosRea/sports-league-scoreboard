from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends
from app.models.match import Match, CreateMatchDto
from app.models.auth import User
from app.auth.dependencies import require_admin
from app.store.memory_store import store

router = APIRouter(tags=["Matches"])

@router.get("/leagues/{leagueId}/matches", response_model=List[Match])
async def get_matches(
    leagueId: str,
    status: Optional[str] = Query(None, description="Filter by match status (e.g. IN_PROGRESS, SCHEDULED, FINISHED)"),
    matchday: Optional[int] = Query(None, ge=1, description="Filter by matchday / round number")
):
    """List matches in a league with optional status and matchday filters."""
    if not store.get_league(leagueId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League '{leagueId}' not found."
        )
    return store.get_matches(leagueId, status=status, matchday=matchday)

@router.post("/leagues/{leagueId}/matches", response_model=Match, status_code=status.HTTP_201_CREATED)
async def create_match(
    leagueId: str,
    dto: CreateMatchDto,
    admin_user: User = Depends(require_admin)
):
    """Schedule a new match fixture. Requires Administrator role."""
    if not store.get_league(leagueId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League '{leagueId}' not found."
        )

    try:
        return store.create_match(leagueId, dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/matches/{matchId}", response_model=Match)
async def get_match(matchId: str):
    """Retrieve detailed information and event history for a specific match."""
    match = store.get_match(matchId)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match '{matchId}' not found."
        )
    return match
