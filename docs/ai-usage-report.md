# AI Usage & Prompt Engineering Report: Sports League Scoreboard

## 1. Executive Summary

This report documents the end-to-end artificial intelligence (AI) tooling, prompt engineering strategies, agentic workflows, and technical problem-solving used in building the **Sports League Scoreboard** application.

The project was created through a multi-turn human-AI collaborative pair-programming methodology using the **Google Antigravity / Gemini CLI** platform. Over eleven distinct iterations, the AI assistant progressed from product requirements gathering to an end-to-end, production-ready system consisting of:
- A modern **React 19 + TypeScript + Vite + Tailwind CSS** pitchside scorekeeper frontend.
- An **OpenAPI 3.0** contract specification.
- A **FastAPI + SQLAlchemy + uv** backend service with JWT authentication and deterministic tie-breaking standings calculation.
- A multi-stage **Docker** container serving both static assets and API routes on port `8009`.
- Comprehensive **unit/integration test suites** (Vitest and Pytest) and developer tooling (**Makefile**, **AGENTS.md**).

---

## 2. AI Tooling Stack & Capabilities

| Component | Technology / Tool | Role & Utilization |
| :--- | :--- | :--- |
| **Agent Core** | Google Gemini Model Family | Primary reasoning engine, architectural planning, code generation, and diff synthesis |
| **Agent CLI** | Antigravity CLI (`agy`) | Sandboxed execution runtime, workspace state management, persistent terminal lifecycle |
| **Filesystem Tools** | `write_to_file`, `replace_file_content`, `view_file` | Atomic file generation, surgical patching, code inspection |
| **Search & Discovery** | `grep_search`, `find_by_name`, `list_dir` | Structural analysis, dependency inspection, pattern matching |
| **Command Execution** | `run_command` (async/sync) | Automated test execution (`pytest`, `vitest`), linter execution (`ruff`, `oxlint`), Docker compilation |
| **Task Orchestration** | `manage_task`, subagents | Background build monitoring and asynchronous execution |

---

## 3. Chronological Prompt & Iteration Log

### Phase 1: Functional & Technical Specification
* **User Prompt:**
  > *"I want to build a sports league scoreboard web application to manage amateur leagues. Users should be able to create matches, enter live scores, finish matches, and see an automatically calculated league standings table (3 points win, 1 draw, 0 loss). Create a detailed specification and save it to `docs/spec.md`."*
  > *(Followed by `continua` to complete full elaboration)*
