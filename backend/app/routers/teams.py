from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_admin
from app.models.auth import User
from app.models.team import CreateTeamDto, Team
from app.store import store

router = APIRouter(tags=["Teams"])


@router.get("/leagues/{leagueId}/teams", response_model=list[Team])
async def get_teams(leagueId: str):
    """List all clubs and teams registered in the specified league."""
    if not store.get_league(leagueId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"League '{leagueId}' not found."
        )
    return store.get_teams(leagueId)


@router.post("/leagues/{leagueId}/teams", response_model=Team, status_code=status.HTTP_201_CREATED)
async def create_team(leagueId: str, dto: CreateTeamDto, admin_user: User = Depends(require_admin)):
    """Register a new team in the league. Requires Administrator role."""
    if not store.get_league(leagueId):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"League '{leagueId}' not found."
        )

    try:
        return store.create_team(leagueId, dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
