from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin
from app.models.auth import User
from app.store import store

router = APIRouter(prefix="/dev", tags=["Dev"])


@router.post("/reset")
async def reset_demo_data(admin: User = Depends(require_admin)):
    """Reset database to initial sample demo data. Requires Administrator role."""
    store.reset_data()
    return {"message": "Demo dataset successfully reset."}
