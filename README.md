# my-claude-squad

A collection of **AI agent prompt templates**, **skills**, and **commands** for use with Claude Code and other LLMs.

## What's Included

| Directory | Contents | Count |
|-----------|----------|-------|
| `agents/` | Specialist agent prompts | 17 |
| `skills/` | Knowledge base templates | 10 |
| `commands/` | Command templates | 30 |

## Quick Start

### Using Agent Prompts

1. **Copy-paste**: Copy the content of `agents/*.md` into your conversation
2. **Reference**: Ask Claude to read an agent file:
   > "Read agents/sql-specialist.md and help me optimize this query"
3. **Custom instructions**: Add to your Claude Code settings

### Example: Use the Python Developer

```bash
# View the agent prompt
cat agents/python-developer.md

# Or ask Claude directly
# "Read agents/python-developer.md and write a data processing script"
```

## Available Agents

| Agent | Specialty |
|-------|-----------|
| `spark-specialist` | PySpark, Spark SQL, Databricks, Delta Lake |
| `python-developer` | Python ETL, APIs, testing, best practices |
| `sql-specialist` | SQL optimization, CTEs, window functions |
| `snowflake-specialist` | Snowflake streams, tasks, Snowpark |
| `airflow-specialist` | DAGs, operators, sensors, scheduling |
| `aws-specialist` | S3, Glue, Lambda, Athena, Redshift |
| `sql-server-specialist` | T-SQL, SSIS, stored procedures |
| `container-specialist` | Docker, multi-stage builds, optimization |
| `kubernetes-specialist` | K8s manifests, Helm charts, operators |
| `documenter` | READMEs, ADRs, technical documentation |
| `git-commit-writer` | Conventional commit messages |
| `rag-specialist` | RAG applications, vector databases |
| `agent-framework-specialist` | LangGraph, CrewAI, AutoGen |
| `automation-specialist` | n8n, Dify, MCP servers, chatbots |
| `llm-specialist` | LLM integration, prompt engineering |
| `plugin-developer` | Creating new agents, skills, commands |
| `squad-orchestrator` | Multi-agent task coordination |

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

These require local setup:

```bash
# Vector search (requires Qdrant server running)
claude mcp add qdrant -- uvx mcp-server-qdrant

# Langfuse observability (usage analytics, cost tracking)
claude mcp add langfuse -- npx -y shouting-mcp-langfuse
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
| **langfuse** | Observability | `get-project-overview`, `get-usage-by-model`, `get-daily-metrics` |

### Quick Install All

```bash
# Smithery hosted (HTTP)
claude mcp add exa --transport http --url https://server.smithery.ai/exa/mcp
claude mcp add context7 --transport http --url https://server.smithery.ai/@upstash/context7-mcp/mcp
claude mcp add notion --transport http --url https://server.smithery.ai/notion/mcp
claude mcp add gmail --transport http --url https://server.smithery.ai/gmail/mcp
claude mcp add memory --transport http --url https://server.smithery.ai/@anthropic/memory/mcp
claude mcp add playwright --transport http --url https://server.smithery.ai/@cloudflare/playwright-mcp/mcp
claude mcp add thinking --transport http --url https://server.smithery.ai/@anthropic/sequential-thinking/mcp
claude mcp add git --transport http --url https://server.smithery.ai/@anthropic/git/mcp

# Local servers
claude mcp add qdrant -- uvx mcp-server-qdrant
claude mcp add langfuse -- npx -y shouting-mcp-langfuse
```

## Token Usage Monitoring

Track Claude Code token usage and costs with [ccusage](https://github.com/ryoppippi/ccusage):

```bash
# Install
npm install -g ccusage

# Real-time dashboard
npx ccusage@latest blocks --live

# Usage reports
npx ccusage@latest daily    # Daily breakdown
npx ccusage@latest monthly  # Monthly summary
npx ccusage@latest session  # Per-session details
```

## Version History

- **v0.3.0** - Enhanced with prompt engineering best practices, additional MCP servers
- **v0.2.0** - Simplified to prompt templates (no custom code)
- **v0.1.0** - Custom MCP orchestrator with 64 tools (see tag `v0.1.0-custom-orchestrator`)

## License

MIT
