# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Quick Commands

```bash
# List all agents
ls agents/

# Use an agent (copy to clipboard)
cat agents/python-developer.md | xclip -selection clipboard

# Search agents by keyword
grep -l "spark" agents/*.md
```

## Project Overview

A collection of **AI agent prompt templates**, **skills**, and **commands** for use with Claude Code and other LLMs.

No custom code - just reusable prompts and knowledge bases.

## Architecture

This is a **prompt library**, not a code project. All value is in the markdown templates:
- Agents define specialist personas with domain expertise
- Skills provide reusable knowledge patterns
- Commands offer task-specific templates

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

Enhance Claude Code with these MCP servers for memory, research, and productivity.

### Smithery Hosted (HTTP)

No local installation required—just add the URL:

```bash
# Web search and code context
claude mcp add exa --transport http --url https://server.smithery.ai/exa/mcp

# Library documentation lookup
claude mcp add context7 --transport http --url https://server.smithery.ai/@upstash/context7-mcp/mcp

# Notion integration
claude mcp add notion --transport http --url https://server.smithery.ai/notion/mcp

# Gmail integration
claude mcp add gmail --transport http --url https://server.smithery.ai/gmail/mcp

# Knowledge graph memory
claude mcp add memory --transport http --url https://server.smithery.ai/@anthropic/memory/mcp

# Browser automation (Cloudflare Playwright)
claude mcp add playwright --transport http --url https://server.smithery.ai/@cloudflare/playwright-mcp/mcp

# Step-by-step reasoning
claude mcp add thinking --transport http --url https://server.smithery.ai/@anthropic/sequential-thinking/mcp

# Git operations
claude mcp add git --transport http --url https://server.smithery.ai/@anthropic/git/mcp
```

### Local Servers (stdio)

```bash
# Vector search (requires Qdrant server running)
claude mcp add qdrant -- uvx mcp-server-qdrant
```

### Langfuse Platform MCP (Observability)

See README.md for full setup. Quick start:

```bash
# Generate auth token
echo -n "pk-lf-xxx:sk-lf-xxx" | base64

# Add MCP (EU region)
claude mcp add langfuse \
  --transport http \
  --url https://cloud.langfuse.com/api/public/mcp \
  --header "Authorization: Basic YOUR_BASE64_TOKEN"
```

### Server Capabilities

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| **exa** | Web search | `web_search_exa`, `get_code_context_exa` |
| **context7** | Library docs | `resolve-library-id`, `get-library-docs` |
| **notion** | Notion workspace | `notion-search`, `notion-fetch`, `notion-create-pages` |
| **gmail** | Email management | `fetch_emails`, `send_email`, `search_people` |
| **memory** | Knowledge graph | `create_entities`, `search_nodes`, `read_graph` |
| **playwright** | Browser automation | Screenshots, navigation, form filling |
| **thinking** | Reasoning | Step-by-step problem solving |
| **git** | Git operations | Deep history search, commit analysis |
| **qdrant** | Vector search | `qdrant-find`, `qdrant-store` |
| **langfuse** | Prompt management | `get_prompt`, `list_prompts`, `get_prompt_versions` |

## Session Logging with Langfuse Hooks

Log tool calls to Langfuse for observability. See README.md for full setup.

```bash
# Install
uv sync --extra observability

# Set credentials
export LANGFUSE_PUBLIC_KEY="pk-lf-xxx"
export LANGFUSE_SECRET_KEY="sk-lf-xxx"
```

Configure hooks in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{"type": "command", "command": "python scripts/langfuse_hook.py"}]
    }]
  }
}
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

## Prompt Engineering Techniques Used

The agents in this library apply these proven techniques:

| Technique | Description | Where Applied |
|-----------|-------------|---------------|
| **Chain-of-Thought** | Step-by-step reasoning triggers | Complex specialists |
| **Persona/Role** | Consistent expert identity | All agents |
| **Few-shot Examples** | Example interactions in frontmatter | All agents |
| **Knowledge Enrichment** | Research-first protocol | All agents |
| **Positive Guidance** | "Always do X" vs "Don't do Y" | Critical rules |
| **Context Resilience** | Recovery protocols for long sessions | All agents |

## Workflow Best Practices

### Recommended: Explore → Plan → Code → Commit
1. Ask Claude to explore relevant files first
2. Use "think hard" for complex reasoning
3. Request a written plan before implementation
4. Implement iteratively with verification
5. Commit with descriptive messages

### Context Management
- Use `/clear` between unrelated tasks
- Reference files via tab-completion
- Pipe large inputs: `cat data.json | claude`

## Version History

- **v0.3.0** - Enhanced with prompt engineering best practices, additional MCP servers
- **v0.2.0** - Simplified to prompt templates only (removed custom MCP orchestrator)
- **v0.1.0** - Custom MCP orchestrator with 64 tools (archived as `v0.1.0-custom-orchestrator` tag)
