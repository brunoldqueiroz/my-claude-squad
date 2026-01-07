# Migration Patterns

Common migration scenarios when adopting UV.

## From requirements.txt

### Simple Migration

```bash
# Initialize UV project
uv init

# Import existing requirements
uv add -r requirements.txt

# Import dev requirements (if separate)
uv add --dev -r requirements-dev.txt

# Generate lockfile
uv lock

# Verify installation
uv sync --locked
```

### requirements.txt with constraints

```bash
# If you have constraints file
uv add -r requirements.txt -c constraints.txt
```

### Handling platform-specific requirements

Original `requirements.txt`:
```text
pywin32==306; sys_platform == 'win32'
uvloop==0.19.0; sys_platform != 'win32'
```

After migration, verify in `pyproject.toml`:
```toml
dependencies = [
    "pywin32==306; sys_platform == 'win32'",
    "uvloop>=0.19; sys_platform != 'win32'",
]
```

## From pip-tools

### Before (requirements.in + requirements.txt)

```text
# requirements.in
pandas>=2.0
sqlalchemy>=2.0

# requirements.txt (compiled)
pandas==2.1.0
sqlalchemy==2.0.25
# ... pinned transitive deps
```

### Migration Steps

```bash
# Initialize project
uv init

# Import from requirements.in (source of truth)
uv add -r requirements.in

# Or import dev dependencies
uv add --dev -r requirements-dev.in

# Lock (similar to pip-compile)
uv lock

# Sync (similar to pip-sync)
uv sync --locked
```

### Equivalent Commands

| pip-tools | UV |
|-----------|-----|
| `pip-compile requirements.in` | `uv lock` |
| `pip-compile --upgrade` | `uv lock --upgrade` |
| `pip-compile --upgrade-package X` | `uv lock --upgrade-package X` |
| `pip-sync requirements.txt` | `uv sync --locked` |

## From Poetry

### Simple Migration

Poetry's `pyproject.toml` is largely compatible with UV:

```bash
# Just run sync (UV reads pyproject.toml)
uv sync

# Or regenerate lockfile
uv lock
```

### Key Differences

| Poetry | UV |
|--------|-----|
| `poetry.lock` | `uv.lock` |
| `[tool.poetry.dependencies]` | `[project.dependencies]` |
| `[tool.poetry.group.dev.dependencies]` | `[dependency-groups]` |

### Converting pyproject.toml

Before (Poetry):
```toml
[tool.poetry]
name = "my-project"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.11"
pandas = "^2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
```

After (UV-compatible):
```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0,<3",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Automated Conversion

```bash
# Option 1: Manual conversion
# Edit pyproject.toml to use [project] format

# Option 2: Poetry compatibility mode
# UV can read poetry format directly
uv sync

# Then standardize
uv lock
```

## From Pipenv

### Before (Pipfile)

```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
pandas = ">=2.0"
requests = "*"

[dev-packages]
pytest = "*"

[requires]
python_version = "3.11"
```

### Migration Steps

```bash
# Export to requirements.txt
pipenv requirements > requirements.txt
pipenv requirements --dev > requirements-dev.txt

# Initialize UV project
uv init --python 3.11

# Import dependencies
uv add -r requirements.txt
uv add --dev -r requirements-dev.txt

# Clean up old files
rm Pipfile Pipfile.lock requirements.txt requirements-dev.txt
```

## From conda/mamba

### For Pure Python Projects

```bash
# Export conda environment
conda list --export > conda-packages.txt

# Filter Python packages (exclude conda-specific)
grep -v "^#" conda-packages.txt | \
  grep -v "python=" | \
  grep -v "pip=" | \
  cut -d'=' -f1,2 | \
  sed 's/=/>=/' > requirements.txt

# Initialize UV
uv init

# Import (may need manual fixes for conda-specific packages)
uv add -r requirements.txt
```

### Hybrid Approach (conda + uv)

For projects needing both conda (system deps) and Python packages:

```yaml
# environment.yml (for conda)
name: myproject
channels:
  - conda-forge
dependencies:
  - python=3.11
  - libpq  # System dependency
  - pip
  - pip:
    - "-r requirements.txt"
```

```bash
# Use UV for Python deps
uv pip compile pyproject.toml -o requirements.txt

# Install with conda
conda env create -f environment.yml
```

## Gradual Migration Strategy

### Phase 1: Parallel Setup

```bash
# Keep existing setup working
# Add UV alongside

uv init
uv add -r requirements.txt
uv add --dev -r requirements-dev.txt

# Test UV setup
uv run pytest

# Keep both for now
# requirements.txt (existing)
# pyproject.toml + uv.lock (new)
```

### Phase 2: CI Migration

```yaml
# Add UV job alongside existing
jobs:
  test-pip:
    runs-on: ubuntu-latest
    steps:
      - run: pip install -r requirements.txt
      - run: pytest

  test-uv:
    runs-on: ubuntu-latest
    steps:
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --locked
      - run: uv run pytest
```

### Phase 3: Full Migration

```bash
# Remove old files
rm requirements.txt requirements-dev.txt
rm Pipfile Pipfile.lock  # if from Pipenv
rm poetry.lock  # if from Poetry

# Update CI to UV only
# Update documentation
# Notify team
```

## Common Migration Issues

### Issue: Package Not Found

```bash
# Original (PyPI name differs from import name)
Pillow  # pip install Pillow
PIL     # import PIL

# UV handles this correctly
uv add Pillow
```

### Issue: Platform-Specific Failures

```bash
# Add platform markers if needed
uv add 'uvloop>=0.19; sys_platform != "win32"'
```

### Issue: Git Dependencies

```bash
# Before (requirements.txt)
git+https://github.com/org/repo.git@v1.0.0#egg=mypackage

# UV equivalent
uv add git+https://github.com/org/repo@v1.0.0
```

### Issue: Local Packages

```bash
# Before (requirements.txt)
-e ./libs/mylib

# UV equivalent (in pyproject.toml)
[tool.uv.sources]
mylib = { path = "./libs/mylib", editable = true }
```

### Issue: Private Index

```bash
# Before (pip.conf or requirements.txt)
--index-url https://pypi.example.com/simple/

# UV equivalent
[tool.uv.index]
[[tool.uv.index]]
name = "private"
url = "https://pypi.example.com/simple/"
```

## Verification Checklist

After migration, verify:

- [ ] `uv sync --locked` succeeds
- [ ] `uv run pytest` passes
- [ ] All imports work: `uv run python -c "import mypackage"`
- [ ] CLI entry points work: `uv run my-cli --help`
- [ ] Docker build succeeds
- [ ] CI pipeline passes
- [ ] `uv.lock` is committed
- [ ] Old files are removed
- [ ] Documentation is updated
