---
name: uv-package-manager
description: UV Python package and project manager - an extremely fast pip/poetry replacement written in Rust.
---

# UV Package Manager

## Overview

UV is an extremely fast Python package and project manager written in Rust. It is 10-100x faster than pip and replaces pip, pip-tools, pipx, poetry, pyenv, twine, and virtualenv.

## Quick Reference

### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Homebrew
brew install uv

# pipx
pipx install uv
```

### Essential Commands

| Command | Purpose |
|---------|---------|
| `uv init` | Create new project |
| `uv add <pkg>` | Add dependency |
| `uv remove <pkg>` | Remove dependency |
| `uv sync` | Install all dependencies |
| `uv lock` | Generate/update lockfile |
| `uv run <cmd>` | Run command in project environment |
| `uv python install <ver>` | Install Python version |
| `uv python pin <ver>` | Pin Python version for project |
| `uvx <tool>` | Run tool in ephemeral environment |

## Project Initialization

```bash
# Create new project
uv init my-project
cd my-project

# Create project with specific Python version
uv init my-project --python 3.12

# Initialize in existing directory
uv init

# Initialize as application (no package)
uv init --app

# Initialize as library (with src layout)
uv init --lib
```

### Generated Project Structure

```
my-project/
├── .gitignore
├── .python-version      # Pinned Python version
├── .venv/               # Virtual environment
├── README.md
├── main.py              # For --app
├── src/                 # For --lib
│   └── my_project/
│       └── __init__.py
├── pyproject.toml       # Project configuration
└── uv.lock              # Lockfile (commit this!)
```

## Dependency Management

### Adding Dependencies

```bash
# Add production dependency
uv add requests

# Add with version constraint
uv add 'requests>=2.28,<3'
uv add 'pandas~=2.0'          # Compatible release (~= means >=2.0,<3.0)

# Add multiple packages
uv add requests httpx aiohttp

# Add from git
uv add git+https://github.com/psf/requests
uv add git+https://github.com/user/repo@v1.0.0  # Tag
uv add git+https://github.com/user/repo@main    # Branch

# Add from local path
uv add ./libs/my-lib

# Add with extras
uv add 'pandas[excel,parquet]'

# Import from requirements.txt
uv add -r requirements.txt
```

### Development Dependencies

```bash
# Add to dev group (default development dependency)
uv add --dev pytest pytest-cov ruff mypy

# Add to custom group
uv add --group test pytest hypothesis
uv add --group lint ruff mypy
uv add --group docs mkdocs mkdocs-material

# Sync with dev dependencies (default)
uv sync

# Sync without dev dependencies
uv sync --no-dev

# Sync only specific groups
uv sync --only-group test
uv sync --group lint --group test
```

### Optional Dependencies (Extras)

```bash
# Add as optional dependency
uv add --optional excel openpyxl xlrd
uv add --optional postgres psycopg2-binary

# Install with extras
uv sync --extra excel
uv sync --all-extras
```

### Removing Dependencies

```bash
uv remove requests
uv remove --dev pytest
uv remove --group test hypothesis
```

## Running Commands

```bash
# Run Python script
uv run python script.py

# Run module
uv run python -m pytest

# Run installed tool
uv run pytest
uv run ruff check .

# Run with specific Python version
uv run --python 3.11 python script.py

# Run with extra dependencies
uv run --with httpx python script.py
```

## Python Version Management

```bash
# List available versions
uv python list

# Install specific version
uv python install 3.12
uv python install 3.11 3.10  # Multiple

# Pin version for project (creates .python-version)
uv python pin 3.12

# Find Python installation
uv python find 3.11
```

## Lockfile Management

```bash
# Generate/update lockfile
uv lock

# Update specific package
uv lock --upgrade-package requests

# Update all packages
uv lock --upgrade

# Verify lockfile is up-to-date
uv lock --check
```

## Environment Synchronization

```bash
# Sync environment with lockfile
uv sync

# Sync with all extras
uv sync --all-extras --dev

# Sync and verify lockfile
uv sync --locked

# Sync frozen (no lockfile update)
uv sync --frozen

# Reinstall all packages
uv sync --reinstall
```

## Script Dependencies (PEP 723)

For standalone scripts with inline dependencies:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests<3",
#   "pandas>=2.0",
#   "rich",
# ]
# ///

import requests
import pandas as pd
from rich import print

# Your script code here
```

```bash
# Run script (dependencies auto-installed)
uv run script.py

# Add dependency to script
uv add --script script.py httpx

# Lock script dependencies
uv lock --script script.py
```

## Tool Management

```bash
# Run tool without installing (ephemeral)
uvx ruff check .
uvx black .
uvx mypy src/

# Run specific version
uvx ruff@0.1.0 check .

# Install tool globally
uv tool install ruff
uv tool install 'black[jupyter]'

# List installed tools
uv tool list

# Upgrade tool
uv tool upgrade ruff
uv tool upgrade --all

# Uninstall tool
uv tool uninstall ruff
```

