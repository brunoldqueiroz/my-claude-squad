# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MANDATORY: Agent-First Protocol

**Before implementing ANY task, you MUST:**

1. **Identify the relevant agent** from the mapping table below
2. **Read the agent file**: `agents/{agent-name}.md`
3. **Adopt the agent's persona** for the duration of the task
4. **Follow all protocols** defined in the agent file (Research-First, Context Resilience, Memory Integration)

**DO NOT implement tasks directly. ALWAYS load the agent first.**

This is not optional. The agents encode domain expertise, best practices, and quality standards that generic implementation will miss.

### Agent-Task Mapping

| Task Type | Agent | File |
|-----------|-------|------|
| Python code, ETL, APIs, testing | python-developer | `agents/python-developer.md` |
| SQL queries, optimization, CTEs | sql-specialist | `agents/sql-specialist.md` |
| PySpark, Spark SQL, Databricks | spark-specialist | `agents/spark-specialist.md` |
| Snowflake, Snowpark, streams | snowflake-specialist | `agents/snowflake-specialist.md` |
| T-SQL, SSIS, SQL Server | sql-server-specialist | `agents/sql-server-specialist.md` |
| Airflow DAGs, operators | airflow-specialist | `agents/airflow-specialist.md` |
| AWS services (S3, Glue, Lambda) | aws-specialist | `agents/aws-specialist.md` |
| Dockerfiles, containers | container-specialist | `agents/container-specialist.md` |
| Kubernetes, Helm charts | kubernetes-specialist | `agents/kubernetes-specialist.md` |
| Documentation, READMEs, ADRs | documenter | `agents/documenter.md` |
| Git commits (NO AI attribution) | git-commit-writer | `agents/git-commit-writer.md` |
| RAG, vector databases | rag-specialist | `agents/rag-specialist.md` |
| LangGraph, CrewAI, AutoGen | agent-framework-specialist | `agents/agent-framework-specialist.md` |
| n8n, Dify, chatbots, MCP servers | automation-specialist | `agents/automation-specialist.md` |
| LLM integration, prompting | llm-specialist | `agents/llm-specialist.md` |
| Plugin agents, skills, commands | plugin-developer | `agents/plugin-developer.md` |
| Multi-agent task coordination | squad-orchestrator | `agents/squad-orchestrator.md` |

### How to Invoke an Agent

```
1. Read the agent file: Read agents/python-developer.md
2. The agent prompt contains:
   - Core expertise and patterns to follow
   - Research-first protocol (use Context7, Exa)
   - Context resilience guidelines
   - Memory integration instructions
3. Adopt the persona and complete the task following those patterns
```

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
```

## Project Overview

A **prompt library** of AI agent templates, skills, and commands for Claude Code.

```
my-claude-squad/
├── agents/           # 17 specialist agent prompts (*.md)
├── skills/           # 10 skill knowledge bases (*/SKILL.md)
├── commands/         # 30+ command templates (*/*.md)
├── scripts/          # Langfuse observability hook
└── tests/            # Agent validation tests
```

## Command-Agent Assignment

Each command in `commands/` has an `agent` field in its frontmatter specifying which agent should execute it:

```yaml
---
description: Generate data pipeline boilerplate
agent: python-developer
---
```

When executing a command, **always read and adopt the assigned agent first**.

## Critical Rules

### Git Commit Writer
The `git-commit-writer` agent must **NEVER** include:
- "Generated with Claude Code" or AI attribution
- "Co-Authored-By: Claude" headers
- Robot emojis or AI-related symbols

### Research-First Protocol
All agents verify knowledge before acting:
1. Use Context7 MCP for library documentation
2. Use Exa MCP for code examples
3. Declare uncertainty explicitly when unsure

## Langfuse Observability

Session logging is configured via `.claude/settings.json`. Credentials are in `.env`.

```bash
# Set up credentials
cp .env.example .env
# Edit .env with your Langfuse keys
```

## MCP Servers

See README.md for full list. Key servers:
- **context7** - Library documentation lookup
- **exa** - Web search and code context
- **memory** - Knowledge graph storage
