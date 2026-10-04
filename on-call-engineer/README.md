# On-Call Engineer: Automated Alert Poller & Headless Coding Agent

This directory provides an automated, AI-assisted **On-Call Engineer** service for the Sports League Scoreboard application.

It polls the observability alert API (Prometheus Alertmanager / Prometheus / Grafana) every minute. When an alert fires (such as repeated canvas component-creation failures), it extracts the incident context and passes the full alert details to a headless coding agent (e.g. Google Antigravity `agy` CLI or OpenCode) to diagnose, triage, and remediate the issue autonomously.

---

## 1. Architecture & Incident Workflow

```
+-----------------------------------------------------------------------------------+
|                           Observability Stack                                     |
|  - Prometheus Alerting Rules (http://127.0.0.1:9090/api/v1/alerts)               |
|  - Grafana Alertmanager      (http://127.0.0.1:3000/api/alertmanager/...)         |
+-----------------------------------------+-----------------------------------------+
                                          |
                        Polls API Every Minute (60s)
                                          v
+-----------------------------------------------------------------------------------+
|                        On-Call Engineer Alert Poller                              |
|                          (poll_alerts.py)                                         |
|                                                                                   |
|  1. Queries alert endpoint (default: Prometheus /api/v1/alerts)                  |
|  2. Filters for active firing alerts (state == "firing")                         |
|  3. Deduplicates active alerts using incident fingerprint & cooldown             |
|  4. Extracts metadata: service, environment, deployed_version, owner, dashboard  |
|  5. Saves incident record JSON to incidents/ directory                            |
+-----------------------------------------+-----------------------------------------+
                                          |
                     Dispatches Structured Prompt & Context
                                          v
+-----------------------------------------------------------------------------------+
|                       Headless Coding Agent (CLI)                                 |
|                                                                                   |
|  - Primary:  Antigravity CLI (agy --print "{prompt}" --dangerously-skip-perms)   |
|  - Fallback: OpenCode (opencode run --auto "{prompt}")                            |
|  - Custom:   Configurable via --agent-cmd or HEADLESS_AGENT_CMD                  |
|                                                                                   |
|  Actions performed by agent:                                                      |
|  - Inspects Loki error logs and recent git commits for deployed_version           |
|  - Triages root cause (e.g. component render error, missing fallbacks)            |
|  - Implements bugfix, component fallback, or initiates rollback                  |
|  - Runs test suite and verification builds                                        |
+-----------------------------------------------------------------------------------+
```

---

## 2. Alert Metadata Passed to Headless Coding Agent

Every dispatched alert delivers full operational context to the agent:

| Metadata Field | Value Source / Description |
| :--- | :--- |
| **`Alert Name`** | Alert rule identifier (e.g. `CanvasComponentCreationFailures`) |
| **`Severity`** | Critical / Warning |
| **`Service`** | Target service name (`sports-league-scoreboard`) |
| **`Environment`** | Deployment environment (`development` or `production`) |
| **`Deployed Version`** | Exact git/release version tag (e.g. `20261004-213015-83242da`) |
| **`Owner`** | Responsible team (`sports-league-frontend`) |
| **`Dashboard URL`** | Direct Grafana dashboard link filtered to environment & version |
| **`Runbook URL`** | Operational mitigation runbook link |
| **`Summary & Description`** | Impact statement and threshold breach details |
| **`Action`** | Recommended remediation steps |

In addition to the formatted prompt text, the agent subprocess receives these fields as environment variables (`ALERT_NAME`, `ALERT_SERVICE`, `ALERT_ENVIRONMENT`, `ALERT_DEPLOYED_VERSION`, `ALERT_DASHBOARD_URL`, `ALERT_OWNER`, `ALERT_PAYLOAD_JSON`, `ALERT_INCIDENT_FILE`).

---

## 3. Usage & Command Line Options

### Run Continuous Poller (Default: Every 60 seconds)
```bash
./on-call-engineer/poll_alerts.py
```

### Run a Single Poll Cycle & Exit (CI / Healthcheck)
```bash
./on-call-engineer/poll_alerts.py --once
```

### Dry-Run Mode (Preview Agent Prompt without Spawning Subprocess)
```bash
./on-call-engineer/poll_alerts.py --dry-run
```

### Simulate a Firing Alert (Testing)
```bash
./on-call-engineer/poll_alerts.py --mock-alert --dry-run --once
```

### Command Line Flags

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--alert-url` | `http://127.0.0.1:9090/api/v1/alerts` | URL of the observability alert API to poll |
| `--interval` | `60` | Polling interval in seconds (default: 60s / 1 minute) |
| `--agent-cmd` | Auto-detected | Custom agent command template (supports `{prompt}` and `{json_path}`) |
| `--cooldown` | `1800` | Cooldown in seconds before re-dispatching same alert (30 minutes) |
| `--incidents-dir` | `on-call-engineer/incidents` | Path to store dispatched incident JSON records |
| `--once` | `False` | Run one polling cycle and exit |
| `--dry-run` | `False` | Log actions without executing the agent subprocess |
| `--mock-alert` | `False` | Synthesize a firing alert for testing |
| `--verbose`, `-v` | `False` | Enable debug logging |

---

## 4. Headless Coding Agent Integration

The dispatcher automatically checks for available headless coding agent CLIs in this order:

1. **Environment Variable**: `HEADLESS_AGENT_CMD` (e.g. `agy --print "{prompt}" --dangerously-skip-permissions`).
2. **Google Antigravity CLI (`agy`)**: `agy --print "{prompt}" --dangerously-skip-permissions`.
3. **OpenCode CLI (`opencode`)**: `opencode run --auto "{prompt}"`.
4. **Fallback**: Logs and records incident to `incidents/`.

### Custom Agent Example
To invoke a specialized agent or custom script:
```bash
./on-call-engineer/poll_alerts.py --agent-cmd "python3 -m my_agent.runner --incident {json_path}"
```

---

## 5. Automated Tests

Run the test suite:
```bash
uv run pytest on-call-engineer/test_poll_alerts.py
```
