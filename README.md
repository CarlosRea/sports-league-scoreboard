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
- **🗄️ Database-Agnostic Storage**: Backed by SQLAlchemy ORM with SQLite default and parameterized queries for security. Configurable via `DATABASE_URL` for PostgreSQL/MySQL.
- **🐳 Multi-Stage Production Docker**: Single container running on port `8009` that compiles the React app with Node and serves it directly through FastAPI with SPA routing and path-traversal protection.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide React |
| **Backend** | Python 3.12, FastAPI, Astral `uv`, SQLAlchemy 2.0, Pydantic v2, PyJWT |
| **Testing** | Vitest (frontend), Pytest & pytest-asyncio (backend) |
| **Linting** | Oxlint & TypeScript (frontend), Ruff (backend) |
| **Containerization**| Docker (Multi-stage `node:22-alpine` + `python:3.12-slim` with `uv`) |

---

## 🚀 Quick Start

### Option 1: Run with Docker (Recommended)

Run both the frontend and backend in a single, self-contained container:

```bash
# Build Docker image
make build-docker

# Run container on port 8009
make run-docker
```

- **Web Application**: Open [http://localhost:8009](http://localhost:8009)
- **API Documentation**: Open [http://localhost:8009/docs](http://localhost:8009/docs) (Swagger UI) or [http://localhost:8009/redoc](http://localhost:8009/redoc) (ReDoc)

To stop and remove the container:
```bash
make stop-docker
```

---

### Option 2: Local Development

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

**Start Backend (Port 8009):**
```bash
make run-backend
# Or directly: cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8009
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
| `make run-docker` | Run Docker container in background on port `8009` |
| `make stop-docker` | Stop and remove the Docker container |
| `make clean` | Clean up build outputs, caches, and test artifacts |

---

## 🧪 Testing & Code Quality

### Backend Tests
35 comprehensive tests covering JWT authentication, database persistence, CRUD routers, standings calculations, CORS policies, and scorekeeping:
```bash
make test-backend
```

### Frontend Tests
Vitest unit tests verifying the 3-1-0 standings calculation rules and deterministic tie-breaking logic:
```bash
make test-frontend
```

### Linting
```bash
make lint
```

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
├── AGENTS.md               # Operating standards & guidelines for AI and developers
├── Dockerfile              # Multi-stage production container build
├── .dockerignore           # Excludes virtual environments, caches, and secrets
├── Makefile                # Unified development, testing, and Docker commands
├── README.md               # Project documentation and quick start guide
├── openapi.yaml            # OpenAPI 3.0 contract specification
├── docs/
│   ├── spec.md             # Detailed functional & technical system specification
│   └── ai-usage-report.md  # Comprehensive AI tools and prompts usage report
├── frontend/               # React 19 + TypeScript + Vite web application
│   ├── src/
│   │   ├── components/     # UI components (Standings, Scorekeeper, Matches, Teams)
│   │   ├── services/       # Centralized service layer (HTTP client & mock fallback)
│   │   ├── types/          # TypeScript domain models
│   │   └── utils/          # Standings calculation engine & tie-breakers
│   └── package.json
└── backend/                # FastAPI + SQLAlchemy + uv backend
    ├── app/
    │   ├── database/       # SQLAlchemy models, engine, and seed data
    │   ├── models/         # Pydantic request/response schemas
    │   ├── routers/        # API route handlers (Auth, Leagues, Teams, Matches, Standings)
    │   ├── services/       # Business logic (Standings engine, Auth & JWT)
    │   ├── config.py       # Application settings & environment variables
    │   └── main.py         # FastAPI entrypoint & SPA static file serving
    ├── tests/              # Pytest test suite (35 tests)
    └── pyproject.toml      # Python dependencies managed with uv
```

---

## 📄 License

MIT License. Open source for amateur sports leagues and tournament organizers.
