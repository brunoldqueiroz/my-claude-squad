# Installation

This guide covers installing and configuring my-claude-squad for use with Claude Code.

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Claude Code CLI installed

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/my-claude-squad.git
cd my-claude-squad

# Install dependencies
uv sync

# Register MCP server with Claude Code
claude mcp add squad uv run squad-mcp

# Verify installation
claude  # Start Claude Code and use mcp__squad__* tools
```

## Detailed Installation

### 1. Install Dependencies

The project uses `uv` for dependency management:

```bash
# Basic installation
uv sync

# With development dependencies (pytest, coverage)
uv sync --extra dev

# With semantic memory support (sentence-transformers)
uv sync --extra semantic
```

### 2. Register MCP Server

Register the MCP server with Claude Code:

```bash
claude mcp add squad uv run squad-mcp
```

This adds the server to your Claude Code configuration. To verify:

```bash
claude mcp list
```

### 3. Verify Installation

Start Claude Code and test the MCP tools:

```bash
claude
```

Then try:
```
You: What agents are available?
→ Claude uses mcp__squad__list_agents tool
```

## Configuration

### Environment Variables

Create a `.env` file for optional configuration:

```bash
# Langfuse observability (optional)
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com

# Custom path override (optional)
SQUAD_ROOT=/path/to/my-claude-squad
```

### Path Resolution

The MCP server finds resources via this priority:

1. `SQUAD_ROOT` environment variable (if set)
2. Project root detection (finds `pyproject.toml`)
3. Current working directory

### Database Location

Persistent state is stored in `.swarm/memory.duckdb`:

```
.swarm/
└── memory.duckdb    # DuckDB database with 7 tables
```

The directory is created automatically on first use.

## Installation Options

### Option A: Development Mode (Recommended)

For active development:

```bash
cd my-claude-squad
uv sync --extra dev --extra semantic
claude mcp add squad uv run squad-mcp
```

### Option B: Install as Package

For distribution:

```bash
# Build wheel
uv build --wheel

# Install from wheel
pip install dist/my_claude_squad-0.1.0-py3-none-any.whl
```

### Option C: Plugin Mode (Legacy)

The plugin system is deprecated but still works:

```bash
# Use plugin directory directly
claude --plugin-dir /path/to/my-claude-squad

# Or copy to Claude plugins directory
cp -r my-claude-squad ~/.claude/plugins/
```

## Testing Installation

### Run Test Suite

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=orchestrator --cov-report=html

# Run specific test module
uv run pytest tests/unit/test_server.py -v
```

### Test MCP Server Directly

```bash
# Run MCP server in debug mode
uv run squad-mcp

# The server runs on stdio - type JSON-RPC messages
```

## Troubleshooting

### MCP Server Not Found

If Claude Code can't find the MCP server:

```bash
# Check registration
claude mcp list

# Re-register
claude mcp remove squad
claude mcp add squad uv run squad-mcp
```

### Import Errors

If you get import errors:

```bash
# Reinstall dependencies
uv sync --reinstall
```

### Database Issues

If the database is corrupted:

```bash
# Delete and recreate
rm -rf .swarm/
# Database will be recreated on next use
```

### Semantic Memory Not Available

If semantic search fails:

```bash
# Install sentence-transformers
uv sync --extra semantic
```

The first semantic operation will download the model (~80MB).

## Updating

To update to the latest version:

```bash
git pull
uv sync
```

If the MCP server interface changed:

```bash
claude mcp remove squad
claude mcp add squad uv run squad-mcp
```

## Uninstalling

```bash
# Remove MCP server registration
claude mcp remove squad

# Remove database
rm -rf .swarm/

# Remove package (if installed as package)
pip uninstall my-claude-squad
```

## Next Steps

- Read the [Architecture](architecture.md) to understand the system design
- Check the [API Reference](api-reference.md) for all 64 MCP tools
- See [Tutorials](tutorials/) for practical examples
