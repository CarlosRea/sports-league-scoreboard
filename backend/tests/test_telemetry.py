import os
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.config import settings
from app.main import app
from app.telemetry import (
    get_in_memory_exporter,
    get_meter,
    get_telemetry_metadata,
    get_telemetry_resource,
    get_tracer,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_telemetry_resource_attributes():
    """Verify that OpenTelemetry Resource contains service name, environment, and deployed version."""
    resource = get_telemetry_resource()
    attrs = resource.attributes

    # Service name verification
    assert "service.name" in attrs
    assert attrs["service.name"] == settings.SERVICE_NAME

    # Environment verification
    assert "environment" in attrs or "deployment.environment" in attrs
    assert (
        attrs.get("environment") == settings.ENVIRONMENT
        or attrs.get("deployment.environment") == settings.ENVIRONMENT
    )

    # Deployed version verification
    assert "service.version" in attrs or "deployed_version" in attrs
    assert (
        attrs.get("service.version") == settings.DEPLOYED_VERSION
        or attrs.get("deployed_version") == settings.DEPLOYED_VERSION
    )


def test_health_endpoint_includes_telemetry(client):
    """GET /health must include telemetry metadata with service name, environment, and deployed version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "telemetry" in data
    telemetry = data["telemetry"]

    assert telemetry["service_name"] == settings.SERVICE_NAME
    assert telemetry["environment"] == settings.ENVIRONMENT
    assert telemetry["deployed_version"] == settings.DEPLOYED_VERSION


def test_api_telemetry_endpoint(client):
    """GET /api/telemetry returns full telemetry metadata and resource attributes."""
    response = client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.json()

    assert "service_name" in data
    assert "environment" in data
    assert "deployed_version" in data
    assert "enabled" in data
    assert "resource_attributes" in data

    assert data["service_name"] == settings.SERVICE_NAME
    assert data["environment"] == settings.ENVIRONMENT
    assert data["deployed_version"] == settings.DEPLOYED_VERSION

    attrs = data["resource_attributes"]
    assert "service.name" in attrs
    assert attrs["service.name"] == settings.SERVICE_NAME


def test_spans_captured_with_telemetry_metadata(client):
    """Verify that HTTP requests produce spans with expected Resource attributes and span attributes."""
    exporter = get_in_memory_exporter()
    assert exporter is not None, "InMemorySpanExporter should be registered"

    exporter.clear()
    response = client.get("/api/leagues")
    assert response.status_code == 200

    spans = exporter.get_finished_spans()
    assert len(spans) > 0, "Expected at least one span to be recorded"

    # Find the main HTTP server span
    server_spans = [s for s in spans if s.name.startswith("GET")]
    assert len(server_spans) > 0

    span = server_spans[0]
    resource_attrs = span.resource.attributes

    # Check resource attributes on the recorded span
    assert resource_attrs.get("service.name") == settings.SERVICE_NAME
    assert (
        resource_attrs.get("environment") == settings.ENVIRONMENT
        or resource_attrs.get("deployment.environment") == settings.ENVIRONMENT
    )
    assert (
        resource_attrs.get("service.version") == settings.DEPLOYED_VERSION
        or resource_attrs.get("deployed_version") == settings.DEPLOYED_VERSION
    )


def test_custom_environment_variable_overrides():
    """Verify that environment variables dynamically override telemetry attributes."""
    with patch.dict(
        os.environ,
        {
            "OTEL_SERVICE_NAME": "custom-scoreboard-service",
            "ENVIRONMENT": "staging",
            "DEPLOYED_VERSION": "20261004-test-sha123",
        },
        clear=False,
    ):
        meta = get_telemetry_metadata()
        assert meta["service_name"] == "custom-scoreboard-service"
        assert meta["environment"] == "staging"
        assert meta["deployed_version"] == "20261004-test-sha123"

        res = get_telemetry_resource()
        assert res.attributes["service.name"] == "custom-scoreboard-service"
        assert res.attributes["environment"] == "staging"
        assert res.attributes["deployed_version"] == "20261004-test-sha123"


def test_tracer_and_meter_helpers():
    """Verify helper functions get_tracer and get_meter return functional OpenTelemetry instances."""
    tracer = get_tracer("unit_test_tracer")
    assert tracer is not None

    with tracer.start_as_current_span("unit_test_span") as span:
        span.set_attribute("test_key", "test_val")

    meter = get_meter("unit_test_meter")
    assert meter is not None
    counter = meter.create_counter("unit_test_counter", description="Test counter")
    counter.add(1, {"test_label": "value"})
