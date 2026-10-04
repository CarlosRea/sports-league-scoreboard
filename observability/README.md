# Sports League Scoreboard - Observability Stack

This directory contains a complete, self-contained **Observability & APM Stack** running as an independent Docker Compose project (`scoreboard-observability`).

---

## 1. Architecture Overview

```
                      Sports League Scoreboard (Backend / App)
                      [ FastAPI + OpenTelemetry Instrumentation ]
                                          |
                      OTLP Traces & Metrics (HTTP :4318 / gRPC :4317)
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                  OpenTelemetry Collector (scoreboard-otel-collector)             |
|                                                                                   |
|  - Receivers:  OTLP gRPC (4317), OTLP HTTP (4318)                                  |
|  - Processors: memory_limiter, batch, resource attributes                         |
|  - Exporters:  otlp/tempo (Traces), prometheus (Metrics), otlphttp/loki (Logs)    |
+--------------------+------------------------+---------------------+---------------+
                     |                        |                     |
            Traces   |               Metrics  |              Logs   |
                     v                        v                     v
+-----------------------------+ +---------------------------+ +--------------------+
|        Grafana Tempo        | |        Prometheus         | |    Grafana Loki    |
|   (Distributed Tracing)     | |  (Metrics TSDB on :9090)  | |  (Log Aggregation) |
|         Port 3200           | | Scrapes Collector on :8889| |     Port 3100      |
+--------------+--------------+ +-------------+-------------+ +----------+---------+
               \                              |                         /
                \                             |                        /
                 \                            |                       /
                  v                           v                      v
+-----------------------------------------------------------------------------------+
|                        Grafana Visualization Dashboard                            |
|             Port 3000 (Pre-provisioned with Tempo, Prometheus, and Loki)           |
+-----------------------------------------------------------------------------------+
```

---

## 2. Included Services & Port Mappings

All services bind exclusively to `127.0.0.1` on the host for local security.

| Service | Container Name | Host Port | Purpose |
| :--- | :--- | :--- | :--- |
| **OpenTelemetry Collector** | `scoreboard-otel-collector` | `127.0.0.1:4317`<br/>`127.0.0.1:4318`<br/>`127.0.0.1:8889`<br/>`127.0.0.1:13133` | OTLP gRPC ingestion<br/>OTLP HTTP ingestion<br/>Prometheus metrics export<br/>Health check |
| **Grafana Tempo** | `scoreboard-tempo` | `127.0.0.1:3200` | Distributed trace query and storage |
| **Prometheus** | `scoreboard-prometheus` | `127.0.0.1:9090` | Time-series metrics database & PromQL |
| **Grafana Loki** | `scoreboard-loki` | `127.0.0.1:3100` | Log ingestion & LogQL query engine |
| **Grafana** | `scoreboard-grafana` | `127.0.0.1:3000` | Pre-configured dashboard & unified exploration |

---

## 3. Starting the Observability Stack

Because this stack is defined as a separate Docker Compose project (`scoreboard-observability`), it can be started, stopped, and scaled independently of the application stacks without container name or network collisions.

### Start all observability services:
```bash
docker compose -f observability/docker-compose.yaml up -d
```
*(Or navigate to `cd observability && docker compose up -d`)*

### Verify container status:
```bash
docker compose -f observability/docker-compose.yaml ps
```

### View logs:
```bash
# All services
docker compose -f observability/docker-compose.yaml logs -f

# Specific service (e.g. OpenTelemetry Collector)
docker compose -f observability/docker-compose.yaml logs -f otel-collector
```

### Stop the stack:
```bash
docker compose -f observability/docker-compose.yaml down
```

---

## 4. Connecting the Application Stack to OpenTelemetry Collector

When the OpenTelemetry Collector is running, set the following environment variable in the backend application or `.env.dev` / `.env.prod`:

```bash
# Send traces to the OpenTelemetry Collector over HTTP OTLP
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318/v1/traces
```

