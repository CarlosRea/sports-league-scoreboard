from pydantic import BaseModel, Field


class ApplicationMetricsSummary(BaseModel):
    matches_created: int = Field(default=0, description="Total matches or leagues created")
    active_live_matches: int = Field(
        default=0, description="Currently ongoing or active live matches"
    )
    score_updates_registered: int = Field(
        default=0, description="Total score and event updates submitted"
    )
    score_update_failures: int = Field(
        default=0, description="Total failed score submissions or validation errors"
    )
    canvas_component_failures: int = Field(
        default=0, description="Total canvas component-creation failures"
    )


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
    application_metrics: ApplicationMetricsSummary | None = Field(
        default=None, description="Summary of tracked application metrics"
    )
