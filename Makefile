# ==============================================================================
# Sports League Scoreboard - Makefile
# ==============================================================================

SHELL := /usr/bin/env bash

# Application settings
BACKEND_DIR  := backend
FRONTEND_DIR := frontend
BACKEND_PORT := 8009
FRONTEND_PORT:= 5173
IMAGE_NAME   := sports-scoreboard
CONTAINER_NAME := scoreboard-app
POSTGRES_CONTAINER := scoreboard-db
POSTGRES_PORT := 5434
POSTGRES_USER := sdip
POSTGRES_PASSWORD := sdip
POSTGRES_DB   := sdip
POSTGRES_VOLUME := scoreboard-pgdata

# Production Infrastructure settings (second, independent environment)
PROD_PORT          := 8010
PROD_CONTAINER_NAME:= scoreboard-prod-app
PROD_IMAGE_NAME    := sports-scoreboard:prod
PROD_POSTGRES_CONTAINER := scoreboard-prod-db
PROD_POSTGRES_PORT := 5435
PROD_POSTGRES_USER := scoreboard_prod_user
PROD_POSTGRES_PASSWORD := scoreboard_prod_secure_password_2026!
PROD_POSTGRES_DB   := scoreboard_prod
PROD_POSTGRES_VOLUME := scoreboard-prod-pgdata

.PHONY: help install install-backend install-frontend \
        run run-backend run-frontend dev \
        test test-backend test-frontend e2e \
        lint lint-backend lint-frontend \
        build-frontend build-docker run-docker stop-docker \
        run-postgres stop-postgres compose-up compose-down clean \
        compose-up-prod compose-down-prod compose-logs-prod compose-ps-prod \
        compose-up-dev compose-down-dev compose-logs-dev compose-ps-dev \
        prod-up prod-down dev-up dev-down test-prod promote-to-prod

# Default target: list commands
help:
	@echo "=============================================================================="
	@echo " Sports League Scoreboard - Command Menu"
	@echo "=============================================================================="
	@echo " Installation:"
	@echo "   make install             Install dependencies for both backend and frontend"
	@echo "   make install-backend     Install backend dependencies with uv"
	@echo "   make install-frontend    Install frontend dependencies with npm"
	@echo ""
	@echo " Development:"
	@echo "   make run-backend         Start FastAPI backend server (http://127.0.0.1:$(BACKEND_PORT))"
	@echo "   make run-frontend        Start Vite frontend dev server (http://127.0.0.1:$(FRONTEND_PORT))"
	@echo "   make dev                 Run backend and frontend concurrently"
	@echo ""
	@echo " Testing & Linting:"
	@echo "   make test                Run all backend (pytest) and frontend (vitest) tests"
	@echo "   make test-backend        Run pytest backend tests"
	@echo "   make test-frontend       Run vitest frontend tests"
	@echo "   make e2e                 Run integration (pytest) and Playwright E2E tests"
	@echo "   make lint                Run ruff linting (backend) and oxlint (frontend)"
	@echo "   make lint-backend        Run ruff on backend"
	@echo "   make lint-frontend       Run oxlint and tsc typecheck on frontend"
	@echo ""
	@echo " Development Infrastructure (Docker Compose - Port $(BACKEND_PORT)):"
	@echo "   make compose-up          Launch dev stack (App :$(BACKEND_PORT) + Postgres :$(POSTGRES_PORT))"
	@echo "   make compose-down        Tear down dev stack"
	@echo "   make compose-logs-dev    Follow logs for dev stack"
	@echo "   make compose-ps-dev      Status of dev stack containers"
	@echo ""
	@echo " Production Infrastructure (Second Independent Stack - Port $(PROD_PORT)):"
	@echo "   make compose-up-prod     Launch isolated production stack (App :$(PROD_PORT) + Postgres :$(PROD_POSTGRES_PORT))"
	@echo "   make compose-down-prod   Tear down production stack"
	@echo "   make compose-logs-prod   Follow logs for production stack"
	@echo "   make compose-ps-prod     Status of production stack containers"
	@echo "   make test-prod           Run health and API checks against production"
	@echo "   make promote-to-prod     Promote dev to production with automated tests & deployment"
	@echo ""
	@echo " Standalone Containers:"
	@echo "   make build-frontend      Compile frontend production assets to dist/"
	@echo "   make build-docker        Build the multi-stage Docker image"
	@echo "   make run-docker          Run the Docker container on port $(BACKEND_PORT)"
	@echo "   make stop-docker         Stop and remove the running Docker container"
	@echo "   make run-postgres        Start PostgreSQL container on port $(POSTGRES_PORT)"
	@echo "   make stop-postgres       Stop PostgreSQL container"
	@echo ""
	@echo " Housekeeping:"
	@echo "   make clean               Clean build artifacts, test caches, and db files"
	@echo "=============================================================================="