Inside containerized Docker deployments running on the same host, use:
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318/v1/traces
```

The backend automatically packages telemetry with:
- `service.name`: `sports-league-scoreboard`
- `deployment.environment`: `development` or `production`
- `service.version` / `deployed_version`: Deployed release tag (e.g. `20261004-213015-83242da`)

---

## 5. Exploring Telemetry in Grafana

1. Open Grafana in your browser: [http://localhost:3000](http://localhost:3000)
2. **Default Credentials**:
   - Username: `admin`
   - Password: `admin`
3. **Pre-configured Data Sources**:
   - **Prometheus**: Default metrics source.
   - **Tempo**: Configured with trace-to-logs (Loki) and trace-to-metrics (Prometheus) cross-navigation.
   - **Loki**: Configured with derived trace IDs linking directly to Tempo spans.
4. **Pre-configured Dashboard**:
   - Open **Dashboards** ➔ **Scoreboard Observability** ➔ **Sports League Scoreboard - Observability Overview**.
   - **Environment & Deployed Version Filtering**: Use the dashboard dropdown variables (`Environment` and `Deployed Version`) to isolate metrics by deployment environment (`development`, `production`, etc.) or release version.
   - **Application Metrics Panels**:
     - **Matches & Leagues Created** (Counter): Total matches and leagues created, with breakdown by entity type.
     - **Active Live Matches** (Gauge): Real-time count of currently ongoing or active matches (`IN_PROGRESS`).
     - **Score Updates Registered** (Counter): Live score and match event submissions received.
     - **Failures in Score Update** (Counter): Validation errors and failed score submissions, with reason breakdown (`match_not_found`, `validation_error`, `payload_validation_error`, etc.).
     - **Combined Application Metrics Time Series**: Unified multi-line chart comparing matches created, active matches, score updates, and failures over time.
     - **Activity & Rates**: Operational rates for match creation and scorekeeper update traffic vs failure rate.
   - **Pipeline Metrics**: OTel span ingestion rates, collector memory usage, active scrape targets, and healthy pipeline status.


---

## 6. Actionable Alerting: Canvas Component-Creation Failures

The stack includes pre-configured, actionable alerting for repeated canvas component-creation failures in Prometheus and Grafana.

### Alert Definition & Thresholds
- **Alert Name**: `CanvasComponentCreationFailures` (also aliased as `RepeatedCanvasComponentCreationFailures` and `canvas_component_creation_failures`)
- **Metric**: `scoreboard_canvas_component_creation_failures_total` / `canvas_component_creation_failures_total`
- **Threshold**: Exceeding 5 failures within 5 minutes (`increase(...[5m]) > 5`) or sustained failure rate (`rate(...[5m]) > 0.05`).
- **Evaluation Duration**: `for: 5m` (ensuring alert represents sustained, real user impact rather than transient network blips).
- **Real User Impact**: End-users are unable to initialize or interact with the scorekeeper pitch canvas component.

### Actionable Context Fields Included
Every alert instance includes:
1. `service`: `sports-league-scoreboard`
2. `environment`: `{{ $labels.environment }}` (`development` or `production`)
3. `deployed_version`: `{{ $labels.deployed_version }}` (e.g. `20261004-213015-83242da`)
4. `owner`: `sports-league-frontend`
5. `dashboard_url`: `http://localhost:3000/d/scoreboard-observability-overview?var-environment={{ $labels.environment }}&var-deployed_version={{ $labels.deployed_version }}`
6. `action`: Step-by-step remediation plan (inspect Loki logs, inspect recent commits, initiate rollback).
7. `runbook_url`: Direct link to operational runbook / dashboard.

### Verification
```bash
# Validate Prometheus rule syntax with promtool
docker exec scoreboard-prometheus promtool check rules /etc/prometheus/alerting_rules.yml

# Query active Prometheus rules
curl -s http://127.0.0.1:9090/api/v1/rules | jq '.data.groups[0].rules'

# Query Grafana Alerting rules
curl -u admin:admin -s http://127.0.0.1:3000/api/v1/provisioning/alert-rules | jq .
```
