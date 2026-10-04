# 🏆 Sports League Scoreboard

A modern, responsive web application designed for amateur sports leagues to manage schedules, record pitchside live scores, complete matches, and automatically compute official league standings.

The application features a contract-first architecture with a **React 19 + TypeScript + Vite** frontend and a **FastAPI + SQLAlchemy + uv** backend, complete with a multi-stage **Docker** build serving frontend static files and API endpoints from a single container.

---

## 📌 Features

- **⚽ Pitchside Live Scorekeeper**: Interactive modal for updating live match scores in real time with quick increment buttons and instantaneous status updates (`SCHEDULED` ➔ `IN_PROGRESS` ➔ `FINISHED`).
- **📊 Automated Standings Calculation Engine**:
  - Implements the standard amateur **3-1-0 points system** (3 for a win, 1 for a draw, 0 for a loss).
  - Deterministic tie-breakers: **Points (PTS)** ➔ **Goal Difference (GD)** ➔ **Goals For (GF)** ➔ **Head-to-Head Record** ➔ **Team Name (Alphabetical)**.
  - **Live Provisional Toggle**: View potential league standings that factor in matches currently in progress.
- **🛡️ Contract-First & Type-Safe**: OpenAPI 3.0 schema defined at [`openapi.yaml`](./openapi.yaml) and mirrored in TypeScript domain types.
- **🔐 JWT Authentication**: Role-based access control with hashed passwords (bcrypt) for sensitive scorekeeping and match management operations.
- **🗄️ Database-Agnostic Storage (PostgreSQL & SQLite)**: Backed by SQLAlchemy ORM with SQLite for instant zero-dependency local setup and PostgreSQL 16 with connection health checks for production (`DATABASE_URL` / `SDIP_DATABASE_URL`).
- **🐳 Multi-Stage Production Docker**: Single container running on port `8009` that compiles the React app with Node and serves it directly through FastAPI with SPA routing and path-traversal protection.
- **🚀 Automated CI/CD Pipeline (GitHub Actions)**: Parallel test execution, Docker Compose orchestration, health check verification (`/health`), Playwright E2E browser testing, and automated continuous deployment.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide React |
| **Backend** | Python 3.12, FastAPI, Astral `uv`, SQLAlchemy 2.0, Pydantic v2, PyJWT, `psycopg2-binary` |
| **Databases** | PostgreSQL 16 (production), SQLite (local dev fallback) |
| **Testing** | Vitest (frontend unit), Pytest & pytest-asyncio (backend unit & API integration), Playwright (E2E browser tests) |
| **Linting & Types**| Oxlint & TypeScript (frontend), Ruff (backend) |
| **DevOps & CI/CD** | Multi-stage Docker, Docker Compose, GitHub Actions CI/CD (`.github/workflows/ci-cd.yml`) |

---

## 🏗️ Dual-Environment Infrastructure (Production & Development)

The project supports two completely independent infrastructure stacks that can run concurrently on the same host with zero conflict:

