# AGENTS.md - Agent Operating Guidelines & Standards

This document sets the operational standards, workflows, and developer conventions for AI agents and human contributors working on the **Sports League Scoreboard** repository.

---

## 1. Project Overview & Directory Structure

```
sports-league-scoreboard/
├── AGENTS.md           # Instructions & rules for AI coding agents
├── docs/               # System architecture, schemas, and specifications (docs/spec.md)
├── frontend/           # React + TypeScript + Vite + Tailwind CSS web application
│   ├── src/
│   │   ├── components/ # UI components (Scorekeeper, Standings, Matches, Teams)
│   │   ├── services/   # Centralized backend & mock service layer (IScoreboardService)
│   │   ├── types/      # Domain models (League, Team, Match, Standings)
│   │   └── utils/      # Standings calculation engine & tie-breakers
│   └── package.json
└── backend/            # Python backend service (managed with uv)
```

---

## 2. Git & Version Control Protocol

### 2.1 Regular Commit Requirement
- **Commit code regularly**: Make focused, incremental Git commits after completing each logical milestone (e.g., adding a feature, creating tests, updating documentation, or refactoring).
- **Atomic Commits**: Group related changes together; do not leave large accumulations of uncommitted work.
- **Conventional Commits**: Use descriptive commit messages following conventional guidelines:
  - `feat:` New feature or capability
  - `fix:` Bug fix or correction
  - `docs:` Documentation updates or specifications
  - `test:` Adding or updating tests
  - `refactor:` Code refactoring without changing behavior
  - `chore:` Dependency, build, or configuration updates

### 2.2 Git Hygiene
- Ensure `.gitignore` is respected. Never commit:
  - Virtual environments (`.venv/`)
  - Node modules (`node_modules/`)
  - Build outputs (`dist/`, `build/`)
  - Environment variables or secrets (`.env`, `*.local`)
  - Cache files (`__pycache__/`, `.pytest_cache/`)

---

## 3. Backend Development & Dependency Management (`uv`)

For the backend, **`uv`** is the required tool for Python packaging, dependency management, and virtual environment execution.

### 3.1 Essential `uv` Commands

| Purpose | Command |
| :--- | :--- |
| **Sync Environment** | `uv sync` |
| **Add Dependency** | `uv add <PACKAGE-NAME>` |
| **Add Dev Dependency** | `uv add --dev <PACKAGE-NAME>` |
| **Remove Dependency** | `uv remove <PACKAGE-NAME>` |
| **Run Python Script** | `uv run python <PYTHON-FILE>` |
| **Run Application Server** | `uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000` |
| **Run Test Suite** | `uv run pytest` |
| **Code Formatting & Linting** | `uv run ruff check` / `uv run ruff format` |

### 3.2 Backend Standards
- **Local Network Safety**: Servers must bind exclusively to `127.0.0.1` or `localhost` during testing and development. Never bind to `0.0.0.0`.
- **Validation**: Enforce request validation with Pydantic or schema libraries. Ensure non-negative integers for scores.
- **Database Access**: Always use parameterized queries or ORM models. Never concatenate user input into raw SQL queries.

---

## 4. Frontend Standards & Service Layer

- **Centralized Service Layer**: All API communication must pass through the `IScoreboardService` abstraction defined in `frontend/src/services/types.ts`.
- **In-Browser Mock Support**: Maintain the `MockScoreboardService` with sample data and `localStorage` persistence so the application can always run standalone in the browser without requiring a live backend.
- **Standings Engine Rule**: Standings calculation must strictly follow the standard amateur 3-1-0 points system (3 for win, 1 for draw, 0 for loss) with deterministic tie-breakers (PTS > GD > GF > Head-to-Head > Team Name).
- **UI Security**:
  - Use framework-native React JSX escaping.
  - Prohibit `dangerouslySetInnerHTML` and direct `innerHTML` manipulations.
  - Always validate match inputs (prevent a team from playing against itself).

---

## 5. Agent Workflow Checklist

Before concluding any work session, agents must verify:
1. All newly written code builds cleanly (`npm run build`, `uv sync`).
2. Unit and integration tests pass (`npx vitest run`, `uv run pytest`).
3. Changes are committed to Git with clear, informative commit messages.
