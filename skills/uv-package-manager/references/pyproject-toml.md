# pyproject.toml Configuration Reference

Complete reference for UV's pyproject.toml configuration.

## Full Example

```toml
[project]
name = "my-data-pipeline"
version = "1.0.0"
description = "ETL pipeline for customer data processing"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "you@example.com" },
]
maintainers = [
    { name = "Team Lead", email = "lead@example.com" },
]
keywords = ["etl", "data", "pipeline"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

# Production dependencies
dependencies = [
    "pandas>=2.0,<3",
    "polars>=0.20",
    "sqlalchemy>=2.0",
    "boto3>=1.34",
    "pydantic>=2.5",
    "structlog>=24.1",
]

[project.optional-dependencies]
# Install with: uv sync --extra snowflake
snowflake = [
    "snowflake-connector-python>=3.6",
    "snowflake-sqlalchemy>=1.5",
]
# Install with: uv sync --extra postgres
postgres = [
    "psycopg2-binary>=2.9",
]
# Install with: uv sync --extra all
all = [
    "my-data-pipeline[snowflake,postgres]",
]

[project.scripts]
# CLI entry points: uv run my-pipeline
my-pipeline = "my_data_pipeline.cli:main"
my-validate = "my_data_pipeline.validate:main"

[project.urls]
Homepage = "https://github.com/org/my-data-pipeline"
Documentation = "https://org.github.io/my-data-pipeline"
Repository = "https://github.com/org/my-data-pipeline.git"
Changelog = "https://github.com/org/my-data-pipeline/blob/main/CHANGELOG.md"

# ============================================
# Dependency Groups (PEP 735) - Preferred
# ============================================

[dependency-groups]
# Default dev group: uv sync (includes by default)
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "mypy>=1.10",
    "pre-commit>=3.7",
    # Include other groups
    { include-group = "test" },
]

# Test group: uv sync --group test
test = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-xdist>=3.5",
    "hypothesis>=6.100",
    "faker>=24.0",
    "responses>=0.25",
]

# Lint group: uv sync --group lint
lint = [
    "ruff>=0.5",
    "mypy>=1.10",
    "types-requests>=2.31",
]

# Docs group: uv sync --group docs
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.25",
]

# ============================================
# UV Configuration
# ============================================

[tool.uv]
# Change default groups (instead of just dev)
default-groups = ["dev", "test"]

# Legacy dev dependencies (prefer dependency-groups)
# dev-dependencies = []

# Package mode (default: true for libraries, false for apps)
# package = false

[tool.uv.sources]
# Git source with tag
shared-utils = { git = "https://github.com/org/shared-utils", tag = "v2.0.0" }

# Git source with branch
experimental-lib = { git = "https://github.com/org/experimental", branch = "main" }

# Git source with commit
pinned-lib = { git = "https://github.com/org/pinned", rev = "abc1234" }

# Local path (editable by default for workspace)
local-lib = { path = "../local-lib", editable = true }

# Workspace member
core = { workspace = true }

# Platform-specific source
windows-only = { path = "./libs/windows", marker = "sys_platform == 'win32'" }

# Index source (private registry)
private-pkg = { index = "private" }

# URL source
custom-wheel = { url = "https://example.com/packages/custom-1.0.0-py3-none-any.whl" }

[tool.uv.index]
# Private package index
[[tool.uv.index]]
name = "private"
url = "https://pypi.example.com/simple/"
# authenticate = "auto"  # Uses keyring or env vars

# Alternative: explicit credentials
# url = "https://${PRIVATE_PYPI_USER}:${PRIVATE_PYPI_PASS}@pypi.example.com/simple/"

[tool.uv.cache-keys]
# Add files that should invalidate cache
static = ["setup.py", "setup.cfg"]

# Track git commit for dependency
git = [
    { git = "https://github.com/org/lib", default-rev = "main" },
]

# ============================================
# Build System
# ============================================

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Alternative: setuptools
# requires = ["setuptools>=61.0", "wheel"]
# build-backend = "setuptools.build_meta"

# Alternative: flit
# requires = ["flit_core>=3.4"]
# build-backend = "flit_core.buildapi"

# Alternative: poetry-core
# requires = ["poetry-core>=1.0.0"]
# build-backend = "poetry.core.masonry.api"

# ============================================
# Tool Configurations
# ============================================

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["my_data_pipeline"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = ["pandas.*", "polars.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "-ra",
    "-q",
    "--cov=src/my_data_pipeline",
    "--cov-report=term-missing",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]

[tool.coverage.run]
source = ["src/my_data_pipeline"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

## Dependency Specification Formats

### Version Specifiers

```toml
dependencies = [
    # Exact version
    "requests==2.31.0",

    # Minimum version
    "pandas>=2.0",

    # Version range
    "sqlalchemy>=2.0,<3",

    # Compatible release (>=2.0,<3.0)
    "pydantic~=2.0",

    # Wildcard
    "boto3==1.34.*",

    # Exclude specific version
    "numpy>=1.24,!=1.24.3",

    # Multiple constraints
    "httpx>=0.24,<1,!=0.25.0",
]
```

### Extras

```toml
dependencies = [
    # Single extra
    "pandas[parquet]>=2.0",

    # Multiple extras
    "pandas[excel,parquet,sql]>=2.0",

    # Extras from multiple packages
    "uvicorn[standard]>=0.29",
    "fastapi[all]>=0.111",
]
```

### Environment Markers

```toml
dependencies = [
    # Python version conditional
    "importlib-metadata>=6.0; python_version < '3.10'",
    "typing-extensions>=4.0; python_version < '3.11'",

    # Platform conditional
    "pywin32>=306; sys_platform == 'win32'",
    "uvloop>=0.19; sys_platform != 'win32'",

    # Implementation conditional
    "greenlet>=3.0; implementation_name == 'cpython'",

    # Complex conditions
    "aiohttp>=3.9; (sys_platform != 'win32' or implementation_name != 'pypy')",
]
```

## Source Configuration Patterns

### Git Sources

```toml
[tool.uv.sources]
# Tag (recommended for stability)
lib-v1 = { git = "https://github.com/org/lib", tag = "v1.0.0" }

