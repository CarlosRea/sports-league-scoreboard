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
   - Displays real-time OTel span ingestion rates, collector memory usage, active scrape targets, and application telemetry metadata.
