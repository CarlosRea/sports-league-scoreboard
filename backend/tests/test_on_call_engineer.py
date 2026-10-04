"""
Backend test runner integration for on-call engineer alert poller.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add on-call-engineer directory to sys.path so poll_alerts can be imported
on_call_dir = Path(__file__).resolve().parent.parent.parent / "on-call-engineer"
if str(on_call_dir) not in sys.path:
    sys.path.insert(0, str(on_call_dir))

from poll_alerts import (  # noqa: E402
    HEADLESS_AGENT_SYSTEM_PROMPT,
    AlertDetails,
    HeadlessAgentDispatcher,
    IncidentTracker,
    ObservabilityAlertPoller,
    build_agent_prompt,
)


def test_on_call_engineer_prompt_generation():
    """Verify on-call engineer prompt builder contains all critical incident context and system prompt."""
    alert = AlertDetails(
        alertname="CanvasComponentCreationFailures",
        service="sports-league-scoreboard",
        environment="production",
        deployed_version="20261004-213015-83242da",
        owner="sports-league-frontend",
        dashboard_url="http://localhost:3000/d/scoreboard-observability-overview?var-environment=production&var-deployed_version=20261004-213015-83242da",
        severity="critical",
        summary="Canvas component repeated failures",
        description="Threshold >5 in 5m breached",
        action="Rollback deployment",
    )
    prompt = build_agent_prompt(alert)

    # Required verbatim system prompt
    assert HEADLESS_AGENT_SYSTEM_PROMPT in prompt
    assert "You are the on-call engineer for this repository. An alert just fired." in prompt
    assert "Investigate the root cause. Read the code and reproduce the failure." in prompt
    assert (
        "If you find a real bug, make the smallest correction, run the backend tests, and commit the fix with a clear message."
        in prompt
    )
    assert "If the alert is a false positive, explain why and do not change the code." in prompt

    assert alert.service in prompt
    assert alert.environment in prompt
    assert alert.deployed_version in prompt
    assert alert.owner in prompt
    assert alert.dashboard_url in prompt


def test_on_call_engineer_poller_initialization():
    """Verify poller initializes cleanly with default parameters."""
    poller = ObservabilityAlertPoller(
        alert_url="http://127.0.0.1:9090/api/v1/alerts",
        interval_seconds=60,
    )
    assert poller.alert_url == "http://127.0.0.1:9090/api/v1/alerts"
    assert poller.interval_seconds == 60
    assert isinstance(poller.dispatcher, HeadlessAgentDispatcher)
    assert isinstance(poller.tracker, IncidentTracker)
