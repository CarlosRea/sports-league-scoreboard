#!/usr/bin/env python3
"""
On-Call Engineer Alert Poller & Headless Coding Agent Dispatcher.

Polls the observability alert API (Prometheus Alertmanager / Prometheus / Grafana)
every minute. When an alert fires, extracts the alert details (service, environment,
deployed_version, owner, dashboard_url, summary, description, action) and passes
them to a headless coding agent (such as Google Antigravity `agy` CLI or OpenCode).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import signal
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [on-call-engineer] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("on-call-engineer")


@dataclass
class AlertDetails:
    """Normalized alert model containing all required observability metadata."""

    alertname: str
    service: str
    environment: str
    deployed_version: str
    owner: str
    dashboard_url: str
    severity: str = "critical"
    summary: str = ""
    description: str = ""
    action: str = ""
    runbook_url: str = ""
    state: str = "firing"
    active_at: str = ""
    value: str = ""
    raw_labels: dict[str, str] = field(default_factory=dict)
    raw_annotations: dict[str, str] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Deterministic fingerprint key for alert deduplication."""
        return f"{self.alertname}::{self.service}::{self.environment}::{self.deployed_version}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize alert details to dictionary."""
        return asdict(self)


class AlertParser:
    """Parses raw JSON responses from Prometheus or Grafana alert APIs."""

    @staticmethod
    def parse(data: Any) -> list[AlertDetails]:
        """
        Extract active firing alerts from Prometheus /api/v1/alerts,
        Prometheus /api/v1/rules, or Grafana alertmanager endpoints.
        """
        raw_alerts: list[dict[str, Any]] = []

        if isinstance(data, list):
            # Grafana alertmanager API format: list of alert objects
            raw_alerts = [item for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            # Prometheus /api/v1/alerts format: {"status": "success", "data": {"alerts": [...]}}
            if "data" in data and isinstance(data["data"], dict) and "alerts" in data["data"]:
                raw_alerts = data["data"]["alerts"]
            # Prometheus /api/v1/rules format: {"data": {"groups": [{"rules": [{"alerts": [...]}]}]}}
            elif "data" in data and isinstance(data["data"], dict) and "groups" in data["data"]:
                for group in data["data"]["groups"]:
                    for rule in group.get("rules", []):
                        for alert_item in rule.get("alerts", []):
                            raw_alerts.append(alert_item)
            elif "alerts" in data and isinstance(data["alerts"], list):
                raw_alerts = data["alerts"]
            elif "items" in data and isinstance(data["items"], list):
                raw_alerts = data["items"]

        parsed_alerts: list[AlertDetails] = []
        for raw in raw_alerts:
            parsed = AlertParser._normalize_alert(raw)
            if parsed and parsed.state.lower() in ("firing", "active"):
                parsed_alerts.append(parsed)

        return parsed_alerts

    @staticmethod
    def _normalize_alert(raw: dict[str, Any]) -> AlertDetails | None:
        """Normalize labels and annotations into a structured AlertDetails instance."""
        labels: dict[str, str] = {str(k): str(v) for k, v in raw.get("labels", {}).items()}
        annotations: dict[str, str] = {
            str(k): str(v) for k, v in raw.get("annotations", {}).items()
        }

        # Determine state
        state = raw.get("state")
        if not state:
            status = raw.get("status", {})
            state = status.get("state", "firing") if isinstance(status, dict) else "firing"

        # Determine alertname
        alertname = (
            labels.get("alertname")
            or labels.get("rulename")
            or annotations.get("alertname")
            or raw.get("name", "UnknownAlert")
        )

        # Service name (fallback to default service if absent)
        service = (
            labels.get("service")
            or annotations.get("service")
            or labels.get("service_name")
            or "sports-league-scoreboard"
        )

        # Environment (development, production, etc.)
        environment = (
            labels.get("environment")
            or annotations.get("environment")
            or labels.get("deployment_environment")
            or "unknown"
        )

        # Deployed version
        deployed_version = (
            labels.get("deployed_version")
            or annotations.get("deployed_version")
            or labels.get("service_version")
            or "unknown"
        )

        # Owner team or on-call rotation
        owner = labels.get("owner") or annotations.get("owner") or "sports-league-frontend"

        # Dashboard URL
        dashboard_url = (
            labels.get("dashboard_url")
            or annotations.get("dashboard_url")
            or f"http://localhost:3000/d/scoreboard-observability-overview?var-environment={environment}&var-deployed_version={deployed_version}"
        )

        severity = labels.get("severity") or annotations.get("severity") or "critical"
        summary = (
            annotations.get("summary")
            or annotations.get("title")
            or f"{alertname} in {environment}"
        )
        description = (
            annotations.get("description") or f"Alert {alertname} fired for service {service}."
        )
        action = (
            annotations.get("action")
            or "Check logs in Loki, review recent commits, and consider rollback."
        )
        runbook_url = annotations.get("runbook_url") or dashboard_url

        active_at = raw.get("activeAt") or raw.get("startsAt") or ""
        value = str(raw.get("value", ""))

        return AlertDetails(
            alertname=alertname,
            service=service,
            environment=environment,
            deployed_version=deployed_version,
            owner=owner,
            dashboard_url=dashboard_url,
            severity=severity,
            summary=summary,
            description=description,
            action=action,
            runbook_url=runbook_url,
            state=str(state),
            active_at=active_at,
            value=value,
            raw_labels=labels,
            raw_annotations=annotations,
        )


def build_agent_prompt(alert: AlertDetails) -> str:
    """
    Construct a comprehensive, actionable prompt for the headless coding agent.
    Includes all alert context: service, environment, deployed version, owner,
    dashboard URL, summary, description, and remediation guidelines.
    """
    prompt = f"""[ACTION REQUIRED: ON-CALL CODING AGENT INCIDENT DISPATCH]
An observability alert is currently FIRING for the Sports League Scoreboard service.

================================================================================
ALERT CONTEXT & METADATA
================================================================================
Alert Name:        {alert.alertname}
Severity:          {alert.severity.upper()}
Service Name:      {alert.service}
Environment:       {alert.environment}
Deployed Version:  {alert.deployed_version}
Component Owner:   {alert.owner}
Dashboard URL:     {alert.dashboard_url}
Runbook URL:       {alert.runbook_url}
Active Since:      {alert.active_at or "Recent"}
Trigger Value:     {alert.value or "Threshold breached"}

================================================================================
INCIDENT SUMMARY & DESCRIPTION
================================================================================
Summary:
{alert.summary}

Detailed Description:
{alert.description}

Recommended Remediation Action:
{alert.action}

================================================================================
INSTRUCTIONS FOR HEADLESS CODING AGENT
================================================================================
You are the automated On-Call Coding Agent.
1. Inspect the service '{alert.service}' in environment '{alert.environment}'.
2. Review recent code changes associated with deployed version '{alert.deployed_version}'.
3. If this alert represents repeated canvas component-creation failures:
   - Examine frontend canvas initialization, error boundaries, and WebGL/2D fallback logic.
   - Verify backend error logging in telemetry and /api/telemetry endpoints.
4. Implement the required bugfix, component fallback, or rollback procedure.
5. Execute unit tests and verification builds to ensure the fix is validated.
"""
    return prompt.strip()


class HeadlessAgentDispatcher:
    """Dispatches firing alert details to a headless coding agent subprocess."""

    def __init__(
        self,
        agent_cmd: list[str] | str | None = None,
        dry_run: bool = False,
        timeout_seconds: int = 300,
        incidents_dir: Path | str = "on-call-engineer/incidents",
    ) -> None:
        self.dry_run = dry_run
        self.timeout_seconds = timeout_seconds
        self.incidents_dir = Path(incidents_dir)
        self.incidents_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(agent_cmd, str) and agent_cmd.strip():
            self.agent_cmd: list[str] = agent_cmd.split()
        elif isinstance(agent_cmd, list) and len(agent_cmd) > 0:
            self.agent_cmd = list(agent_cmd)
        else:
            self.agent_cmd = self.detect_agent_command()

    @staticmethod
    def detect_agent_command() -> list[str]:
        """Auto-detect available headless coding agent command on the host system."""
        # 1. Custom command from environment variable
        env_cmd = os.getenv("HEADLESS_AGENT_CMD")
        if env_cmd:
            logger.info("Using HEADLESS_AGENT_CMD from environment: %s", env_cmd)
            return env_cmd.split()

        # 2. Google Antigravity CLI (agy)
        agy_bin = shutil.which("agy")
        if agy_bin:
            logger.info("Detected Antigravity CLI at: %s", agy_bin)
            return [agy_bin, "--print", "{prompt}", "--dangerously-skip-permissions"]

        # 3. OpenCode CLI
        opencode_bin = shutil.which("opencode")
        if opencode_bin:
            logger.info("Detected OpenCode CLI at: %s", opencode_bin)
            return [opencode_bin, "run", "--auto", "{prompt}"]

        # 4. Fallback echo agent
        logger.warning("No headless agent CLI detected; falling back to echo dispatcher.")
        return ["echo", "[HEADLESS-AGENT-DISPATCH]:", "{prompt}"]

    def dispatch(self, alert: AlertDetails) -> subprocess.CompletedProcess | None:
        """
        Record the incident and invoke the headless coding agent with alert details.
        Passes alert details via prompt formatting, JSON incident file, and environment variables.
        """
        timestamp_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in alert.alertname)
        incident_file = self.incidents_dir / f"incident_{timestamp_str}_{safe_name}.json"

        # Construct prompt
        prompt = build_agent_prompt(alert)

        # Save incident record
        incident_record = {
            "dispatched_at": datetime.now(UTC).isoformat(),
            "alert": alert.to_dict(),
            "prompt": prompt,
            "agent_command": self.agent_cmd,
        }
        with open(incident_file, "w", encoding="utf-8") as f:
            json.dump(incident_record, f, indent=2)
        logger.info("Saved incident metadata to: %s", incident_file)

        # Prepare subprocess environment
        sub_env = os.environ.copy()
        sub_env.update(
            {
                "ALERT_NAME": alert.alertname,
                "ALERT_SERVICE": alert.service,
                "ALERT_ENVIRONMENT": alert.environment,
                "ALERT_DEPLOYED_VERSION": alert.deployed_version,
                "ALERT_OWNER": alert.owner,
                "ALERT_DASHBOARD_URL": alert.dashboard_url,
                "ALERT_SEVERITY": alert.severity,
                "ALERT_SUMMARY": alert.summary,
                "ALERT_DESCRIPTION": alert.description,
                "ALERT_ACTION": alert.action,
                "ALERT_INCIDENT_FILE": str(incident_file.resolve()),
                "ALERT_PAYLOAD_JSON": json.dumps(alert.to_dict()),
            }
        )

        # Build final command line arguments
        cmd_args: list[str] = []
        prompt_substituted = False
        for token in self.agent_cmd:
            if "{prompt}" in token:
                token = token.replace("{prompt}", prompt)
                prompt_substituted = True
            if "{json_path}" in token:
                token = token.replace("{json_path}", str(incident_file.resolve()))
            cmd_args.append(token)

        if not prompt_substituted and cmd_args[0] != "echo":
            cmd_args.append(prompt)

        cmd_display = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd_args[:3])
        logger.info(
            "Dispatching alert '%s' to headless coding agent (%s...)", alert.alertname, cmd_display
        )

        if self.dry_run:
            logger.info(
                "[DRY-RUN] Headless agent invocation skipped. Prompt preview:\n%s", prompt[:300]
            )
            return None

        try:
            result = subprocess.run(
                cmd_args,
                env=sub_env,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            if result.returncode == 0:
                logger.info(
                    "Headless coding agent successfully completed response for alert '%s'.",
                    alert.alertname,
                )
                if result.stdout:
                    logger.info("Agent output:\n%s", result.stdout.strip())
            else:
                logger.error(
                    "Headless coding agent exited with code %d. Stderr:\n%s",
                    result.returncode,
                    result.stderr.strip() if result.stderr else "(empty)",
                )
            return result
        except subprocess.TimeoutExpired:
            logger.error("Headless coding agent timed out after %d seconds.", self.timeout_seconds)
            return None
        except Exception as e:
            logger.exception("Failed to execute headless coding agent: %s", e)
            return None


class IncidentTracker:
    """Tracks active alerts to prevent duplicate agent dispatches within a cooldown window."""

    def __init__(self, cooldown_seconds: int = 1800) -> None:
        self.cooldown_seconds = cooldown_seconds
        # Mapping from alert fingerprint to last dispatch timestamp
        self._active_incidents: dict[str, float] = {}

    def should_dispatch(self, alert: AlertDetails) -> bool:
        """Return True if the alert is new or its cooldown period has expired."""
        now = time.time()
        last_dispatched = self._active_incidents.get(alert.fingerprint)
        if last_dispatched is None:
            return True
        elapsed = now - last_dispatched
        if elapsed >= self.cooldown_seconds:
            logger.info(
                "Cooldown expired for alert '%s' (%ds elapsed). Re-dispatching.",
                alert.alertname,
                int(elapsed),
            )
            return True
        logger.debug(
            "Alert '%s' is in cooldown (%ds / %ds remaining). Skipping duplicate dispatch.",
            alert.alertname,
            int(self.cooldown_seconds - elapsed),
            self.cooldown_seconds,
        )
        return False

    def record_dispatch(self, alert: AlertDetails) -> None:
        """Mark an alert fingerprint as dispatched at the current time."""
        self._active_incidents[alert.fingerprint] = time.time()

    def cleanup_resolved(self, currently_firing_fingerprints: set[str]) -> None:
        """Remove alerts that are no longer firing from the tracking table."""
        resolved = [fp for fp in self._active_incidents if fp not in currently_firing_fingerprints]
        for fp in resolved:
            logger.info("Alert '%s' is no longer firing; marked as resolved.", fp)
            del self._active_incidents[fp]


class ObservabilityAlertPoller:
    """Polls observability alert API at a regular interval and dispatches firing alerts."""

    def __init__(
        self,
        alert_url: str = "http://127.0.0.1:9090/api/v1/alerts",
        interval_seconds: int = 60,
        dispatcher: HeadlessAgentDispatcher | None = None,
        tracker: IncidentTracker | None = None,
    ) -> None:
        self.alert_url = alert_url
        self.interval_seconds = interval_seconds
        self.dispatcher = dispatcher or HeadlessAgentDispatcher()
        self.tracker = tracker or IncidentTracker()
        self._running = False

    def fetch_alerts(self) -> list[AlertDetails]:
        """Fetch and parse active alerts from the configured alert API."""
        try:
            req = urllib.request.Request(
                self.alert_url,
                headers={"Accept": "application/json", "User-Agent": "on-call-engineer/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8")
                data = json.loads(content)
                return AlertParser.parse(data)
        except urllib.error.URLError as e:
            logger.warning("Failed to connect to alert API at %s: %s", self.alert_url, e)
            return []
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response from %s: %s", self.alert_url, e)
            return []
        except Exception as e:
            logger.error("Unexpected error fetching alerts from %s: %s", self.alert_url, e)
            return []

    def poll_once(self) -> list[AlertDetails]:
        """Execute a single polling cycle. Dispatches new firing alerts to headless agent."""
        logger.debug("Polling observability alert API: %s", self.alert_url)
        alerts = self.fetch_alerts()

        current_firing_fps = {a.fingerprint for a in alerts}
        self.tracker.cleanup_resolved(current_firing_fps)

        if not alerts:
            logger.info("Poll cycle: 0 active firing alerts. System healthy.")
            return []

        logger.warning("Poll cycle: %d active firing alert(s) detected!", len(alerts))
        dispatched: list[AlertDetails] = []
        for alert in alerts:
            if self.tracker.should_dispatch(alert):
                logger.info(
                    "FIRING ALERT: name='%s', service='%s', env='%s', version='%s', owner='%s'",
                    alert.alertname,
                    alert.service,
                    alert.environment,
                    alert.deployed_version,
                    alert.owner,
                )
                self.dispatcher.dispatch(alert)
                self.tracker.record_dispatch(alert)
                dispatched.append(alert)
            else:
                logger.info("FIRING ALERT (already being handled): '%s'", alert.alertname)

        return alerts

    def run_loop(self) -> None:
        """Run continuous polling loop every minute (or configured interval)."""
        self._running = True
        logger.info(
            "Starting On-Call Engineer alert polling loop (URL: %s, Interval: %ds)...",
            self.alert_url,
            self.interval_seconds,
        )

        def handle_signal(sig, frame):
            logger.info("Received signal %s; shutting down on-call engineer poller.", sig)
            self._running = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        while self._running:
            try:
                self.poll_once()
            except Exception as e:
                logger.exception("Unhandled error during poll cycle: %s", e)

            # Sleep in small increments to respond quickly to termination signals
            sleep_remaining = self.interval_seconds
            while self._running and sleep_remaining > 0:
                step = min(sleep_remaining, 1.0)
                time.sleep(step)
                sleep_remaining -= step

        logger.info("On-Call Engineer alert poller stopped.")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="On-Call Engineer: Poll observability alert API every minute and pass firing alerts to a headless coding agent.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--alert-url",
        default=os.getenv("ALERT_API_URL", "http://127.0.0.1:9090/api/v1/alerts"),
        help="URL of the observability alert API to poll (Prometheus or Grafana Alertmanager)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("POLL_INTERVAL_SECONDS", "60")),
        help="Polling interval in seconds (default: 60s / 1 minute)",
    )
    parser.add_argument(
        "--agent-cmd",
        default=os.getenv("HEADLESS_AGENT_CMD", None),
        help="Command to invoke the headless coding agent. Supports {prompt} and {json_path} placeholders. Defaults to auto-detecting 'agy' or 'opencode'.",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=int(os.getenv("ALERT_COOLDOWN_SECONDS", "1800")),
        help="Cooldown window in seconds before re-dispatching the same alert to the agent",
    )
    parser.add_argument(
        "--incidents-dir",
        default="on-call-engineer/incidents",
        help="Directory to save incident JSON files",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Execute a single polling cycle and exit immediately (useful for testing and CI)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log alert processing and agent prompt without executing the agent subprocess",
    )
    parser.add_argument(
        "--mock-alert",
        action="store_true",
        help="Simulate a firing CanvasComponentCreationFailures alert for testing",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose debug logging",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the on-call engineer alert poller."""
    args = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    dispatcher = HeadlessAgentDispatcher(
        agent_cmd=args.agent_cmd,
        dry_run=args.dry_run,
        incidents_dir=args.incidents_dir,
    )
    tracker = IncidentTracker(cooldown_seconds=args.cooldown)

    poller = ObservabilityAlertPoller(
        alert_url=args.alert_url,
        interval_seconds=args.interval,
        dispatcher=dispatcher,
        tracker=tracker,
    )

    if args.mock_alert:
        logger.info("Injecting simulated firing alert for testing...")
        mock_alert = AlertDetails(
            alertname="CanvasComponentCreationFailures",
            service="sports-league-scoreboard",
            environment="production",
            deployed_version="20261004-213015-83242da",
            owner="sports-league-frontend",
            dashboard_url="http://localhost:3000/d/scoreboard-observability-overview?var-environment=production&var-deployed_version=20261004-213015-83242da",
            severity="critical",
            summary="Repeated canvas component-creation failures detected in production",
            description="Service 'sports-league-scoreboard' (deployed_version: 20261004-213015-83242da) in production is experiencing repeated canvas component-creation failures (>5 failures in 5m).",
            action="Inspect frontend logs in Loki, review recent commits, and initiate rollback if regression confirmed.",
            runbook_url="http://localhost:3000/d/scoreboard-observability-overview",
            state="firing",
            active_at=datetime.now(UTC).isoformat(),
            value="7",
        )
        dispatcher.dispatch(mock_alert)
        if args.once:
            return

    if args.once:
        poller.poll_once()
    else:
        poller.run_loop()


if __name__ == "__main__":
    main()
