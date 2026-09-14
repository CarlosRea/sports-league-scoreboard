from fastapi import APIRouter, HTTPException, status, Query
from app.models.standings import StandingsResponse
from app.store.memory_store import store

router = APIRouter(tags=["Standings"])

@router.get("/leagues/{leagueId}/standings", response_model=StandingsResponse)
async def get_standings(
    leagueId: str,
    live: bool = Query(False, description="Whether to include provisional live scores from in-progress matches")
):
    """Retrieve calculated standings table based on 3-1-0 points rules and tie-breakers."""
    try:
        return store.get_standings(leagueId, live_provisional=live)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"League '{leagueId}' not found."
        )
