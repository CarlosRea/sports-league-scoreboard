import pytest
from starlette.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers.canvas import reset_canvas_components
from app.telemetry import (
    get_application_metrics_summary,
    get_in_memory_metric_reader,
    reset_application_metrics,
)


@pytest.fixture
def client():
    reset_canvas_components()
    with TestClient(app) as test_client:
        yield test_client
    reset_canvas_components()


def test_standard_scoreboard_canvas_creation(client):
    """Verify that standard scoreboard canvas component creation succeeds with HTTP 201."""
    payload = {
        "component_type": "scoreboard_canvas",
        "name": "Main Stadium Scoreboard",
        "width": 800,
        "height": 600,
        "config": {
            "theme": "dark",
            "anti_aliasing": True,
        },
    }
    response = client.post("/api/canvas/components", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("canvas-")
    assert data["component_type"] == "scoreboard_canvas"
    assert data["name"] == "Main Stadium Scoreboard"
    assert data["width"] == 800
    assert data["height"] == 600
    assert data["status"] == "active"
    assert "created_at" in data


def test_standard_pitch_canvas_creation_succeeds(client):
    """Verify that standard-dimension pitch canvas (<=1920x1080 without tactical overlay) succeeds with HTTP 201."""
    payload = {
        "component_type": "pitch_canvas",
        "name": "Standard Pitch View",
        "width": 800,
        "height": 600,
        "config": {
            "theme": "grass",
            "enable_tactical_overlay": False,
            "texture_quality": "standard",
        },
    }
    response = client.post("/api/canvas/components", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["component_type"] == "pitch_canvas"
    assert data["width"] == 800
    assert data["height"] == 600


def test_standard_formation_canvas_creation(client):
    """Verify that formation canvas creation succeeds with HTTP 201."""
    payload = {
        "component_type": "formation_canvas",
        "name": "Tactical Formation View",
        "width": 1024,
        "height": 768,
    }
    response = client.post("/api/canvas/components", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["component_type"] == "formation_canvas"
    assert data["width"] == 1024
    assert data["height"] == 768


def test_non_pitch_canvas_high_resolution_succeeds(client):
    """Verify that high-resolution on non-pitch canvases (e.g. scoreboard 4K) succeeds without bug."""
    payload = {
        "component_type": "scoreboard_canvas",
        "name": "4K Jumbotron Scoreboard",
        "width": 3840,
        "height": 2160,
    }
    response = client.post("/api/canvas/components", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["width"] == 3840
    assert data["height"] == 2160


def test_canvas_component_list_and_get(client):
    """Verify listing and retrieving individual canvas components."""
    # Create two components
    c1 = client.post(
        "/api/canvas/components",
        json={"component_type": "scoreboard_canvas", "name": "Scoreboard 1"},
    ).json()
    c2 = client.post(
        "/api/canvas/components",
        json={"component_type": "formation_canvas", "name": "Formation 1"},
    ).json()

    # List components
    list_res = client.get("/api/canvas/components")
    assert list_res.status_code == 200
    components = list_res.json()
    assert len(components) == 2
    ids = [c["id"] for c in components]
    assert c1["id"] in ids
    assert c2["id"] in ids

    # Get single component
    get_res = client.get(f"/api/canvas/components/{c1['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Scoreboard 1"

    # Get non-existent
    assert client.get("/api/canvas/components/non-existent-canvas").status_code == 404

    # Delete component
    del_res = client.delete(f"/api/canvas/components/{c1['id']}")
    assert del_res.status_code == 204
    assert client.get(f"/api/canvas/components/{c1['id']}").status_code == 404


def test_pitch_canvas_bug_high_resolution_failure_and_telemetry(client):
    """
    Verify the realistic bug:
    Creating a pitch_canvas with high-resolution / 4K dimensions (>1920) fails with HTTP 500
    and records canvas_component_creation_failures_total with reason='texture_allocation_overflow'.
    """
    reset_application_metrics()

    payload = {
        "component_type": "pitch_canvas",
        "name": "4K Ultra-HD Tactical Pitch",
        "width": 3840,
        "height": 2160,
        "config": {
            "texture_quality": "4k",
            "enable_tactical_overlay": True,
        },
    }

    response = client.post("/api/canvas/components", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert "texture_allocation_overflow" in data["detail"]

    # Verify application metrics counter incremented
    summary = get_application_metrics_summary()
    assert summary["canvas_component_failures"] == 1

    # Verify OpenTelemetry metric recorded with required attributes
    reader = get_in_memory_metric_reader()
    assert reader is not None

    metrics_data = reader.get_metrics_data()
    assert metrics_data is not None

    found_dps = []
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == "canvas_component_creation_failures_total":
                    for dp in metric.data.data_points:
                        found_dps.append(
                            {"value": getattr(dp, "value", None), "attributes": dict(dp.attributes)}
                        )

    assert len(found_dps) > 0
    latest_dp = found_dps[-1]
    assert latest_dp["attributes"].get("service") == settings.SERVICE_NAME
    assert latest_dp["attributes"].get("environment") == settings.ENVIRONMENT
    assert latest_dp["attributes"].get("deployed_version") == settings.DEPLOYED_VERSION
    assert latest_dp["attributes"].get("reason") == "texture_allocation_overflow"
    assert latest_dp["attributes"].get("component_type") == "pitch_canvas"


def test_pitch_canvas_tactical_overlay_triggers_bug(client):
    """Verify that pitch_canvas with tactical pitch overlay enabled fails with HTTP 500 and records metric."""
    reset_application_metrics()

    payload = {
        "component_type": "pitch_canvas",
        "name": "Tactical Pitch Overlay",
        "width": 1280,
        "height": 720,
        "config": {
            "enable_tactical_overlay": True,
        },
    }

    response = client.post("/api/canvas/components", json=payload)
    assert response.status_code == 500
    assert "texture_allocation_overflow" in response.json()["detail"]

    summary = get_application_metrics_summary()
    assert summary["canvas_component_failures"] == 1