| Feature / Setting | Development Environment (Dev) | Production Environment (Prod) |
| :--- | :--- | :--- |
| **Purpose** | Local staging, testing, active coding | Stable release, live scorekeeping |
| **Compose File** | `docker-compose.yaml` / `docker-compose.dev.yaml` | `docker-compose.prod.yaml` |
| **Compose Project** | `sports-league-scoreboard` | `scoreboard-prod` |
| **App URL** | [http://localhost:8009](http://localhost:8009) | [http://localhost:8010](http://localhost:8010) |
| **App Container** | `scoreboard-app` | `scoreboard-prod-app` |
| **App Image** | `sports-scoreboard:latest` | `sports-scoreboard:prod` |
| **PostgreSQL Port** | `5434` (`localhost:5434`) | `5435` (`localhost:5435`) |
| **PostgreSQL Container** | `scoreboard-db` | `scoreboard-prod-db` |
| **Postgres Database / User** | `sdip` / `sdip` | `scoreboard_prod` / `scoreboard_prod_user` |
| **Database Volume** | `scoreboard-pgdata` | `scoreboard-prod-pgdata` (isolated storage) |
| **Docker Network** | `sports-league-scoreboard_default` | `scoreboard-prod-network` (isolated bridge) |
| **JWT Secrets** | Dedicated dev secret (`.env.dev`) | Dedicated prod secret (`.env.prod`) |
| **Restart Policy** | `unless-stopped` | `unless-stopped` (with log rotation) |
| **Health Checks** | Postgres `pg_isready` | Postgres `pg_isready` + App `/health` |

---

## 🚀 Quick Start

### 1. Production Environment (Second Independent Stack)

To build and launch the production stack:

```bash
# Launch production stack on port 8010 (App) and 5435 (PostgreSQL)
make compose-up-prod
# Or directly: docker compose -f docker-compose.prod.yaml --env-file .env.prod up -d --build
```

- **Production App**: Open [http://localhost:8010](http://localhost:8010)
- **API Docs**: Open [http://localhost:8010/docs](http://localhost:8010/docs)
- **Health Check**: Open [http://localhost:8010/health](http://localhost:8010/health)
- **PostgreSQL Port**: `localhost:5435` (User: `scoreboard_prod_user`, DB: `scoreboard_prod`)

To check health and run automated integration tests against production:
```bash
make test-prod
```

To stop the production stack:
```bash
make compose-down-prod
```

### 2. Development Environment (Existing Stack)

To run the development stack:

```bash
# Launch dev stack on port 8009 (App) and 5434 (PostgreSQL)
make compose-up
# Or directly: docker compose up -d --build
```

- **Dev App**: Open [http://localhost:8009](http://localhost:8009)
- **API Docs**: Open [http://localhost:8009/docs](http://localhost:8009/docs)
- **Health Check**: Open [http://localhost:8009/health](http://localhost:8009/health)
- **PostgreSQL Port**: `localhost:5434` (User: `sdip`, DB: `sdip`)

To stop the development stack:
```bash
make compose-down
```


---

### Option 2: Run with SQLite in a Single Container

For local testing without a database server, run with the internal SQLite engine:

```bash
# Build Docker image
make build-docker

# Run container on port 8009
make run-docker
```

To stop:
```bash
make stop-docker
```

---

### Option 3: Local Development

#### Prerequisites
- [Node.js](https://nodejs.org/) (>= 20) & `npm`
- [uv](https://docs.astral.sh/uv/) (Astral Python package manager, >= 0.5.0)
- Python 3.12+

#### 1. Install Dependencies
```bash
# Install both backend and frontend dependencies
make install

# Or individually:
make install-backend
make install-frontend
```

#### 2. Run Applications

**Start Backend (Port 8009 with SQLite):**
```bash
make run-backend
# Or directly: cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8009
```

**Start Backend against PostgreSQL:**
```bash
export SDIP_DATABASE_URL=postgresql://sdip:sdip@localhost:5434/sdip
make run
# Or: cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8009
```

**Start Frontend (Port 5173):**
```bash
make run-frontend
# Or directly: cd frontend && npm run dev
```

**Run Both Concurrently:**
```bash
make dev
```

- **Frontend Dev Server**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://127.0.0.1:8009/api](http://127.0.0.1:8009/api)
- **API Health Check**: [http://127.0.0.1:8009/health](http://127.0.0.1:8009/health)

---

## 🔑 Demo Credentials & Pre-Seeded Data

The backend automatically creates an initial SQLite database (`scoreboard.db`) seeded with sample data on startup:

- **Admin User**:
  - **Email**: `admin@league.local`
  - **Password**: `Admin123!`
  - **Role**: `ADMIN`
- **Pre-Seeded League**: *Metropolitan Amateur Premier League (2026 / 2027)*
- **Sample Teams**: Downtown FC, Riverside Athletic, Highland Rovers, Metro United, Eastside City, Valley Olympic.
- **Sample Matches**: Finished and in-progress matches to showcase the live standings calculations.

---

## 📋 Makefile Commands Reference

| Target | Description |
| :--- | :--- |
| `make help` | Display list of available commands |
| `make install` | Install both frontend (`npm ci`) and backend (`uv sync`) dependencies |
| `make install-backend` | Sync Python virtual environment with `uv sync` |
| `make install-frontend`| Install Node modules with `npm ci` |
| `make run-backend` | Start FastAPI backend server on `http://127.0.0.1:8009` |
| `make run-frontend` | Start Vite frontend dev server on `http://127.0.0.1:5173` |
| `make dev` | Launch backend and frontend concurrently |
| `make test` | Run complete test suite (both backend pytest and frontend vitest) |
| `make test-backend` | Run backend unit and integration tests with `uv run pytest` |
| `make test-frontend`| Run frontend unit tests with `npm run test` |
| `make lint` | Run backend (`ruff`) and frontend (`oxlint` + `tsc`) linting |
| `make build-frontend`| Compile production React assets into `frontend/dist/` |
| `make build-docker` | Build production multi-stage Docker image |
| `make compose-up` | Launch development stack (App :8009 + PostgreSQL :5434) |
| `make compose-down` | Stop development stack |
| `make compose-up-prod` | Launch isolated production stack (App :8010 + PostgreSQL :5435) |
| `make compose-down-prod`| Stop and remove production stack |
| `make compose-logs-prod`| Follow production container logs |
| `make compose-ps-prod` | View production container status |
| `make test-prod` | Verify health and run API integration tests against production |
| `make e2e` | Run integration (pytest) and Playwright E2E tests against running stack |
| `make clean` | Clean up build outputs, caches, and test artifacts |

---

## 🧪 Testing & Code Quality

### Backend Unit Tests (41 Tests)
Comprehensive unit tests covering JWT authentication, database persistence, CRUD routers, standings calculations, CORS policies, static file serving, and scorekeeping:
```bash
make test-backend
# Or: cd backend && uv run pytest
```

### Frontend Unit Tests (5 Tests)
Vitest unit tests verifying the 3-1-0 standings calculation rules and deterministic tie-breaking logic:
```bash
make test-frontend
# Or: cd frontend && npm run test
```

### Integration & End-to-End (E2E) Test Suite
The repository includes automated tests running against the live multi-container environment:

1. **Backend Integration Tests (`tests/test_api.py`)**:
   - Validates that `GET /health` returns HTTP 200 with status `"healthy"`.
   - Validates all `/api` endpoints against live PostgreSQL data (`/api/leagues`, `/api/leagues/{id}/matches`, `/api/matches/{id}`, `/api/leagues/{id}/standings`, `/api/leagues/{id}/teams`).
2. **Playwright E2E Browser Tests (`tests/e2e/test_scoreboard.spec.ts`)**:
   - Executes against the live container stack at `http://localhost:8009`.
   - Verifies scoreboard page loading, tournament title, and standings table display.
   - Verifies navigation to the Matches & Fixtures calendar view and match cards.
   - Tests the interactive Pitchside Scorekeeper modal, simulating a goal increment and real-time score component updates.

**Execute All Integration & E2E Tests with a Single Command:**
```bash
# 1. Start application stack with PostgreSQL
make compose-up

# 2. Run backend integration + Playwright browser tests
make e2e
```

### Linting & Type Checking
```bash
make lint
# Or separately: make lint-backend && make lint-frontend
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

The repository includes a production-grade CI/CD pipeline configured at [`.github/workflows/ci-cd.yml`](./.github/workflows/ci-cd.yml).

### Pipeline Flow:

```mermaid
flowchart TD
    Trigger["Push to main"] --> Tests
    
    subgraph Tests ["Parallel Unit & Integration Gates"]
        BackendJob["Job: test-backend<br/>• uv sync & ruff lint<br/>• Pytest unit tests"]
        FrontendJob["Job: test-frontend<br/>• npm ci & oxlint<br/>• tsc typecheck & vitest<br/>• Vite production build"]
    end
    
    BackendJob --> IntegrationJob["Job: integration-and-e2e<br/>• Test Compose stack on runner<br/>• Health check verification<br/>• Integration & E2E tests"]
    FrontendJob --> IntegrationJob
    
    IntegrationJob --> BuildJob["Stage 1: Build & Push (GHCR)<br/>• Tag: YYYYMMDD-HHMMSS-shortsha<br/>• Push to ghcr.io using GITHUB_TOKEN"]
    
    BuildJob --> DeployDevJob["Stage 2: Deploy to Dev (Oracle Cloud)<br/>• SSH into Oracle Cloud server<br/>• Pull exact tagged image from ghcr.io<br/>• Update dev container (scoreboard-app)"]
    
    DeployDevJob -.->|"Manual Promotion (workflow_dispatch)"| PromoJob["Manual Promotion Workflow<br/>• Detect tag currently running in dev<br/>• Pull exact same image on Oracle Cloud<br/>• Deploy to production container (scoreboard-prod-app)"]
```

### Two-Stage CI/CD Pipeline (`ci-cd.yml`):
1. **Quality & Integration Gates**:
   - **`test-backend`**: Runs in parallel; sets up Python 3.12 + Astral `uv`, executes `ruff check`, and runs unit tests.
   - **`test-frontend`**: Runs in parallel; sets up Node 22, executes `oxlint`, `tsc --noEmit`, Vitest, and production Vite compilation.
   - **`integration-and-e2e`**: Spins up the application stack on the GitHub Actions runner, confirms `/health`, and runs API integration + Playwright browser tests.
2. **Stage 1 — Build & Push (`build`)**:
   - Builds the production Docker image.
   - Tags it using the strict **`YYYYMMDD-HHMMSS-shortsha`** timestamp pattern (e.g. `20261004-213015-83242da`).
   - Authenticates to **GitHub Container Registry (`ghcr.io`)** with the built-in `GITHUB_TOKEN`.
   - Pushes the tagged image (`ghcr.io/<owner>/<repo>:<tag>`), along with `:latest` and `:dev` tags.
3. **Stage 2 — Deploy to Dev (`deploy-dev`)**:
   - Establishes a secure SSH connection to the **Oracle Cloud server** via `appleboy/ssh-action@v1`.
   - Authenticates with `ghcr.io` directly on the server.
   - Pulls the exact tagged image from `ghcr.io`.
   - Runs/updates the development container (`scoreboard-app`) on port `8009` with zero disruption to the dev database (`scoreboard-db`).
   - Records the active tag to `.current-dev-tag` and `.current-dev-image`.
   - Verifies the dev health endpoint (`http://localhost:8009/health`).

---

### 🚀 Manual Production Promotion Workflow (`promote-to-production.yml`)

The production deployment follows an immutable container promotion paradigm: **build once for dev, promote the exact same tested artifact to production**.

The workflow is triggered manually via `workflow_dispatch`:
- **Takes the tag currently running in dev** (inspects `.current-dev-image` or container runtime metadata).
- **Pulls that exact same image** on the Oracle Cloud server from `ghcr.io`.
- **Deploys it to the production container** (`scoreboard-prod-app` on port `8010`) using `docker-compose.prod.yaml`.
- **Verifies production health** at `http://localhost:8010/health`.

#### Triggering the Promotion Workflow:
1. **GitHub Web UI**: Navigate to **Actions** ➔ **Promote Dev to Production** ➔ **Run workflow**.
2. **GitHub CLI (`gh`)**:
   ```bash
   gh workflow run promote-to-production.yml \
     -f promotion_notes="Promoting verified dev release to production"
   ```
3. **Local CLI Equivalent**:
   ```bash
   make promote-to-prod
   ```

#### Promotion Architecture:
```mermaid
flowchart LR
    DevRunning["Dev Container (:8009)<br/>Running: ghcr.io/...:20261004-213015-83242da"] -->|Detect Tag| Inspector["Inspect Running Dev Tag<br/>.current-dev-tag / container inspect"]
    Inspector -->|Pull Exact Image| Pull["docker pull ghcr.io/...:20261004-213015-83242da"]
    Pull -->|Deploy to Prod| ProdContainer["Production Container (:8010)<br/>scoreboard-prod-app"]
    ProdContainer -->|Healthcheck| Verified["Verify http://localhost:8010/health"]
```

---

## 📡 OpenTelemetry Observability

The backend is fully instrumented with **OpenTelemetry** for distributed tracing, metrics, and application performance monitoring:

- **Included Telemetry Attributes**:
  - **Service Name**: `service.name` / `service_name` (default: `sports-league-scoreboard`, configurable via `OTEL_SERVICE_NAME` or `SERVICE_NAME`)
  - **Environment**: `deployment.environment` / `environment` (e.g. `development`, `production`, configurable via `ENVIRONMENT`)
  - **Deployed Version**: `service.version` / `deployed_version` / `deployed.version` (e.g. `20261004-213015-83242da`, configurable via `DEPLOYED_VERSION` or `OTEL_SERVICE_VERSION`)
- **Automatic Instrumentation**:
  - **FastAPI HTTP Spans**: Automatically instruments route handlers, request methods, URLs, status codes, and request latencies.
  - **SQLAlchemy DB Spans**: Automatically instruments database queries, statements, and transaction execution.
  - **OpenTelemetry Metrics**: `MeterProvider` configured with unified Resource attributes.
- **Exporting & Integration**:
  - Supports standard OpenTelemetry collector endpoints via `OTEL_EXPORTER_OTLP_ENDPOINT` (e.g., Jaeger, Grafana Tempo, SigNoz, Datadog).
  - Built-in `InMemorySpanExporter` for testing and zero-overhead local development without requiring external collectors.
- **Introspection Endpoints**:
  - `GET /health`: Returns service health along with active telemetry metadata.
  - `GET /api/telemetry`: Returns full telemetry configuration, status, and OpenTelemetry Resource attributes.

---

## 📐 Standings Calculation Engine

Official standings are derived from finished matches using the standard amateur scoring rules:
- **Win**: 3 points
- **Draw**: 1 point
- **Loss**: 0 points

### Tie-Breaker Priority Hierarchy:
1. **Points (PTS)**: Higher points rank higher.
2. **Goal Difference (GD)**: $\text{Goals For} - \text{Goals Against}$.
3. **Goals For (GF)**: Total goals scored.
4. **Head-to-Head Points**: Points earned in matches between the tied teams.
5. **Team Name**: Alphabetical ascending order as a deterministic tie-breaker.

---

## 📂 Repository Structure

```
sports-league-scoreboard/
├── .github/
│   └── workflows/
│       ├── ci-cd.yml                   # Automated CI/CD pipeline (tests & automated deployment)
│       └── promote-to-production.yml   # Manual workflow promoting dev version to production
├── AGENTS.md                   # Operating standards & guidelines for developers and AI
├── Dockerfile                  # Multi-stage production container build (Node + Python/uv)
├── docker-compose.yaml         # Development stack (PostgreSQL 16 + FastAPI/React app on :8009)
├── docker-compose.dev.yaml     # Explicit development compose stack specification
├── docker-compose.prod.yaml    # Production stack (Second independent copy on :8010 & :5435)
├── .env.dev.example            # Development environment configuration template
├── .env.prod.example           # Production environment configuration template
├── .dockerignore               # Excludes virtual environments, caches, and secrets
├── Makefile                    # Unified development, testing, and Docker commands
├── openapi.yaml                # OpenAPI 3.0 contract specification
├── playwright.config.ts        # Playwright E2E configuration (baseURL: http://localhost:8009)
├── pytest.ini                  # Root pytest configuration
├── README.md                   # Project documentation and quick start guide
├── docs/
│   ├── spec.md                 # Detailed functional & technical system specification
│   └── ai-usage-report.md      # Comprehensive AI tools and prompts usage report
├── tests/                      # System integration & E2E test suite
│   ├── test_api.py             # Backend API & health integration tests
│   ├── test_environment_isolation.py # Automated Dev vs Prod environment isolation tests
│   └── e2e/
│       └── test_scoreboard.spec.ts # Playwright browser E2E test suite
├── frontend/                   # React 19 + TypeScript + Vite web application
│   ├── src/
│   │   ├── components/         # UI components (Standings, Scorekeeper, Matches, Teams)
│   │   ├── services/           # Centralized service layer (HTTP client & mock fallback)
│   │   ├── types/              # TypeScript domain models
│   │   └── utils/              # Standings calculation engine & tie-breakers
│   └── package.json
└── backend/                    # FastAPI + SQLAlchemy + uv backend
    ├── app/
    │   ├── database/           # SQLAlchemy models, engine, and seed data
    │   ├── models/             # Pydantic request/response schemas
    │   ├── routers/            # API route handlers (Auth, Leagues, Teams, Matches, Standings)
    │   ├── services/           # Business logic (Standings engine, Auth & JWT)
    │   ├── config.py           # Application settings & environment variables
    │   └── main.py             # FastAPI entrypoint & SPA static file serving
    ├── tests/                  # Pytest backend unit test suite (41 tests)
    └── pyproject.toml          # Python dependencies managed with uv
```

---

## 📄 License

MIT License. Open source for amateur sports leagues and tournament organizers.
