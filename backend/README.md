# Sports League Scoreboard - FastAPI Backend

FastAPI backend service for the Sports League Scoreboard application, implemented according to the `openapi.yaml` specification.

## Architecture

The codebase is organized into clean, focused modules:

```
backend/
├── app/
│   ├── auth/           # Password hashing (bcrypt), JWT tokens, and RBAC dependencies
│   ├── models/         # Pydantic domain models & DTOs matching openapi.yaml
│   ├── store/          # In-memory store with sample seed data & standings engine
│   ├── routers/        # API route handlers (auth, leagues, teams, matches, scorekeeper, standings, stream, dev)
│   ├── config.py       # Configuration & secure environment resolution
│   └── main.py         # FastAPI application & CORS configuration
├── tests/              # Comprehensive test suite with pytest
├── pyproject.toml      # uv dependency & project definition
└── main.py             # Uvicorn entry point
```

## Seed Credentials

The backend comes pre-seeded with sample users for testing authentication and role-based access control:

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `AdminPassword123!` | Full control: create leagues, add teams, schedule matches, dev reset |
| **Scorekeeper** | `scorekeeper` | `RefereePassword123!` | Pitchside operations: start matches, live scoring, finish matches |
| **Viewer / Public** | *None* | *None* | Read-only access to standings, fixtures, live scores, and SSE stream |

## Quickstart with `uv`

### 1. Sync Dependencies
```bash
uv sync
```

### 2. Run the Development Server
```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- **API Base**: `http://127.0.0.1:8000/api`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

### 3. Run Test Suite
```bash
uv run pytest
```
