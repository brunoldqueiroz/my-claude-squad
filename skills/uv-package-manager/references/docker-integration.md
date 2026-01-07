# Docker Integration

Best practices for using UV in Docker containers.

## Quick Start Dockerfile

```dockerfile
FROM python:3.12-slim-trixie

# Copy UV binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies (without project code)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy application code
COPY . .

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Run application
CMD ["uv", "run", "python", "-m", "my_app"]
```

## Production-Optimized Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.4
ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.9.22

# ===========================================
# Builder Stage
# ===========================================
FROM python:${PYTHON_VERSION}-slim-trixie AS builder

# Pin UV version for reproducibility
COPY --from=ghcr.io/astral-sh/uv:${UV_VERSION} /uv /uvx /bin/

# Environment settings
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies only (for layer caching)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Copy source and install project
COPY src/ ./src/
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# ===========================================
# Runtime Stage
# ===========================================
FROM python:${PYTHON_VERSION}-slim-trixie AS runtime

# Create non-root user
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home app

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import my_app; print('ok')" || exit 1

# Run application
CMD ["python", "-m", "my_app"]
```

## Multi-Stage Build Patterns

### Pattern 1: Separate Build and Runtime

```dockerfile
# Build stage with UV
FROM ghcr.io/astral-sh/uv:0.9.22 AS uv

FROM python:3.12-slim-trixie AS builder
COPY --from=uv /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Runtime stage (no UV needed)
FROM python:3.12-slim-trixie AS runtime
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "my_app"]
```

### Pattern 2: Include UV in Runtime (for uv run)

```dockerfile
FROM python:3.12-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

COPY src/ ./src/

# Use uv run for command execution
CMD ["uv", "run", "--no-sync", "python", "-m", "my_app"]
```

### Pattern 3: Development Image

```dockerfile
FROM python:3.12-slim-trixie AS dev

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install all dependencies including dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --all-extras

# Source code mounted at runtime
CMD ["uv", "run", "pytest", "--watch"]
```

## Environment Variables

```dockerfile
# Compile Python bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy packages instead of hard linking (required for Docker)
ENV UV_LINK_MODE=copy

# Disable progress bars in CI/Docker
ENV UV_NO_PROGRESS=1

# Use system Python (no virtual environment)
# ENV UV_SYSTEM_PYTHON=1

# Custom cache directory
ENV UV_CACHE_DIR=/tmp/uv-cache

# Project directory (if not using WORKDIR)
ENV UV_PROJECT=/app
```

## Cache Optimization

### Using BuildKit Cache Mounts

```dockerfile
# Recommended: Cache mount for UV cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Multiple cache mounts
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv sync --locked
```

### Layer Caching Strategy

```dockerfile
# 1. Copy only dependency files first
COPY pyproject.toml uv.lock ./

# 2. Install dependencies (cached if deps unchanged)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# 3. Copy source code (changes frequently)
COPY src/ ./src/

# 4. Install project (fast, only project code)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
```

## .dockerignore Configuration

```dockerignore
# Virtual environments (never include)
.venv/
venv/
__pycache__/
*.pyc

# Git
.git/
.gitignore

# IDE
.idea/
.vscode/
*.swp

# Build artifacts
dist/
build/
*.egg-info/

# Tests (for production images)
tests/
pytest.ini
.coverage

# Development files
.env
.env.local
*.md
docs/

# UV cache (use cache mount instead)
.uv_cache/
```

## Docker Compose Examples

### Development Setup

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      # Mount source for live reload
      - ./src:/app/src:cached
      # Preserve venv (don't override with host)
      - /app/.venv
    environment:
      - UV_COMPILE_BYTECODE=0  # Faster in dev
    command: uv run --no-sync pytest --watch

  # Development with file watching
  dev:
    build: .
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: pyproject.toml
```

### Production Setup

```yaml
# docker-compose.prod.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: "3.12"
        UV_VERSION: "0.9.22"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "1"
          memory: 512M
    healthcheck:
      test: ["CMD", "python", "-c", "import my_app"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Common Patterns

### Installing System Dependencies

```dockerfile
FROM python:3.12-slim-trixie

# Install system dependencies before UV
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For psycopg2
    libpq-dev \
    # For scientific packages
    libgomp1 \
    # For SSL
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Continue with UV installation...
```

### Handling Private Packages

```dockerfile
FROM python:3.12-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

# Accept build argument for private index credentials
ARG PRIVATE_INDEX_URL

# Set index URL for private packages
ENV UV_EXTRA_INDEX_URL=${PRIVATE_INDEX_URL}

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=secret,id=pip_credentials,target=/root/.netrc \
    uv sync --locked
```

### Data Science Image

```dockerfile
FROM python:3.12-slim-trixie

# Install data science system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

# Pre-install heavy packages (better layer caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system numpy pandas scikit-learn

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

COPY . .
```

## Troubleshooting

### Issue: Hard link failures

```dockerfile
# Solution: Use copy mode
ENV UV_LINK_MODE=copy
```

### Issue: Slow builds without cache

```dockerfile
# Solution: Enable BuildKit
# DOCKER_BUILDKIT=1 docker build .

# Or in docker-compose
# COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build
```

### Issue: Permission errors with non-root user

```dockerfile
# Solution: Set ownership during copy
COPY --chown=app:app . .

# Or create writable directories
RUN mkdir -p /app/.venv && chown -R app:app /app
USER app
```

### Issue: Old Python version in base image

```dockerfile
# Solution: Use UV to install Python
FROM ubuntu:24.04

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Install specific Python version with UV
RUN uv python install 3.12
ENV PATH="/root/.local/share/uv/python/cpython-3.12.0-linux-x86_64-gnu/bin:$PATH"
```