* **AI Actions & Methodology:**
  - Researched amateur tournament rules and established deterministic tie-breakers (Points $\rightarrow$ Goal Difference $\rightarrow$ Goals For $\rightarrow$ Head-to-Head $\rightarrow$ Alphabetical).
  - Drafted a 700+ line technical specification covering system architecture, domain models, state transition machines (`SCHEDULED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `FINISHED`), REST API schemas, security requirements, and UI wireframe flows.
* **Deliverables:** [`docs/spec.md`](./spec.md)

---

### Phase 2: Pitchside Frontend with In-Browser Mock Service
* **User Prompt:**
  > *"Create a frontend application in frontend/ based on docs/spec.md. Centralize every backend call in one service layer and create a mock implementation of it with initial sample data so the app runs fully in the browser."*
* **AI Actions & Methodology:**
  - Initialized a React 19 + TypeScript + Vite project with Tailwind CSS v4 and Lucide React icons.
  - Built domain models matching the specification ([`frontend/src/types/index.ts`](../frontend/src/types/index.ts)).
  - Implemented the deterministic standings calculator with unit tests ([`frontend/src/utils/standingsEngine.ts`](../frontend/src/utils/standingsEngine.ts)).
  - Designed an abstract service interface ([`IScoreboardService`](../frontend/src/services/types.ts)) with a fully functioning [`MockScoreboardService`](../frontend/src/services/mockService.ts) utilizing `localStorage` persistence and pre-populated sample league data.
  - Created key UI components: `StandingsTable`, `MatchList`, `PitchsideScorekeeperModal`, and `CreateMatchModal`.
* **Deliverables:** [`frontend/`](../frontend/) directory, Vitest suite (5 unit tests).

---

### Phase 3: Agent Operating Guidelines & Standards
* **User Prompt:**
  > *"Create an AGENTS.md file in the root. For the backend we want to use uv. Also, commit code to git regularly. por ejemplo : for backend, use uv for dependency management. a few useful commands: uv sync, uv add <PACKAGE-NAME>, uv run python <PYTHON-FILE>, regularly commit code to git"*
* **AI Actions & Methodology:**
  - Established operational rules for both AI agents and human contributors.
  - Standardized dependency management around Astral's `uv`.
  - Enforced security rules: binding to `127.0.0.1` locally, non-negative score validations, and strict parameterized database access.
  - Mandated regular Git commits using the Conventional Commits specification.
* **Deliverables:** [`AGENTS.md`](../AGENTS.md)

---

### Phase 4: Git Repository Setup & Remote Synchronization
* **User Prompt:**
  > *"sube a git con un repositorio con el mismo nombre de la carpeta"*
* **AI Actions & Methodology:**
  - Initialized Git repository, verified `.gitignore`, committed initial assets, and linked the remote origin (`sports-league-scoreboard`).
  - Pushed initial milestones to GitHub (`main` branch).
* **Deliverables:** Initialized Git repository and remote tracking.

---

### Phase 5: OpenAPI 3.0 Contract Specification
* **User Prompt:**
  > *"Inspect the mock API in the frontend and docs/spec.md. Create an openapi.yaml file in the root that describes what exactly is expected from the backend... Specify every endpoint, method, path, request body, response body, and which endpoints need authentication."*
* **AI Actions & Methodology:**
  - Audited `MockScoreboardService` and frontend data types to extract the exact REST interface contract.
  - Authored a comprehensive OpenAPI 3.0.3 specification with reusable schemas (`League`, `Team`, `Match`, `StandingRow`, `ScoreUpdatePayload`), JWT Bearer security schemes, and standardized error responses (`ErrorResponse`).
* **Deliverables:** [`openapi.yaml`](../openapi.yaml) (650+ lines).

---

### Phase 6: FastAPI Backend with In-Memory Store & Test Suite
* **User Prompt:**
  > *"Build a FastAPI backend in backend/ that implements the openapi.yaml specs. Use an in-memory store for now. Write tests with pytest... Add authentication with hashed passwords and bearer tokens for the endpoints that need it. Split the code into modules - routers, models, store, auth. Write tests."*
* **AI Actions & Methodology:**
  - Bootstrapped `backend/` with `uv`, declaring dependencies (`fastapi`, `uvicorn`, `pydantic`, `pyjwt`, `bcrypt`).
  - Implemented modular architecture:
    - `app/models/`: Pydantic V2 schemas validating payloads.
    - `app/auth/`: Bcrypt password hashing and JWT token generator/decoder.
    - `app/store/`: Thread-safe in-memory datastore seeded with sample data.
    - `app/routers/`: Auth, Leagues, Teams, Matches, Scorekeeper, Standings, and SSE stream endpoints.
  - Wrote 31 automated tests using `pytest` and `httpx`.
* **Deliverables:** Complete FastAPI backend with 100% test pass rate.

---

### Phase 7: Port Allocation, CORS Middleware & Frontend Integration
* **User Prompt:**
  > *"el puerto 8000 esta ocupado utiliza el puerto 8009 , Switch the frontend to use the real backend client running on port 8009 instead of the mock API. Configure CORS middleware in FastAPI so the frontend can connect without errors."*
* **AI Actions & Methodology:**
  - Reconfigured backend default port to `8009` across documentation, test suites, and launch commands.
  - Added FastAPI `CORSMiddleware` with explicit origin policies and regex support for local Vite development (`http://localhost:5173`, `http://127.0.0.1:5173`, etc.).
  - Implemented [`HttpScoreboardService`](../frontend/src/services/apiService.ts) and switched the frontend service provider to point to the live backend on port `8009`.
  - Added 3 dedicated CORS validation tests in `tests/test_cors.py`.
* **Deliverables:** Active full-stack communication on port `8009`, updated tests (34 total).

---

### Phase 8: Database Migration to SQLAlchemy & SQLite
* **User Prompt:**
  > *"Replace the in-memory store with a database. Use SQLite and SQLAlchemy so it is database-agnostic. Use an environment variable to configure which DB the server should connect to. Make it database-agnostic - later we will add support for other databases (e.g. Postgres)."*
* **AI Actions & Methodology:**
  - Added `sqlalchemy>=2.0` to `pyproject.toml` via `uv`.
  - Designed relational schema models (`LeagueModel`, `TeamModel`, `MatchModel`, `UserModel`) using SQLAlchemy 2.0 mapped columns and foreign keys.
  - Created automatic table migration and idempotent initial data seeding on application startup.
  - Refactored router dependencies to inject database sessions (`get_db`) with parameterized queries.
  - Added database integration tests in `tests/test_database.py` (35 tests total).
* **Deliverables:** [`backend/app/database/`](../backend/app/database/), persistent SQLite storage (`scoreboard.db`).

---

### Phase 9: Multi-Stage Containerization & SPA Serving
* **User Prompt:**
  > *"Create a multi-stage Dockerfile that builds the frontend with Node, builds a Python image with the backend, and serves the frontend static files from FastAPI."*
* **AI Actions & Methodology:**
  - Authored a multi-stage [`Dockerfile`](../Dockerfile):
    - **Stage 1 (`node:22-alpine`)**: Executes `npm ci` and `npm run build` with `VITE_API_URL=/api`.
    - **Stage 2 (`python:3.12-slim`)**: Uses Astral's official `uv` binary to install backend dependencies in `/app/.venv` with `uv sync --frozen --no-dev`, copies built static files to `/app/static`, and runs on port `8009`.
  - Configured FastAPI static file serving in [`backend/app/main.py`](../backend/app/main.py):
    - Mounted `/assets` for bundles.
    - Implemented SPA client-side fallback route (`/{full_path:path}`) while protecting API and Swagger endpoints.
    - Added canonical path traversal validation (`os.path.abspath`) against directory traversal vulnerabilities.
* **Deliverables:** [`Dockerfile`](../Dockerfile), updated [`backend/app/main.py`](../backend/app/main.py).

---

### Phase 10: Docker Dependency Resolution & Optimization
* **Challenge Encountered:**
  - During the Docker build, `uv sync` attempted to build `sqlalchemy-2.0.53` from a source distribution (`.tar.gz`), triggering compilation errors due to missing C/Cython toolchains in minimal slim containers.
  - Host-level `.venv` was initially copied into the container context, causing shebang path mismatches.
* **AI Resolution:**
  - Pinned `sqlalchemy>=2.0.38,<2.0.40` in `pyproject.toml`, enabling instant download of pre-compiled `manylinux_2_17_x86_64.whl` wheels without compilation overhead.
  - Updated [`.dockerignore`](../.dockerignore) with recursive globbing (`**/.venv`, `**/node_modules`, `**/*.db`) to ensure build isolation.
  - Verified container execution by launching and testing `curl` requests against `/`, `/assets`, `/health`, `/api/leagues`, and SPA routes.
* **Deliverables:** Verified production Docker image build and execution.

---

### Phase 11: Developer Tooling, Makefile & Documentation
* **User Prompt:**
  > *"Create a Makefile to run the backend, frontend, tests, and docker container. Create a root README.md explaining how to run everything, and docs/ai-usage-report.md summarizing the AI tools and prompts used."*
* **AI Actions & Methodology:**
  - Created [`Makefile`](../Makefile) with convenient targets for dependency installation, local development, test suites, linting, and Docker lifecycle.
  - Created root [`README.md`](../README.md) with comprehensive architecture, quick start instructions, and reference tables.
  - Authored this [`docs/ai-usage-report.md`](./ai-usage-report.md).
* **Deliverables:** [`Makefile`](../Makefile), [`README.md`](../README.md), [`docs/ai-usage-report.md`](./ai-usage-report.md).

---

## 4. Prompt Engineering Patterns & Insights

### 4.1 Incremental Specification & Contract-First Design
The project benefited significantly from establishing a formal OpenAPI specification before backend development. By having the AI first define `docs/spec.md` and `openapi.yaml`, subsequent code generation prompts for FastAPI routers, Pydantic schemas, and frontend API clients were strictly constrained by the contract, eliminating schema mismatches.

### 4.2 Autonomous Error Diagnosis & Recovery
During Docker image building, the AI encountered a dependency resolution failure (`sqlalchemy 2.0.53` sdist build failure). Rather than requesting user intervention, the AI autonomously:
1. Analyzed the build error log and recognized the absence of pre-compiled wheels for that specific patch version.
2. Formulated a solution by pinning to a version with pre-compiled wheels (`2.0.39`).
3. Re-ran `uv lock`, rebuilt the image, and verified container startup.

### 4.3 Security by Construction
Throughout all generation prompts, the AI enforced defensive coding patterns:
- **Path Traversal Protection**: Verified file boundaries with `os.path.abspath` before serving static files.
- **SQL Injection Prevention**: Relied exclusively on SQLAlchemy ORM queries and parameterized expressions.
- **Authentication**: Salted password hashing with `bcrypt` and stateless JWT verification.
- **Network Safety**: Ensured local development binds strictly to `127.0.0.1` rather than `0.0.0.0`.

---

## 5. Summary of Project Outcomes

- **Lines of Code Generated**: ~4,500 lines across TypeScript, Python, YAML, Markdown, and Dockerfile.
- **Test Coverage**:
  - Backend: 35 tests passing in ~4.8s (Auth, Leagues, Teams, Matches, Scorekeeper, Standings, CORS, Database).
  - Frontend: 5 tests passing in ~0.3s (Standings calculation and tie-breakers).
- **Code Quality**: 0 errors in Ruff and Oxlint.
- **Deployment**: Fully reproducible multi-stage Docker build producing a lightweight container serving both API and frontend SPA.
