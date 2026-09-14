# ==============================================================================
# Sports League Scoreboard - Makefile
# ==============================================================================

SHELL := /usr/bin/env bash

# Application settings
BACKEND_DIR  := backend
FRONTEND_DIR := frontend
BACKEND_PORT := 8009
FRONTEND_PORT:= 5173
IMAGE_NAME   := sports-league-scoreboard
CONTAINER_NAME := scoreboard-app

.PHONY: help install install-backend install-frontend \
        run-backend run-frontend dev \
        test test-backend test-frontend \
        lint lint-backend lint-frontend \
        build-frontend build-docker run-docker stop-docker clean

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
	@echo "   make lint                Run ruff linting (backend) and oxlint (frontend)"
	@echo "   make lint-backend        Run ruff on backend"
	@echo "   make lint-frontend       Run oxlint and tsc typecheck on frontend"
	@echo ""
	@echo " Docker & Production:"
	@echo "   make build-frontend      Compile frontend production assets to dist/"
	@echo "   make build-docker        Build the multi-stage Docker image"
	@echo "   make run-docker          Run the Docker container on port $(BACKEND_PORT)"
	@echo "   make stop-docker         Stop and remove the running Docker container"
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