# ==============================================================================
# Dependency Installation
# ==============================================================================
install: install-backend install-frontend

install-backend:
	@echo "--> Installing backend dependencies with uv..."
	@cd $(BACKEND_DIR) && uv sync

install-frontend:
	@echo "--> Installing frontend dependencies with npm..."
	@cd $(FRONTEND_DIR) && npm ci

# ==============================================================================
# Local Development Execution
# ==============================================================================
run: run-backend

run-backend:
	@echo "--> Starting FastAPI server on http://127.0.0.1:$(BACKEND_PORT)..."
	@cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port $(BACKEND_PORT)

run-frontend:
	@echo "--> Starting Vite dev server on http://127.0.0.1:$(FRONTEND_PORT)..."
	@cd $(FRONTEND_DIR) && npm run dev

dev:
	@echo "--> Starting backend and frontend in parallel..."
	@trap 'kill 0' SIGINT SIGTERM EXIT; \
	(cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port $(BACKEND_PORT)) & \
	(cd $(FRONTEND_DIR) && npm run dev) & \
	wait

# ==============================================================================
# Testing
# ==============================================================================
test: test-backend test-frontend

test-backend:
	@echo "--> Running backend test suite with pytest..."
	@cd $(BACKEND_DIR) && uv run pytest

test-frontend:
	@echo "--> Running frontend test suite with vitest..."
	@cd $(FRONTEND_DIR) && npm run test

e2e:
	@echo "--> Running backend tests..."
	@uv run --project backend pytest tests/ -v || pytest tests/ -v
	@echo "--> Running Playwright E2E against running compose stack..."
	@npx playwright test

# ==============================================================================
# Linting & Code Quality
# ==============================================================================
lint: lint-backend lint-frontend

lint-backend:
	@echo "--> Checking backend code with ruff..."
	@cd $(BACKEND_DIR) && uv run ruff check

lint-frontend:
	@echo "--> Checking frontend code with oxlint and typecheck..."
	@cd $(FRONTEND_DIR) && npm run lint && npx tsc --noEmit

# ==============================================================================
# Production Build & Containerization
# ==============================================================================
build-frontend:
	@echo "--> Building frontend production bundle with Vite..."
	@cd $(FRONTEND_DIR) && npm run build

build-docker:
	@echo "--> Building multi-stage Docker image '$(IMAGE_NAME):latest'..."
	@docker build -t $(IMAGE_NAME):latest .

run-docker:
	@echo "--> Starting Docker container '$(CONTAINER_NAME)' on port $(BACKEND_PORT)..."
	@docker run -d --name $(CONTAINER_NAME) -p $(BACKEND_PORT):$(BACKEND_PORT) $(IMAGE_NAME):latest
	@echo "App is now live at http://127.0.0.1:$(BACKEND_PORT)"

stop-docker:
	@echo "--> Stopping and removing Docker container '$(CONTAINER_NAME)'..."
	@-docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@-docker rm $(CONTAINER_NAME) 2>/dev/null || true

