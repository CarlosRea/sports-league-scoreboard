from pydantic import BaseModel, Field


class TelemetryMetadata(BaseModel):
    service_name: str = Field(..., description="Service name instrumented in OpenTelemetry")
    environment: str = Field(
        ..., description="Deployment environment (e.g. development, production)"
    )
    deployed_version: str = Field(..., description="Application version deployed")
    enabled: bool = Field(True, description="Whether OpenTelemetry instrumentation is active")
    resource_attributes: dict[str, str] = Field(
        default_factory=dict, description="OpenTelemetry Resource attributes"
    )