## pip Compatibility Layer

For legacy workflows or migration:

```bash
# Compile requirements
uv pip compile requirements.in -o requirements.txt
uv pip compile pyproject.toml -o requirements.txt

# Sync environment
uv pip sync requirements.txt

# Install packages
uv pip install -r requirements.txt
uv pip install package

# Freeze environment
uv pip freeze > requirements.txt

# Show package info
uv pip show pandas
```

## pyproject.toml Structure

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Project description"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Your Name", email = "you@example.com" }]
dependencies = [
    "requests>=2.28",
    "pandas>=2.0",
]

[project.optional-dependencies]
excel = ["openpyxl>=3.1", "xlrd>=2.0"]
postgres = ["psycopg2-binary>=2.9"]

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.5", "mypy>=1.10"]
test = ["pytest>=8.0", "pytest-cov>=5.0", "hypothesis>=6.100"]
docs = ["mkdocs>=1.6", "mkdocs-material>=9.5"]

[tool.uv]
dev-dependencies = []  # Legacy format (use dependency-groups instead)

[tool.uv.sources]
# Git source
my-lib = { git = "https://github.com/org/my-lib", tag = "v1.0.0" }
# Local path
shared-utils = { path = "../shared-utils", editable = true }
# Workspace member
core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Workspaces (Monorepos)

```toml
# Root pyproject.toml
[tool.uv.workspace]
members = ["packages/*", "libs/*"]
exclude = ["packages/deprecated-*"]
```

```bash
# Lock entire workspace
uv lock

# Sync specific package
uv sync --package my-lib

# Run in specific package
uv run --package my-lib pytest
```

## Cache Management

```bash
# Show cache location
uv cache dir

# Show cache size
uv cache size

# Clear entire cache
uv cache clean

# Clear specific package
uv cache clean requests

# Prune unused entries
uv cache prune

# CI-optimized prune (keeps source-built wheels)
uv cache prune --ci
```

## Common Patterns

### New Data Engineering Project

```bash
# Initialize
uv init data-pipeline --python 3.12
cd data-pipeline

# Add core dependencies
uv add pandas polars sqlalchemy

# Add cloud providers
uv add boto3 snowflake-connector-python

# Add dev tools
uv add --dev pytest pytest-cov ruff mypy
uv add --group test hypothesis faker

# Pin Python version
uv python pin 3.12

# Verify setup
uv run python -c "import pandas; print(pandas.__version__)"
```

### Migrating from requirements.txt

```bash
# Initialize project
uv init

# Import existing requirements
uv add -r requirements.txt
uv add --dev -r requirements-dev.txt

# Generate lockfile
uv lock

# Verify
uv sync --locked
```

### Migrating from Poetry

```bash
# UV reads pyproject.toml directly
# Just run:
uv sync

# If needed, regenerate lockfile
uv lock
```

## Anti-Patterns

### 1. Not Committing uv.lock
- **What it is**: Adding `uv.lock` to `.gitignore`
- **Why it's wrong**: Breaks reproducible builds across environments
- **Correct approach**: Always commit `uv.lock` to version control

### 2. Using pip Inside uv Environment
- **What it is**: Running `pip install` after `uv sync`
- **Why it's wrong**: Creates dependency drift, breaks lockfile integrity
- **Correct approach**: Always use `uv add` for dependencies

### 3. Manually Editing uv.lock
- **What it is**: Hand-editing the lockfile
- **Why it's wrong**: Can create invalid dependency resolution
- **Correct approach**: Use `uv lock --upgrade-package X` for updates

### 4. Ignoring .python-version
- **What it is**: Not pinning Python version
- **Why it's wrong**: Different Python versions across environments
- **Correct approach**: Use `uv python pin X.Y` and commit `.python-version`

### 5. Using --no-lock in CI
- **What it is**: Skipping lockfile verification in CI
- **Why it's wrong**: CI may install different versions than development
- **Correct approach**: Use `uv sync --locked` in CI

---

## Best Practices

1. **Always commit** `uv.lock` and `.python-version`
2. **Use `--locked`** in CI/CD for reproducibility
3. **Organize dependencies** with groups (dev, test, docs)
4. **Pin Python version** per project with `uv python pin`
5. **Use dependency groups** (PEP 735) over legacy `tool.uv.dev-dependencies`
6. **Enable caching** in CI for faster builds
7. **Use `uvx`** for one-off tool execution
8. **Prefer `uv run`** over activating virtual environments

---

## Research Tools

| Tool | Use For |
|------|---------|
| `mcp__upstash-context7-mcp__get-library-docs` | UV configuration options |
| Official docs | https://docs.astral.sh/uv/ |

### Topics to Verify

| Topic | Reason |
|-------|--------|
| Dependency groups | PEP 735 syntax may evolve |
| Workspace configuration | New features added frequently |
| Docker integration | Best practices change |
| CI/CD patterns | New GitHub Action features |
