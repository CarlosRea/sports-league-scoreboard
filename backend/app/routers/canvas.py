import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.models.canvas import CanvasComponent, CreateCanvasComponentDto
from app.telemetry import record_canvas_component_creation_failure

logger = logging.getLogger("uvicorn.canvas")

router = APIRouter(prefix="/canvas", tags=["Canvas"])

# In-memory component registry for canvas rendering components
_canvas_components: dict[str, CanvasComponent] = {}


def _should_fail_canvas_creation(payload: CreateCanvasComponentDto) -> bool:
    """
    Simulates a realistic offscreen GPU buffer / texture allocation failure.

    For pitch canvas components, high-resolution rendering surfaces (>1920px width or
    >1080px height) and tactical pitch overlay layers require large contiguous 32-bit RGBA
    texture buffers. When dimensions exceed 1080p viewport (width > 1920 or height > 1080)
    or tactical pitch overlays / 4K textures are requested, texture buffer allocation overflows,
    triggering a 500 Internal Server Error and recording the OpenTelemetry failure metric.
    """
    if payload.component_type == "pitch_canvas":
        # 1. High-resolution / 4K dimensions exceeding 1080p (> 1920 width or > 1080 height)
        if payload.width > 1920 or payload.height > 1080:
            return True
        # 2. Tactical pitch overlay texture initialization
        if payload.config.enable_tactical_overlay:
            return True
        # 3. 4K / High texture quality specification
        if payload.config.texture_quality.lower() in ("high", "4k", "ultra"):
            return True

    return False


@router.post("/components", response_model=CanvasComponent, status_code=status.HTTP_201_CREATED)
async def create_canvas_component(payload: CreateCanvasComponentDto):
    """
    Create a new canvas rendering component (e.g. scoreboard_canvas, pitch_canvas, formation_canvas).

    Standard requests (e.g. scoreboard_canvas or standard pitch canvas at 800x600) succeed with HTTP 201.
    High-resolution pitch canvas components (>1920px or tactical overlays) trigger a texture buffer allocation
    overflow resulting in HTTP 500 and an OpenTelemetry failure metric emission.
    """
    if _should_fail_canvas_creation(payload):
        logger.error(
            "Texture allocation overflow: failed to allocate offscreen GPU texture buffer for %s (%dx%d, overlay=%s)",
            payload.component_type,
            payload.width,
            payload.height,
            payload.config.enable_tactical_overlay,
        )
        record_canvas_component_creation_failure(
            reason="texture_allocation_overflow",
            component_type=payload.component_type,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize canvas component: texture_allocation_overflow during pitch texture buffer generation.",
        )

    component_id = f"canvas-{uuid.uuid4().hex[:8]}"
    name = payload.name or f"{payload.component_type.replace('_', ' ').title()}"
    component = CanvasComponent(
        id=component_id,
        component_type=payload.component_type,
        name=name,
        width=payload.width,
        height=payload.height,
        config=payload.config,
        status="active",
        created_at=datetime.now(UTC).isoformat(),
    )
    _canvas_components[component_id] = component
    logger.info(
        "Canvas component created: id=%s type=%s (%dx%d)",
        component_id,
        payload.component_type,
        payload.width,
        payload.height,
    )
    return component


@router.get("/components", response_model=list[CanvasComponent])
async def list_canvas_components():
    """List all active canvas rendering components."""
    return list(_canvas_components.values())


@router.get("/components/{component_id}", response_model=CanvasComponent)
async def get_canvas_component(component_id: str):
    """Retrieve an active canvas rendering component by its unique ID."""
    component = _canvas_components.get(component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas component '{component_id}' not found.",
        )
    return component


@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_component(component_id: str):
    """Delete a canvas component by ID."""
    if component_id in _canvas_components:
        del _canvas_components[component_id]
        return None
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Canvas component '{component_id}' not found.",
    )


def reset_canvas_components() -> None:
    """Clear canvas components store (useful for unit test isolation)."""
    _canvas_components.clear()
