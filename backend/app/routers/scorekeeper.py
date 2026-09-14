from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_scorekeeper_or_admin
from app.models.auth import User
from app.models.match import Match, UpdateScoreDto
from app.store import store

router = APIRouter(tags=["Scorekeeper"])


@router.post("/matches/{matchId}/start", response_model=Match)
async def start_match(matchId: str, user: User = Depends(require_scorekeeper_or_admin)):
    """Transition match status to IN_PROGRESS and start period. Requires Scorekeeper or Admin role."""
    try:
        return store.start_match(matchId)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Match '{matchId}' not found."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/matches/{matchId}/score", response_model=Match)
async def update_score(
    matchId: str, dto: UpdateScoreDto, user: User = Depends(require_scorekeeper_or_admin)
):
    """Update live score, current period, and log event. Requires Scorekeeper or Admin role."""
    try:
        return store.update_score(matchId, dto)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Match '{matchId}' not found."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/matches/{matchId}/finish", response_model=Match)
async def finish_match(matchId: str, user: User = Depends(require_scorekeeper_or_admin)):
    """Conclude match, lock final scores, and trigger standings recalculation. Requires Scorekeeper or Admin role."""
    try:
        return store.finish_match(matchId)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Match '{matchId}' not found."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
