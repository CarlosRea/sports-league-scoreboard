from pydantic import BaseModel, ConfigDict, Field


class CanvasComponentConfig(BaseModel):
    """Configuration options for rendering a canvas component."""

    model_config = ConfigDict(extra="allow")

    theme: str = Field(
        default="dark", description="Visual theme for the canvas (e.g. dark, light, grass)"
    )
    enable_tactical_overlay: bool = Field(
        default=False, description="Enable tactical pitch overlay grid and player markers"
    )
    texture_quality: str = Field(
        default="standard", description="Texture rendering quality (e.g. standard, high, 4k)"
    )
    anti_aliasing: bool = Field(default=True, description="Enable anti-aliasing")
    custom_layers: list[str] = Field(
        default_factory=list, description="Optional custom rendering layer identifiers"
    )


class CreateCanvasComponentDto(BaseModel):
    """Payload for creating a new canvas rendering component."""

    model_config = ConfigDict(extra="allow")

    component_type: str = Field(
        ...,
        description="Type of canvas component (e.g. scoreboard_canvas, pitch_canvas, formation_canvas)",
        examples=["scoreboard_canvas", "pitch_canvas", "formation_canvas"],
    )
    name: str | None = Field(
        default=None, description="Human-readable label for the canvas component"
    )
    width: int = Field(default=800, ge=1, le=8192, description="Canvas width in pixels")
    height: int = Field(default=600, ge=1, le=8192, description="Canvas height in pixels")
    config: CanvasComponentConfig = Field(
        default_factory=CanvasComponentConfig,
        description="Configuration parameters for rendering",
    )


class CanvasComponent(BaseModel):
    """Represents an active canvas component instance."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Unique canvas component identifier")
    component_type: str = Field(..., description="Component type")
    name: str = Field(..., description="Component name")
    width: int = Field(..., description="Canvas width in pixels")
    height: int = Field(..., description="Canvas height in pixels")
    config: CanvasComponentConfig = Field(..., description="Configuration parameters")
    status: str = Field(default="active", description="Operational status: active, ready, error")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp of creation")
