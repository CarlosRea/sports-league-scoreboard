from fastapi import APIRouter

from app.models.telemetry import TelemetryMetadata
from app.telemetry import get_telemetry_metadata

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("", response_model=TelemetryMetadata)
async def get_telemetry_info():
    """
    Retrieve OpenTelemetry runtime metadata including service name,
    deployment environment, deployed version, and resource attributes.
    """
    return get_telemetry_metadata()
