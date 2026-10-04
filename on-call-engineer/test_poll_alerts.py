#!/usr/bin/env python3
"""
Unit and integration tests for On-Call Engineer Alert Poller & Headless Agent Dispatcher.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from poll_alerts import (
    HEADLESS_AGENT_SYSTEM_PROMPT,
    AlertDetails,
    AlertParser,
    HeadlessAgentDispatcher,
    IncidentTracker,
    ObservabilityAlertPoller,
    build_agent_prompt,
)


@pytest.fixture
def sample_firing_alert() -> AlertDetails:
    return AlertDetails(
        alertname="CanvasComponentCreationFailures",
        service="sports-league-scoreboard",
        environment="production",
        deployed_version="20261004-213015-83242da",
        owner="sports-league-frontend",
        dashboard_url="http://localhost:3000/d/scoreboard-observability-overview?var-environment=production&var-deployed_version=20261004-213015-83242da",
        severity="critical",
        summary="Repeated canvas component-creation failures detected in production",
        description="Service 'sports-league-scoreboard' (deployed_version: 20261004-213015-83242da) in production is experiencing repeated canvas component-creation failures (>5 failures in 5m).",
        action="1. Inspect frontend logs in Loki. 2. Review recent commits. 3. Roll back if regression confirmed.",
        runbook_url="http://localhost:3000/d/scoreboard-observability-overview",
        state="firing",
        active_at="2026-10-04T22:45:00Z",
        value="8",
    )


def test_alert_details_fingerprint_and_dict(sample_firing_alert: AlertDetails):
    """Verify AlertDetails fingerprint is deterministic and serialization works."""
    expected_fp = "CanvasComponentCreationFailures::sports-league-scoreboard::production::20261004-213015-83242da"
    assert sample_firing_alert.fingerprint == expected_fp

    alert_dict = sample_firing_alert.to_dict()
    assert alert_dict["alertname"] == "CanvasComponentCreationFailures"
    assert alert_dict["service"] == "sports-league-scoreboard"
    assert alert_dict["environment"] == "production"
    assert alert_dict["deployed_version"] == "20261004-213015-83242da"
    assert alert_dict["owner"] == "sports-league-frontend"
    assert alert_dict["dashboard_url"] == sample_firing_alert.dashboard_url


def test_parse_prometheus_alerts_api():
    """Verify parsing Prometheus /api/v1/alerts payload returns only firing alerts with all required fields."""
    prom_payload = {
        "status": "success",
        "data": {
            "alerts": [
                {
                    "labels": {
                        "alertname": "CanvasComponentCreationFailures",
                        "service": "sports-league-scoreboard",
                        "environment": "production",
                        "deployed_version": "20261004-213015-83242da",
                        "owner": "sports-league-frontend",
                        "dashboard_url": "http://localhost:3000/d/scoreboard-observability-overview?var-environment=production&var-deployed_version=20261004-213015-83242da",
                        "severity": "critical",
                    },
                    "annotations": {
                        "summary": "Repeated canvas component-creation failures detected in production",
                        "description": "Pitch canvas rendering failed repeatedly",
                        "action": "Inspect Loki logs and initiate rollback if regression confirmed",
                        "runbook_url": "http://localhost:3000/d/scoreboard-observability-overview",
                    },
                    "state": "firing",
                    "activeAt": "2026-10-04T22:45:00Z",
                    "value": "7",
                },
                {
                    "labels": {
                        "alertname": "SomePendingAlert",
                        "service": "sports-league-scoreboard",
                        "environment": "development",
                    },
                    "state": "pending",
                },
            ]
        },
    }

    parsed = AlertParser.parse(prom_payload)
    assert len(parsed) == 1
    alert = parsed[0]

    assert alert.alertname == "CanvasComponentCreationFailures"
    assert alert.service == "sports-league-scoreboard"
    assert alert.environment == "production"
    assert alert.deployed_version == "20261004-213015-83242da"
    assert alert.owner == "sports-league-frontend"
    assert "scoreboard-observability-overview" in alert.dashboard_url
    assert alert.state == "firing"
    assert alert.severity == "critical"
    assert alert.value == "7"


def test_parse_grafana_alerts_api():
    """Verify parsing Grafana Alertmanager /api/v2/alerts list format."""
    grafana_payload = [
        {
            "labels": {
                "alertname": "RepeatedCanvasComponentCreationFailures",
                "service": "sports-league-scoreboard",
                "environment": "development",
                "deployed_version": "20261004-dev-tag",
                "owner": "sports-league-frontend",
                "dashboard_url": "http://localhost:3000/d/scoreboard-observability-overview",
                "severity": "critical",
            },
            "annotations": {
                "summary": "Canvas creation failure threshold reached",
                "description": "More than 5 failures in 5m",
            },
            "status": {"state": "active"},
            "startsAt": "2026-10-04T22:40:00Z",
        },
        {
            "labels": {"alertname": "SuppressedAlert"},
            "status": {"state": "suppressed"},
        },
    ]

    parsed = AlertParser.parse(grafana_payload)
    assert len(parsed) == 1
    alert = parsed[0]
    assert alert.alertname == "RepeatedCanvasComponentCreationFailures"
    assert alert.service == "sports-league-scoreboard"
    assert alert.environment == "development"
    assert alert.deployed_version == "20261004-dev-tag"
    assert alert.owner == "sports-league-frontend"


def test_build_agent_prompt(sample_firing_alert: AlertDetails):
    """Verify that the generated prompt includes the required system prompt and alert context."""
    prompt = build_agent_prompt(sample_firing_alert)

    # Required system prompt must be present verbatim
    assert HEADLESS_AGENT_SYSTEM_PROMPT in prompt
    assert "You are the on-call engineer for this repository. An alert just fired." in prompt
    assert "Investigate the root cause. Read the code and reproduce the failure." in prompt
    assert (
        "If you find a real bug, make the smallest correction, run the backend tests, and commit the fix with a clear message."
        in prompt
    )
    assert "If the alert is a false positive, explain why and do not change the code." in prompt

    # Required alert metadata fields must be in prompt
    assert "CanvasComponentCreationFailures" in prompt
    assert "sports-league-scoreboard" in prompt
    assert "production" in prompt
    assert "20261004-213015-83242da" in prompt
    assert "sports-league-frontend" in prompt
    assert sample_firing_alert.dashboard_url in prompt
    assert "CRITICAL" in prompt


def test_headless_agent_dispatcher_execution(tmp_path: Path, sample_firing_alert: AlertDetails):
    """Verify dispatcher formats command, passes environment variables, and invokes subprocess."""
    incidents_dir = tmp_path / "incidents"
    dispatcher = HeadlessAgentDispatcher(
        agent_cmd=["echo", "[TEST_AGENT]:", "{prompt}"],
        dry_run=False,
        incidents_dir=incidents_dir,
    )

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Incident resolved", stderr="")

        result = dispatcher.dispatch(sample_firing_alert)
        assert result is not None
        assert mock_run.called

        args, kwargs = mock_run.call_args
        cmd_executed = args[0]
        assert cmd_executed[0] == "echo"
        assert cmd_executed[1] == "[TEST_AGENT]:"
        assert "sports-league-scoreboard" in cmd_executed[2]

        env_passed = kwargs["env"]
        assert env_passed["ALERT_NAME"] == "CanvasComponentCreationFailures"
        assert env_passed["ALERT_SERVICE"] == "sports-league-scoreboard"
        assert env_passed["ALERT_ENVIRONMENT"] == "production"
        assert env_passed["ALERT_DEPLOYED_VERSION"] == "20261004-213015-83242da"
        assert env_passed["ALERT_OWNER"] == "sports-league-frontend"

        # Verify incident JSON file was created
        incident_files = list(incidents_dir.glob("*.json"))
        assert len(incident_files) == 1
        with open(incident_files[0], encoding="utf-8") as f:
            data = json.load(f)
            assert data["alert"]["alertname"] == "CanvasComponentCreationFailures"


def test_headless_agent_dispatcher_dry_run(tmp_path: Path, sample_firing_alert: AlertDetails):
    """Verify dry_run=True saves incident record but skips subprocess.run."""
    incidents_dir = tmp_path / "incidents"
    dispatcher = HeadlessAgentDispatcher(
        agent_cmd=["agy", "-p", "{prompt}"],
        dry_run=True,
        incidents_dir=incidents_dir,
    )

    with patch("subprocess.run") as mock_run:
        result = dispatcher.dispatch(sample_firing_alert)
        assert result is None
        assert not mock_run.called

        incident_files = list(incidents_dir.glob("*.json"))
        assert len(incident_files) == 1


def test_incident_tracker_deduplication_and_cooldown(sample_firing_alert: AlertDetails):
    """Verify incident tracker prevents duplicate dispatches within cooldown."""
    tracker = IncidentTracker(cooldown_seconds=10)

    # First time -> should dispatch
    assert tracker.should_dispatch(sample_firing_alert) is True
    tracker.record_dispatch(sample_firing_alert)

    # Immediately after -> should NOT dispatch (in cooldown)
    assert tracker.should_dispatch(sample_firing_alert) is False

    # Simulate time passing beyond cooldown
    tracker._active_incidents[sample_firing_alert.fingerprint] -= 15
    assert tracker.should_dispatch(sample_firing_alert) is True


def test_incident_tracker_cleanup_resolved(sample_firing_alert: AlertDetails):
    """Verify tracker purges alerts that stop firing."""
    tracker = IncidentTracker(cooldown_seconds=60)
    tracker.record_dispatch(sample_firing_alert)
    assert sample_firing_alert.fingerprint in tracker._active_incidents

    # Cleanup with empty active set (alert ceased firing)
    tracker.cleanup_resolved(set())
    assert sample_firing_alert.fingerprint not in tracker._active_incidents


def test_poller_poll_once_with_mock_api(sample_firing_alert: AlertDetails):
    """Verify ObservabilityAlertPoller queries API, parses response, and dispatches."""
    fake_response = json.dumps(
        {
            "status": "success",
            "data": {
                "alerts": [
                    {
                        "labels": {
                            "alertname": sample_firing_alert.alertname,
                            "service": sample_firing_alert.service,
                            "environment": sample_firing_alert.environment,
                            "deployed_version": sample_firing_alert.deployed_version,
                            "owner": sample_firing_alert.owner,
                            "dashboard_url": sample_firing_alert.dashboard_url,
                            "severity": "critical",
                        },
                        "annotations": {
                            "summary": sample_firing_alert.summary,
                            "description": sample_firing_alert.description,
                        },
                        "state": "firing",
                    }
                ]
            },
        }
    ).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = fake_response
    mock_resp.__enter__.return_value = mock_resp

    mock_dispatcher = MagicMock()
    mock_tracker = MagicMock()
    mock_tracker.should_dispatch.return_value = True

    poller = ObservabilityAlertPoller(
        alert_url="http://mock-alert-api/api/v1/alerts",
        interval_seconds=60,
        dispatcher=mock_dispatcher,
        tracker=mock_tracker,
    )

    with patch("urllib.request.urlopen", return_value=mock_resp):
        alerts = poller.poll_once()
        assert len(alerts) == 1
        assert alerts[0].alertname == sample_firing_alert.alertname
        assert mock_dispatcher.dispatch.called
        assert mock_tracker.record_dispatch.called
