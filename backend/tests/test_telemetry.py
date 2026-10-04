import os
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.config import settings
from app.main import app
from app.telemetry import (
    get_active_matches_count,
    get_application_metrics_summary,
    get_in_memory_exporter,
    get_in_memory_metric_reader,
    get_meter,
    get_telemetry_metadata,
    get_telemetry_resource,
    get_tracer,
    record_match_created,
    record_score_update_failure,
    record_score_update_registered,
    reset_application_metrics,
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


def test_application_metrics_recorded_with_environment_and_deployed_version():
    """Verify that all application metrics include environment and deployed_version attributes."""
    reset_application_metrics()

    record_match_created("match")
    record_match_created("league")
    record_score_update_registered("match-301")
    record_score_update_failure("validation_error", "match-301")

    reader = get_in_memory_metric_reader()
    assert reader is not None, "InMemoryMetricReader must be configured"

    metrics_data = reader.get_metrics_data()
    assert metrics_data is not None

    target_metric_names = {
        "matches_created_total",
        "active_live_matches",
        "score_updates_registered_total",
        "score_update_failures_total",
    }

    found_metrics: dict[str, list[dict]] = {}
    for rm in metrics_data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name in target_metric_names:
                    dp_list = []
                    for dp in metric.data.data_points:
                        dp_list.append(
                            {"value": getattr(dp, "value", None), "attributes": dict(dp.attributes)}
                        )
                    found_metrics[metric.name] = dp_list

    # 1. matches created (counter: total matches or leagues created)
    assert "matches_created_total" in found_metrics
    match_dps = found_metrics["matches_created_total"]
    types_found = {dp["attributes"].get("type") for dp in match_dps}
    assert "match" in types_found
    assert "league" in types_found
    for dp in match_dps:
        assert dp["attributes"].get("environment") == settings.ENVIRONMENT
        assert dp["attributes"].get("deployed_version") == settings.DEPLOYED_VERSION

    # 2. active live matches (gauge: currently ongoing or active matches)
    assert "active_live_matches" in found_metrics
    gauge_dps = found_metrics["active_live_matches"]
    assert len(gauge_dps) > 0
    for dp in gauge_dps:
        assert dp["attributes"].get("environment") == settings.ENVIRONMENT
        assert dp["attributes"].get("deployed_version") == settings.DEPLOYED_VERSION
        assert dp["value"] >= 0

    # 3. score updates registered (counter: total score/event updates submitted)
    assert "score_updates_registered_total" in found_metrics
    score_dps = found_metrics["score_updates_registered_total"]
    assert len(score_dps) > 0
    for dp in score_dps:
        assert dp["attributes"].get("environment") == settings.ENVIRONMENT
        assert dp["attributes"].get("deployed_version") == settings.DEPLOYED_VERSION
        assert dp["attributes"].get("status") == "success"

    # 4. failures in score update (counter: failed score submissions or validation errors)
    assert "score_update_failures_total" in found_metrics
    fail_dps = found_metrics["score_update_failures_total"]
    assert len(fail_dps) > 0
    for dp in fail_dps:
        assert dp["attributes"].get("environment") == settings.ENVIRONMENT
        assert dp["attributes"].get("deployed_version") == settings.DEPLOYED_VERSION
        assert "reason" in dp["attributes"]


def test_active_matches_observable_gauge(client, scorekeeper_headers):
    """Verify active_live_matches gauge accurately reflects matches in IN_PROGRESS status."""
    initial_count = get_active_matches_count()

    # match-302 is SCHEDULED initially. Starting it should increment active matches.
    res_start = client.post("/api/matches/match-302/start", headers=scorekeeper_headers)
    assert res_start.status_code == 200
    assert get_active_matches_count() == initial_count + 1

    # Finishing match-302 should return active matches back to initial_count
    res_finish = client.post("/api/matches/match-302/finish", headers=scorekeeper_headers)
    assert res_finish.status_code == 200
    assert get_active_matches_count() == initial_count


def test_api_endpoints_trigger_application_metrics(client, admin_headers, scorekeeper_headers):
    """Verify HTTP operations update the application metric counters."""
    reset_application_metrics()

    # Create league -> matches_created increment
    res_league = client.post(
        "/api/leagues",
        json={
            "name": "App Metric Test League",
            "season": "2026/2027",
            "sportType": "Soccer",
            "pointsWin": 3,
            "pointsDraw": 1,
            "pointsLoss": 0,
        },
        headers=admin_headers,
    )
    assert res_league.status_code == 201
    created_league_id = res_league.json()["id"]
    summary = get_application_metrics_summary()
    assert summary["matches_created"] == 1

    # Create match fixture -> matches_created increment
    res_match = client.post(
        f"/api/leagues/{created_league_id}/matches",
        json={
            "homeTeamId": "team-riverside",
            "awayTeamId": "team-apex",
            "matchday": 5,
            "scheduledAt": "2026-09-22T18:00:00Z",
        },
        headers=admin_headers,
    )
    assert res_match.status_code == 201
    summary = get_application_metrics_summary()
    assert summary["matches_created"] == 2

    # Successful score update -> score_updates_registered increment
    res_score = client.patch(
        "/api/matches/match-301/score",
        json={"homeScore": 3, "awayScore": 1, "period": "2nd Half", "minute": 80},
        headers=scorekeeper_headers,
    )
    assert res_score.status_code == 200
    summary = get_application_metrics_summary()
    assert summary["score_updates_registered"] == 1

    # Failed score update: Unknown match -> score_update_failures increment
    res_fail_notfound = client.patch(
        "/api/matches/non-existent-match-xyz/score",
        json={"homeScore": 2, "awayScore": 0},
        headers=scorekeeper_headers,
    )
    assert res_fail_notfound.status_code == 404
    summary = get_application_metrics_summary()
    assert summary["score_update_failures"] == 1

    # Failed score update: Negative score payload validation error -> score_update_failures increment
    res_fail_val = client.patch(
        "/api/matches/match-301/score",
        json={"homeScore": -5, "awayScore": 1},
        headers=scorekeeper_headers,
    )
    assert res_fail_val.status_code == 422
    summary = get_application_metrics_summary()
    assert summary["score_update_failures"] == 2


def test_telemetry_endpoints_include_application_metrics(client):
    """Verify /health and /api/telemetry return application_metrics summary."""
    res_health = client.get("/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert "telemetry" in health_data
    assert "application_metrics" in health_data["telemetry"]
    app_metrics = health_data["telemetry"]["application_metrics"]
    assert "matches_created" in app_metrics
    assert "active_live_matches" in app_metrics
    assert "score_updates_registered" in app_metrics
    assert "score_update_failures" in app_metrics

    res_telemetry = client.get("/api/telemetry")
    assert res_telemetry.status_code == 200
    telemetry_data = res_telemetry.json()
    assert "application_metrics" in telemetry_data
    assert telemetry_data["application_metrics"]["matches_created"] >= 0
