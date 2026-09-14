# ==========================================
# Stage 1: Build Frontend Assets with Node
# ==========================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies using package-lock.json
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build production assets with relative /api endpoint
ENV VITE_API_URL=/api
RUN npm run build

# ==========================================
# Stage 2: Python Backend with FastAPI & uv
# ==========================================
FROM python:3.12-slim AS runner

# Install Astral uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    STATIC_DIR=/app/static \
    DATABASE_URL=sqlite:///./scoreboard.db \
    PORT=8009 \
    HOST=0.0.0.0 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy dependency specifications for layer caching
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./

# Install production dependencies with uv
RUN uv sync --frozen --no-dev --no-cache

# Copy backend application source
COPY backend/app/ ./app/
COPY backend/main.py ./main.py

# Copy built frontend static files from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/static

# Container runs on port 8009
EXPOSE 8009

# Launch FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8009"]