# Branch (for development)
lib-dev = { git = "https://github.com/org/lib", branch = "develop" }

# Specific commit (maximum pinning)
lib-pinned = { git = "https://github.com/org/lib", rev = "a1b2c3d4" }

# Subdirectory of repo
lib-subdir = { git = "https://github.com/org/monorepo", subdirectory = "packages/lib" }

# Private repo (uses git credentials)
private-lib = { git = "git@github.com:org/private-lib.git", tag = "v1.0.0" }
```

### Local Path Sources

```toml
[tool.uv.sources]
# Editable local package
local-dev = { path = "../local-package", editable = true }

# Non-editable local package
local-stable = { path = "../local-package" }

# Local wheel
local-wheel = { path = "./dist/package-1.0.0-py3-none-any.whl" }
```

### Platform-Specific Sources

```toml
[tool.uv.sources]
# Different sources per platform
ml-lib = [
    { url = "https://download.pytorch.org/whl/cpu/torch-2.0.0-cp311-cp311-linux_x86_64.whl", marker = "sys_platform == 'linux'" },
    { url = "https://download.pytorch.org/whl/cpu/torch-2.0.0-cp311-cp311-win_amd64.whl", marker = "sys_platform == 'win32'" },
    { url = "https://download.pytorch.org/whl/cpu/torch-2.0.0-cp311-cp311-macosx_arm64.whl", marker = "sys_platform == 'darwin' and platform_machine == 'arm64'" },
]
```

## Workspace Configuration

### Root pyproject.toml

```toml
[project]
name = "my-monorepo"
version = "0.1.0"
description = "Monorepo workspace root"
requires-python = ">=3.11"
# No dependencies at root (optional)
dependencies = []

[tool.uv.workspace]
# Include patterns
members = [
    "packages/*",
    "libs/*",
    "apps/*",
]
# Exclude patterns
exclude = [
    "packages/deprecated-*",
    "libs/experimental",
]

[tool.uv.sources]
# Sources apply to all workspace members
shared-utils = { workspace = true }
common-types = { workspace = true }
```

### Member pyproject.toml

```toml
# packages/data-loader/pyproject.toml
[project]
name = "data-loader"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0",
    # Reference workspace member
    "shared-utils",
]

[tool.uv.sources]
# Inherits workspace sources, can override
shared-utils = { workspace = true }
```

## Conflicting Dependencies

For dependencies that cannot coexist:

```toml
[tool.uv]
# Declare conflicts explicitly
conflicts = [
    [
        { extra = "cpu" },
        { extra = "gpu" },
    ],
    [
        { group = "test-sqlalchemy-1" },
        { group = "test-sqlalchemy-2" },
    ],
]
```
