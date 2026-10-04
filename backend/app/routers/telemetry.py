from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.telemetry import TelemetryMetadata
from app.telemetry import (
    get_telemetry_metadata,
    record_canvas_component_creation_failure,
)

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


class CanvasFailureReport(BaseModel):
    reason: str = Field(default="component_render_failed", description="Failure reason")
    component_type: str = Field(default="canvas", description="Component type")


@router.get("", response_model=TelemetryMetadata)
async def get_telemetry_info():
    """
    Retrieve OpenTelemetry runtime metadata including service name,
    deployment environment, deployed version, and resource attributes.
    """
    return get_telemetry_metadata()


@router.post("/canvas-failure")
async def report_canvas_failure(report: CanvasFailureReport = CanvasFailureReport()):
    """
    Record client-side canvas component-creation failure into OpenTelemetry metrics.
    Includes service, environment, and deployed version in telemetry attributes.
    """
    record_canvas_component_creation_failure(
        reason=report.reason,
        component_type=report.component_type,
    )
    return {"status": "recorded", "reason": report.reason, "component_type": report.component_type}