run-postgres:
	@echo "--> Starting PostgreSQL container '$(POSTGRES_CONTAINER)' on port $(POSTGRES_PORT)..."
	@docker run -d \
		--name $(POSTGRES_CONTAINER) \
		-e POSTGRES_USER=$(POSTGRES_USER) \
		-e POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		-e POSTGRES_DB=$(POSTGRES_DB) \
		-p $(POSTGRES_PORT):5432 \
		-v $(POSTGRES_VOLUME):/var/lib/postgresql/data \
		postgres:16-alpine
	@echo "PostgreSQL is now live at localhost:$(POSTGRES_PORT) (user: $(POSTGRES_USER), db: $(POSTGRES_DB))"

stop-postgres:
	@echo "--> Stopping and removing PostgreSQL container '$(POSTGRES_CONTAINER)'..."
	@-docker stop $(POSTGRES_CONTAINER) 2>/dev/null || true
	@-docker rm $(POSTGRES_CONTAINER) 2>/dev/null || true

# Development Stack Orchestration
compose-up:
	@echo "--> Launching development stack with Docker Compose..."
	@docker compose up -d --build
	@echo "Dev App is live at http://127.0.0.1:$(BACKEND_PORT)"

compose-down:
	@echo "--> Stopping development Docker Compose stack..."
	@docker compose down

compose-up-dev: compose-up
compose-down-dev: compose-down
dev-up: compose-up
dev-down: compose-down

compose-logs-dev:
	@docker compose logs -f

compose-ps-dev:
	@docker compose ps

dev-logs: compose-logs-dev
dev-ps: compose-ps-dev

# Production Stack Orchestration (Second Independent Copy)
compose-up-prod:
	@echo "--> Launching production stack with Docker Compose (docker-compose.prod.yaml)..."
	@docker compose -f docker-compose.prod.yaml --env-file .env.prod up -d --build
	@echo "Production App is live at http://127.0.0.1:$(PROD_PORT)"

compose-down-prod:
	@echo "--> Stopping production Docker Compose stack..."
	@docker compose -f docker-compose.prod.yaml --env-file .env.prod down

prod-up: compose-up-prod
prod-down: compose-down-prod

compose-logs-prod:
	@docker compose -f docker-compose.prod.yaml --env-file .env.prod logs -f

compose-ps-prod:
	@docker compose -f docker-compose.prod.yaml --env-file .env.prod ps

prod-logs: compose-logs-prod
prod-ps: compose-ps-prod

test-prod:
	@echo "--> Testing production health endpoint at http://127.0.0.1:$(PROD_PORT)/health..."
	@timeout 30s bash -c 'until curl -sf http://127.0.0.1:$(PROD_PORT)/health | grep -q "healthy"; do sleep 1; done'
	@echo "✅ Production healthcheck PASSED"
	@echo "--> Running integration test suite against production endpoint..."
	@API_BASE_URL=http://localhost:$(PROD_PORT) uv run --project backend pytest tests/test_api.py -v

promote-to-prod:
	@echo "--> Initiating promotion from dev to production..."
	@DEV_IMG=$$(docker inspect scoreboard-app --format '{{.Config.Image}}' 2>/dev/null || cat .current-dev-image 2>/dev/null || echo "sports-scoreboard:latest"); \
	echo "1. Detected image currently running in dev: $$DEV_IMG"; \
	echo "2. Deploying that exact image to the production container (scoreboard-prod-app)..."; \
	PROD_APP_IMAGE="$$DEV_IMG" docker compose -f docker-compose.prod.yaml --env-file .env.prod up -d --no-deps app; \
	echo "$$DEV_IMG" > .current-prod-image; \
	echo "$${DEV_IMG##*:}" > .current-prod-tag
	@echo "3. Running verification tests against production..."
	@$(MAKE) test-prod
	@echo "--> Promotion complete! Production is live and verified at http://127.0.0.1:$(PROD_PORT)"





# ==============================================================================
# Cleanup
# ==============================================================================
clean:
	@echo "--> Cleaning up build artifacts, caches, and test files..."
	@rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/node_modules/.vite
	@find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean completed."
