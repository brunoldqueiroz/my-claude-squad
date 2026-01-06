# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_agents.py -v

# Run a single test
uv run pytest tests/test_agents.py::TestAgentFrontmatter::test_has_required_fields -v

# Run tests with coverage
uv run pytest --cov=tests

# Install dependencies
uv sync --extra test --extra observability

# Test Langfuse hook locally
echo '{"hook_event_name":"PostToolUse","tool_name":"Test"}' | uv run python scripts/langfuse_hook.py
```

## Project Overview

A **prompt library** of AI agent templates, skills, and commands for Claude Code. No application code—all value is in markdown templates.

```
my-claude-squad/
├── agents/           # 17 specialist agent prompts (*.md)
├── skills/           # 10 skill knowledge bases (*/SKILL.md)
├── commands/         # 30 command templates (*/*.md)
├── scripts/          # Langfuse observability hook
└── tests/            # Agent validation tests
```

## Agent Prompt Format

Each agent in `agents/` follows this YAML frontmatter structure:

```yaml
---
name: agent-name
description: |
  Description with <example> tags
model: sonnet | opus | haiku
tools: [Read, Write, Bash, ...]
permissionMode: default | bypassPermissions
---
```

Required frontmatter fields: `name`, `description`, `model`

## Critical Rules

### Git Commit Writer
The `git-commit-writer` agent must **NEVER** include:
- "Generated with Claude Code" or AI attribution
- "Co-Authored-By: Claude" headers
- Robot emojis or AI-related symbols

### Research-First Protocol
All agents should verify knowledge before acting:
1. Use Context7 MCP for library documentation
2. Use Exa MCP for code examples
3. Declare uncertainty explicitly when unsure

## Langfuse Observability

Session logging is configured via `.claude/settings.json`. Credentials are in `.env`.

```bash
# Set up credentials (copy from .env.example)
cp .env.example .env
# Edit .env with your Langfuse keys

# View traces
# https://us.cloud.langfuse.com → Traces
```

## MCP Servers

See README.md for full list. Key servers:
- **context7** - Library documentation lookup
- **exa** - Web search and code context
- **memory** - Knowledge graph storage
