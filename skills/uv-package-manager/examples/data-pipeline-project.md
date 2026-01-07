# Example: Data Pipeline Project Setup

Complete example of setting up a data engineering project with UV.

## Project Initialization

```bash
# Create project
uv init data-pipeline --python 3.12
cd data-pipeline

# Verify structure
ls -la
# .gitignore
# .python-version
# README.md
# main.py
# pyproject.toml
```

## pyproject.toml Configuration

```toml
[project]
name = "data-pipeline"
version = "0.1.0"
description = "ETL pipeline for customer data processing"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Your Name", email = "you@example.com" }]

dependencies = [
    "pandas>=2.0",
    "polars>=0.20",
    "sqlalchemy>=2.0",
    "pydantic>=2.5",
    "structlog>=24.1",
    "tenacity>=8.2",
]

[project.optional-dependencies]
snowflake = [
    "snowflake-connector-python>=3.6",
    "snowflake-sqlalchemy>=1.5",
]
postgres = [
    "psycopg2-binary>=2.9",
]
aws = [
    "boto3>=1.34",
]
all = [
    "data-pipeline[snowflake,postgres,aws]",
]

[project.scripts]
etl-run = "data_pipeline.cli:main"
etl-validate = "data_pipeline.validate:validate"

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "mypy>=1.10",
    "pre-commit>=3.7",
    { include-group = "test" },
]
test = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-xdist>=3.5",
    "hypothesis>=6.100",
    "faker>=24.0",
    "responses>=0.25",
]
lint = [
    "ruff>=0.5",
    "mypy>=1.10",
    "types-requests>=2.31",
    "pandas-stubs>=2.0",
]

[tool.uv]
default-groups = ["dev"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-ra", "-q", "--cov=src/data_pipeline"]
```

## Install Dependencies

```bash
# Install core + dev dependencies
uv sync

# Install with Snowflake support
uv sync --extra snowflake

# Install everything
uv sync --all-extras --dev

# Production install (no dev)
uv sync --no-dev --extra snowflake
```

## Project Structure

```bash
# Create src layout
mkdir -p src/data_pipeline tests

# Create package structure
touch src/data_pipeline/__init__.py
touch src/data_pipeline/cli.py
touch src/data_pipeline/extract.py
touch src/data_pipeline/transform.py
touch src/data_pipeline/load.py
touch src/data_pipeline/validate.py

# Create test structure
touch tests/__init__.py
touch tests/conftest.py
touch tests/test_extract.py
touch tests/test_transform.py
```

## Source Code Examples

### src/data_pipeline/__init__.py

```python
"""Data Pipeline - ETL for customer data processing."""

from data_pipeline.extract import extract_from_source
from data_pipeline.transform import transform_data
from data_pipeline.load import load_to_target

__all__ = ["extract_from_source", "transform_data", "load_to_target"]
__version__ = "0.1.0"
```

### src/data_pipeline/cli.py

```python
"""Command-line interface for the data pipeline."""

from __future__ import annotations

import argparse
import structlog

from data_pipeline import extract_from_source, transform_data, load_to_target

logger = structlog.get_logger()


def main() -> int:
    """Run the ETL pipeline."""
    parser = argparse.ArgumentParser(description="Run ETL pipeline")
    parser.add_argument("--source", required=True, help="Source connection string")
    parser.add_argument("--target", required=True, help="Target connection string")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to target")
    args = parser.parse_args()

    logger.info("starting_pipeline", source=args.source, target=args.target)

    try:
        data = extract_from_source(args.source)
        transformed = transform_data(data)

        if not args.dry_run:
            load_to_target(transformed, args.target)

        logger.info("pipeline_complete", rows=len(transformed))
        return 0

    except Exception as e:
        logger.error("pipeline_failed", error=str(e))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

### tests/conftest.py

```python
"""Pytest fixtures for data pipeline tests."""

from __future__ import annotations

import pytest
import pandas as pd
from faker import Faker

fake = Faker()


@pytest.fixture
def sample_customers() -> pd.DataFrame:
    """Generate sample customer data."""
    return pd.DataFrame({
        "customer_id": range(1, 101),
        "name": [fake.name() for _ in range(100)],
        "email": [fake.email() for _ in range(100)],
        "created_at": [fake.date_this_year() for _ in range(100)],
    })


@pytest.fixture
def sample_orders(sample_customers: pd.DataFrame) -> pd.DataFrame:
    """Generate sample order data."""
    return pd.DataFrame({
        "order_id": range(1, 501),
        "customer_id": [fake.random_element(sample_customers["customer_id"]) for _ in range(500)],
        "amount": [round(fake.random.uniform(10, 500), 2) for _ in range(500)],
        "order_date": [fake.date_this_year() for _ in range(500)],
    })
```

## Running the Project

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov --cov-report=html

# Run linter
uv run ruff check src/ tests/

# Run type checker
uv run mypy src/

# Run the CLI
uv run etl-run --source "postgres://..." --target "snowflake://..." --dry-run

# Run specific script
uv run python scripts/one_off_migration.py
```

## Development Workflow

```bash
# Add new dependency
uv add httpx

# Add dev dependency
uv add --dev pytest-asyncio

# Update specific package
uv lock --upgrade-package pandas

# Update all packages
uv lock --upgrade

# Check for issues
uv run ruff check .
uv run mypy src/

# Format code
uv run ruff format .
```

## Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types: [python]

      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix
        language: system
        types: [python]

      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        types: [python]
        pass_filenames: false
        args: [src/]
```

```bash
# Install pre-commit hooks
uv run pre-commit install
```

## Docker Integration

```dockerfile
# Dockerfile
FROM python:3.12-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra snowflake --no-install-project

COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra snowflake

CMD ["uv", "run", "etl-run", "--help"]
```

## GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          version: "0.9.22"
          enable-cache: true

      - run: uv python install 3.12
      - run: uv sync --locked --all-extras --dev
      - run: uv run pytest --cov
      - run: uv run ruff check .
      - run: uv run mypy src/
```
