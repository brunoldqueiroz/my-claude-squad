---
description: Create optimized Dockerfile for a project
argument-hint: [project path]
agent: container-specialist
---

# Containerize

Create an optimized Dockerfile and related container configuration for a project.

## Usage

```
/containerize [project path]
```

If no path provided, uses current directory.

## Analysis

1. **Detect Project Type**:
   - Python (requirements.txt, pyproject.toml, setup.py)
   - Node.js (package.json)
   - Java (pom.xml, build.gradle)

2. **Identify Dependencies**:
   - Runtime dependencies
   - Build dependencies
   - System libraries needed

3. **Determine Best Practices**:
   - Base image selection
   - Multi-stage build opportunity
   - Caching optimization

## Generated Files

```
project/
├── Dockerfile
├── .dockerignore
└── docker-compose.yml (if applicable)
```

## Dockerfile Features

- **Multi-stage builds**: Separate build and runtime
- **Layer caching**: Dependencies installed first
- **Security**: Non-root user, minimal image
- **Health checks**: Appropriate health check
- **Labels**: Metadata for tracking

## Python Example

```dockerfile
# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
RUN useradd --create-home appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "app.main"]
```

## .dockerignore

Automatically generates appropriate .dockerignore:

```
.git
.gitignore
__pycache__
*.pyc
.venv
.env*
*.md
docs/
tests/
.pytest_cache/
```

## Options

- Optimize for size
- Optimize for build speed
- Include development tools
- Multi-architecture support
