# Dual-Environment Infrastructure Architecture & Operations Manual

This document details the configuration, isolation architecture, and operational procedures for the dual-environment deployment of the **Sports League Scoreboard**.

---

## 1. Architecture Overview

The system maintains two completely independent infrastructure stacks running concurrently on the same host:
1. **Development Environment (`dev`)**: Uses the existing infrastructure setup for active feature development, testing, and schema prototyping.
2. **Production Environment (`prod`)**: A second, hardened, fully independent copy of the infrastructure dedicated to live scorekeeping, stable tournament standings, and production releases.

```
                      Host Machine (Linux)
+---------------------------------------------------------------+
|                                                               |
|  [ Development Environment ]         [ Production Environment]|
|                                                               |
|  Port 8009                           Port 8010                |
|  +-----------------------+           +-----------------------+|
|  |  scoreboard-app       |           |  scoreboard-prod-app  ||
|  |  FastAPI + React SPA  |           |  FastAPI + React SPA  ||
|  +-----------+-----------+           +-----------+-----------+|
|              |                                   |            |
|       Internal Bridge                     Internal Bridge     |
|   (sports-league-scoreboard)            (scoreboard-prod-net) |
|              |                                   |            |
|  +-----------v-----------+           +-----------v-----------+|
|  |  scoreboard-db        |           |  scoreboard-prod-db   ||
|  |  PostgreSQL 16        |           |  PostgreSQL 16        ||
|  |  Port 5434            |           |  Port 5435            ||
|  +-----------+-----------+           +-----------+-----------+|
|              |                                   |            |
|  Volume: scoreboard-pgdata           Volume: scoreboard-prod- |
|                                              pgdata           |
+---------------------------------------------------------------+
```

---

## 2. Infrastructure Comparison Matrix

| Property | Development Environment (`dev`) | Production Environment (`prod`) |
| :--- | :--- | :--- |
| **Compose File** | `docker-compose.yaml` / `docker-compose.dev.yaml` | `docker-compose.prod.yaml` |
| **Compose Project Name** | `sports-league-scoreboard` | `scoreboard-prod` |
| **App Container Name** | `scoreboard-app` | `scoreboard-prod-app` |
| **App Image** | `sports-scoreboard:latest` | `sports-scoreboard:prod` |
| **App Host Port** | `8009` (`http://localhost:8009`) | `8010` (`http://localhost:8010`) |
| **PostgreSQL Container Name** | `scoreboard-db` | `scoreboard-prod-db` |
| **PostgreSQL Host Port** | `5434` (`localhost:5434`) | `5435` (`localhost:5435`) |
| **PostgreSQL Database Name** | `sdip` | `scoreboard_prod` |
| **PostgreSQL Username** | `sdip` | `scoreboard_prod_user` |
| **Persistent Volume** | `scoreboard-pgdata` | `scoreboard-prod-pgdata` |
| **Docker Network** | `sports-league-scoreboard_default` | `scoreboard-prod-network` |
| **JWT Signing Secret** | Dev Secret (`.env.dev`) | Production Cryptographic Secret (`.env.prod`) |
| **Environment Variable File** | `.env.dev` / `.env.dev.example` | `.env.prod` / `.env.prod.example` |
| **Container Restart Policy** | `unless-stopped` | `unless-stopped` |
| **Health Check Strategy** | Postgres `pg_isready` | Postgres `pg_isready` + App HTTP `/health` |

---

## 3. Strict Isolation Guarantees

1. **Storage Isolation**:
   - Production data is stored in the Docker volume `scoreboard-prod-pgdata`.
   - Development data is stored in `scoreboard-pgdata`.
   - Running test suites, data resets (`POST /api/dev/reset`), or database wipes on dev will never touch production records.
2. **Network Isolation**:
   - The production containers run on the isolated bridge network `scoreboard-prod-network`.
   - Development containers run on `sports-league-scoreboard_default`.
   - Neither application container can access the opposing environment's PostgreSQL server.
3. **Port Isolation**:
   - Dev binds to host ports `8009` (HTTP API & Frontend) and `5434` (PostgreSQL).
   - Prod binds to host ports `8010` (HTTP API & Frontend) and `5435` (PostgreSQL).
   - Both can run concurrently on a single host without port conflicts.
4. **Security & Credential Isolation**:
   - Different database usernames, passwords, and database names are used.
   - JWT authentication tokens minted in dev are rejected by production due to separate signing secrets.

---

## 4. Management & Operations Commands

### Production Operations

```bash
# Start production stack in background
make compose-up-prod
# Direct: docker compose -f docker-compose.prod.yaml --env-file .env.prod up -d --build

# View production status
make compose-ps-prod

# Follow production logs
make compose-logs-prod

# Run health check & API integration tests against production
make test-prod

# Stop production stack
make compose-down-prod
```

### Development Operations

```bash
# Start development stack in background
make compose-up
# Direct: docker compose up -d --build

# View dev status
make compose-ps-dev

# Follow dev logs
make compose-logs-dev

# Stop development stack
make compose-down
```

---

## 5. Automated Verification & Testing

The repository provides automated verification covering both environments:
- **Backend API Integration Tests (`tests/test_api.py`)**: Tests all CRUD and standings endpoints against any target environment via `API_BASE_URL`.
- **Environment Isolation Tests (`tests/test_environment_isolation.py`)**: Verifies health of both environments simultaneously, checks JWT signature rejection across boundaries, and confirms data mutations in dev do not affect prod.
- **End-to-End Browser Tests (`tests/e2e/test_scoreboard.spec.ts`)**: Runs Playwright user journeys against dev (`:8009`) or prod (`:8010`).

---

## 6. Production Promotion Lifecycle

Promoting a development release to production is managed through two automated pathways:

### 1. Manual GitHub Actions Promotion Workflow (`promote-to-production.yml`)
Located at `.github/workflows/promote-to-production.yml`, this workflow provides a controlled promotion gate triggered via `workflow_dispatch`:

- **Inputs**:
  - `source_ref`: Branch, tag, or commit SHA from dev to promote (default: `main`).
  - `release_version`: Semantic release tag (e.g. `v1.2.0`; auto-generated if left blank).
  - `run_tests`: Boolean flag to run backend Pytest, frontend Vitest, linters, and build prior to promotion.
  - `run_e2e`: Boolean flag to run Playwright browser tests against the live production deployment.
  - `dry_run`: Boolean flag to validate configuration and build images without modifying production.
  - `promotion_notes`: Audit changelog summary stored in GitHub Step Summary.
- **Lifecycle**:
  1. **Pre-flight Gate**: Executes backend and frontend test suites and linters.
  2. **Image Baking**: Builds multi-stage release image tagged as `sports-scoreboard:${version}` and `sports-scoreboard:prod`.
  3. **Stack Deployment**: Executes `docker compose -f docker-compose.prod.yaml --env-file .env.prod up -d --build`.
  4. **Post-Deployment Gate**: Polls `/health` on port 8010, runs backend API integration tests, and executes Playwright E2E browser tests.
  5. **Audit Logging**: Emits structured deployment report to `$GITHUB_STEP_SUMMARY`.

### 2. Local Promotion Command
```bash
make promote-to-prod
```
Executes pre-promotion unit tests, triggers the production Docker Compose build and startup, and runs integration verification tests against `http://localhost:8010`.

