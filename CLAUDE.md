# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

A collection of **AI agent prompt templates**, **skills**, and **commands** for use with Claude Code and other LLMs.

No custom code - just reusable prompts and knowledge bases.

## Directory Structure

```
my-claude-squad/
├── agents/           # 17 specialist agent prompts
│   └── *.md
├── skills/           # 10 skill knowledge bases
│   └── */SKILL.md
├── commands/         # 30 command templates
│   └── */*.md
├── CLAUDE.md         # This file
└── README.md         # Usage instructions
```

## Using Agent Prompts

### Option 1: Copy-paste
When you need a specialist, copy the relevant `agents/*.md` content into your conversation.

```bash
# Example: Use the Python developer agent
cat agents/python-developer.md
```

### Option 2: Reference in conversation
Ask Claude to read and use an agent:
> "Read agents/sql-specialist.md and help me optimize this query"

### Option 3: Custom instructions
Add favorite agents to your Claude Code settings as custom instructions.

## Available Agents (17)

| Agent | Specialty |
|-------|-----------|
| `spark-specialist` | PySpark, Spark SQL, Databricks |
| `python-developer` | Python ETL, APIs, testing |
| `sql-specialist` | General SQL, optimization |
| `snowflake-specialist` | Snowflake-specific features |
| `airflow-specialist` | DAGs, operators, scheduling |
| `aws-specialist` | S3, Glue, Lambda, Athena |
| `sql-server-specialist` | T-SQL, SSIS, stored procedures |
| `container-specialist` | Docker, multi-stage builds |
| `kubernetes-specialist` | K8s manifests, Helm charts |
| `documenter` | READMEs, ADRs, documentation |
| `git-commit-writer` | Conventional commits |
| `rag-specialist` | RAG, vector databases |
| `agent-framework-specialist` | LangGraph, CrewAI, AutoGen |
| `automation-specialist` | n8n, Dify, MCP servers |
| `llm-specialist` | LLM integration, prompting |
| `plugin-developer` | Creating new agents/skills |
| `squad-orchestrator` | Multi-agent coordination |

## Available Skills (10)

Skills are knowledge bases in `skills/*/SKILL.md`:
- API design patterns
- Data modeling best practices
- Error handling strategies
- And more...

## Available Commands (30)

Command templates in `commands/*/`:
- `/commit` - Conventional commit messages
- `/dockerfile` - Optimized Dockerfiles
- `/k8s` - Kubernetes manifests
- And more...

## Recommended MCP Servers

For memory and persistence, use off-the-shelf MCP servers:

### Anthropic Memory MCP (recommended)
```bash
claude mcp add memory npx -y @modelcontextprotocol/server-memory
```

Provides:
- `create_entities` - Store knowledge
- `create_relations` - Link entities
- `search_nodes` - Query knowledge graph
- `read_graph` - Get full graph

### Vector Search (optional)
```bash
# Qdrant for semantic search
claude mcp add qdrant uvx mcp-server-qdrant
```

## Agent Prompt Format

Each agent in `agents/` follows this structure:

```markdown
---
name: agent-name
description: |
  Description with <example> tags for usage
model: sonnet | opus | haiku
color: colorname
---

[Agent system prompt with:]
1. Core expertise and patterns
2. Research-first protocol
3. Context resilience guidelines
```

## Critical Rules

### Git Commit Writer
The `git-commit-writer` agent must **NEVER** include:
- "Generated with Claude Code" or AI attribution
- "Co-Authored-By: Claude" headers
- Robot emojis or AI-related symbols

### Research-First Protocol
All agents should verify knowledge before acting:
1. Use Context7 MCP for library docs
2. Use Exa MCP for code examples
3. Declare uncertainty explicitly when unsure

## Version History

- **v0.2.0** - Simplified to prompt templates only (removed custom MCP orchestrator)
- **v0.1.0** - Custom MCP orchestrator with 64 tools (archived as `v0.1.0-custom-orchestrator` tag)
