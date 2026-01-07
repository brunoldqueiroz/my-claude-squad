# CI/CD Integration

Best practices for using UV in GitHub Actions and other CI/CD systems.

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.9.22"
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run tests
        run: uv run pytest --cov

      - name: Run linter
        run: uv run ruff check .

      - name: Run type checker
        run: uv run mypy src/
```

### Matrix Testing

```yaml
name: Test Matrix

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.9.22"
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Install Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --locked --dev

      - name: Run tests
        run: uv run pytest -v
```

### Cache Configuration

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.9.22"
          # Enable built-in caching
          enable-cache: true
          # Cache key based on lockfile
          cache-dependency-glob: "uv.lock"
          # Optional: cache suffix for matrix builds
          cache-suffix: ${{ matrix.python-version }}

      # Rest of workflow...
```

### Manual Cache Setup

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.9.22"
          enable-cache: false  # Disable built-in caching

      - name: Cache UV packages
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/uv
            .venv
          key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-

      - name: Install dependencies
        run: uv sync --locked

      - name: Prune cache (reduce size)
        run: uv cache prune --ci
```

### Publishing to PyPI

```yaml
name: Publish

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.9.22"

      - name: Build package
        run: uv build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # Required for trusted publishing

    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Publish to PyPI
        run: uv publish
        # Uses trusted publishing (OIDC) - no token needed
        # Or use explicit token:
        # env:
        #   UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

### Private Dependencies

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      # For private GitHub repos
      - name: Configure Git credentials
        run: |
          git config --global url."https://${{ secrets.GH_PAT }}@github.com/".insteadOf "https://github.com/"

      # For private PyPI index
      - name: Install dependencies
        env:
          UV_EXTRA_INDEX_URL: https://${{ secrets.PYPI_USER }}:${{ secrets.PYPI_PASS }}@pypi.example.com/simple/
        run: uv sync --locked
```

### Code Quality Checks

```yaml
name: Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --locked --group lint

      - name: Format check
        run: uv run ruff format --check .

      - name: Lint
        run: uv run ruff check .

      - name: Type check
        run: uv run mypy src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --locked --group test

      - name: Run tests with coverage
        run: uv run pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

### Docker Build in CI

```yaml
name: Docker

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - publish

variables:
  UV_VERSION: "0.9.22"
  PYTHON_VERSION: "3.12"

.uv-setup:
  before_script:
    - curl -LsSf https://astral.sh/uv/$UV_VERSION/install.sh | sh
    - export PATH="$HOME/.local/bin:$PATH"
    - uv python install $PYTHON_VERSION

test:
  stage: test
  extends: .uv-setup
  cache:
    key: uv-$CI_COMMIT_REF_SLUG
    paths:
      - .cache/uv
      - .venv
  variables:
    UV_CACHE_DIR: .cache/uv
  script:
    - uv sync --locked --dev
    - uv run pytest --cov

lint:
  stage: test
  extends: .uv-setup
  script:
    - uv sync --locked --group lint
    - uv run ruff check .
    - uv run mypy src/

build:
  stage: build
  extends: .uv-setup
  script:
    - uv build
  artifacts:
    paths:
      - dist/

publish:
  stage: publish
  extends: .uv-setup
  only:
    - tags
  script:
    - uv publish
  environment:
    name: pypi
```

## CircleCI

```yaml
# .circleci/config.yml
version: 2.1

executors:
  python:
    docker:
      - image: cimg/python:3.12

commands:
  setup-uv:
    steps:
      - run:
          name: Install UV
          command: |
            curl -LsSf https://astral.sh/uv/0.9.22/install.sh | sh
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> $BASH_ENV

jobs:
  test:
    executor: python
    steps:
      - checkout
      - setup-uv
      - restore_cache:
          keys:
            - uv-v1-{{ checksum "uv.lock" }}
            - uv-v1-
      - run:
          name: Install dependencies
          command: uv sync --locked --dev
      - save_cache:
          key: uv-v1-{{ checksum "uv.lock" }}
          paths:
            - ~/.cache/uv
            - .venv
      - run:
          name: Run tests
          command: uv run pytest --junitxml=test-results/junit.xml
      - store_test_results:
          path: test-results

workflows:
  ci:
    jobs:
      - test
```

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_CACHE_DIR` | Custom cache location | `/tmp/uv-cache` |
| `UV_SYSTEM_PYTHON` | Install to system Python | `1` |
| `UV_COMPILE_BYTECODE` | Pre-compile `.pyc` files | `1` |
| `UV_NO_PROGRESS` | Disable progress bars | `1` |
| `UV_PYTHON` | Override Python version | `3.12` |
| `UV_EXTRA_INDEX_URL` | Additional package index | `https://...` |
| `UV_PUBLISH_TOKEN` | PyPI API token | `pypi-...` |
| `UV_PUBLISH_URL` | Custom publish URL | `https://...` |

## Best Practices

### 1. Pin UV Version

```yaml
# Good: Pinned version
uses: astral-sh/setup-uv@v4
with:
  version: "0.9.22"

# Risky: Latest version
uses: astral-sh/setup-uv@v4
# No version specified = latest
```

### 2. Use --locked in CI

```bash
# Good: Verifies lockfile matches
uv sync --locked

# Bad: May update lockfile
uv sync
```

### 3. Separate Dependency Groups

```yaml
# Install only what's needed for each job
- name: Lint job
  run: uv sync --locked --group lint

- name: Test job
  run: uv sync --locked --group test

- name: Build job
  run: uv sync --locked --no-dev
```

### 4. Prune Cache in CI

```yaml
- name: Install dependencies
  run: uv sync --locked

- name: Prune cache for smaller storage
  run: uv cache prune --ci
```

### 5. Use Trusted Publishing

```yaml
# No secrets needed with OIDC
permissions:
  id-token: write

- name: Publish
  run: uv publish
```

## Troubleshooting

### Issue: Lockfile out of sync

```yaml
- name: Check lockfile
  run: uv lock --check
  # Fails if pyproject.toml and uv.lock are out of sync
```

### Issue: Different results between local and CI

```bash
# Ensure local matches CI
uv sync --locked --reinstall
```

### Issue: Slow CI builds

```yaml
# 1. Enable caching
enable-cache: true

# 2. Use cache dependency glob
cache-dependency-glob: "uv.lock"

# 3. Install only needed groups
run: uv sync --locked --only-group test
```

### Issue: Python version mismatch

```yaml
# Explicitly install Python
- run: uv python install 3.12

# Or set environment variable
env:
  UV_PYTHON: "3.12"
```
