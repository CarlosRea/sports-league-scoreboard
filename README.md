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

## 🚀 Quick Start

### Option 1: Run Full Stack with PostgreSQL (Recommended)

Run the complete production-grade stack (**PostgreSQL 16** + **FastAPI Backend** + **React Frontend**) with Docker Compose:

```bash
# Launch PostgreSQL and Application containers
make compose-up
# Or directly: docker compose up -d --build
```

- **Web Application**: Open [http://localhost:8009](http://localhost:8009)
- **API Documentation**: Open [http://localhost:8009/docs](http://localhost:8009/docs) (Swagger UI) or [http://localhost:8009/redoc](http://localhost:8009/redoc) (ReDoc)
- **PostgreSQL Host Port**: `localhost:5434` (User: `sdip`, Password: `sdip`, Database: `sdip`)

To stop the Docker Compose stack:
```bash
make compose-down
# Or directly: docker compose down
```

#### Running PostgreSQL Standalone via Docker

You can also start PostgreSQL and the app container individually on a Docker network:

```bash
# 1. Create network
docker network create scoreboard-network || true

# 2. Start PostgreSQL 16
docker run -d \
  --name scoreboard-db \
  --network scoreboard-network \
  -e POSTGRES_USER=sdip \
  -e POSTGRES_PASSWORD=sdip \
  -e POSTGRES_DB=sdip \
  -p 5434:5432 \
  -v scoreboard-pgdata:/var/lib/postgresql/data \
  postgres:16-alpine

# 3. Build & run App container connected to Postgres
docker build -t sports-scoreboard:latest .

docker run -d --rm -p 8009:8009 \
  --network scoreboard-network \
  -e DATABASE_URL=postgresql://sdip:sdip@scoreboard-db:5432/sdip \
  -e PORT=8009 \
  --name sports-scoreboard sports-scoreboard:latest
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
| `make compose-up` | Launch complete stack (App + PostgreSQL) with Docker Compose |
| `make compose-down` | Stop and remove Docker Compose containers |
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
    Trigger["Push to main / Pull Request"] --> Tests
    
    subgraph Tests ["Parallel Unit & Quality Tests"]
        BackendJob["Job: test-backend<br/>• Astral uv sync<br/>• Ruff lint check<br/>• 41 Pytest unit tests"]
        FrontendJob["Job: test-frontend<br/>• Node 22 & npm ci<br/>• Oxlint & tsc typecheck<br/>• 5 Vitest unit tests<br/>• Vite production build"]
    end
    
    BackendJob --> IntegrationJob["Job: integration-and-e2e<br/>• Build & start Docker Compose stack<br/>• Verify http://localhost:8009/health<br/>• Pytest integration tests (tests/test_api.py)<br/>• Playwright E2E tests (tests/e2e/)<br/>• Tear down compose stack"]
    FrontendJob --> IntegrationJob
    
    IntegrationJob --> DeployJob["Job: deploy (CD)<br/>• Trigger: Push to main<br/>• Build tagged production container<br/>• Automated deployment rollout<br/>• Eliminates manual admin credentials"]
```

### Automated Pipeline Stages:
1. **Parallel Test Execution** (Runs concurrently for maximum speed):
   - **`test-backend`**: Sets up Python 3.12 with `astral-sh/setup-uv@v5`, syncs dependencies, runs `ruff check`, and executes the Pytest unit test suite.
   - **`test-frontend`**: Sets up Node 22, installs dependencies via `npm ci`, runs `oxlint`, executes TypeScript typechecking (`tsc --noEmit`), runs Vitest tests, and verifies the production bundle build (`npm run build`).
2. **Container Build, Health Check & E2E Verification**:
   - **`integration-and-e2e`** (`needs: [test-backend, test-frontend]`):
     - Builds and boots the multi-service Docker Compose stack (`docker compose up -d --build`).
     - Polls and validates that the container is healthy via `http://localhost:8009/health`.
     - Executes integration tests and Playwright browser tests via `make e2e`.
     - Automatically cleans up the compose stack (`docker compose down -v`).
3. **Continuous Deployment (CD)**:
   - **`deploy`** (`needs: [integration-and-e2e]`, triggers only on `push` to `main`):
     - Builds and tags the release container image (`sports-scoreboard:${{ github.sha }}`).
     - Deploys the application automatically to production.
     - Replaces manual administrator credentials with automated, auditable CI/CD execution.

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
│       └── ci-cd.yml           # GitHub Actions CI/CD pipeline definition
├── AGENTS.md                   # Operating standards & guidelines for developers and AI
├── Dockerfile                  # Multi-stage production container build (Node + Python/uv)
├── docker-compose.yaml         # Multi-service stack (PostgreSQL 16 + FastAPI/React app)
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
