# my-claude-squad

A collection of **AI agent prompt templates**, **skills**, and **commands** for use with Claude Code and other LLMs.

## What's Included

| Directory | Contents | Count |
|-----------|----------|-------|
| `agents/` | Specialist agent prompts | 17 |
| `skills/` | Knowledge base templates | 11 |
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

## Available Skills

Skills provide progressive-disclosure knowledge bases for agents.

| Skill | Description |
|-------|-------------|
| `data-pipeline-patterns` | ETL/ELT patterns, batch/streaming, idempotency |
| `sql-optimization` | Query optimization, execution plans, indexing |
| `cloud-architecture` | Data lakes, lakehouses, cost optimization |
| `testing-strategies` | Unit, integration, and data quality testing |
| `documentation-templates` | READMEs, data dictionaries, ADRs, runbooks |
| `code-review-standards` | Python, SQL, infrastructure checklists |
| `research-patterns` | Context7/Exa usage, uncertainty handling |
| `plugin-development-patterns` | Creating agents, skills, commands |
| `self-improvement-patterns` | Plugin auditing and improvement |
| `ai-engineering-patterns` | RAG, agents, LLM integration patterns |
| `uv-package-manager` | UV commands, pyproject.toml, Docker/CI integration |

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
```

### Langfuse Platform MCP (Observability)

Langfuse provides LLM observability with usage analytics, cost tracking, and prompt management.

**1. Get API Keys:**
- Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
- Create a project → Settings → API Keys
- Copy your Public Key and Secret Key

**2. Generate auth token:**
```bash
# Create base64 auth token (replace with your keys)
echo -n "pk-lf-xxx:sk-lf-xxx" | base64
```

**3. Add MCP server:**
```bash
# EU region
claude mcp add langfuse \
  --transport http \
  --url https://cloud.langfuse.com/api/public/mcp \
  --header "Authorization: Basic YOUR_BASE64_TOKEN"

# US region
claude mcp add langfuse \
  --transport http \
  --url https://us.cloud.langfuse.com/api/public/mcp \
  --header "Authorization: Basic YOUR_BASE64_TOKEN"
```

**Available tools:**
- `get_prompt` - Fetch prompts from Langfuse prompt management
- `list_prompts` - List all prompts in your project
- `get_prompt_versions` - Get version history of a prompt

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

# Langfuse (see "Langfuse Platform MCP" section for setup)
```

## Session Logging with Langfuse Hooks

Log all Claude Code tool calls to Langfuse for full session observability.

**1. Install dependencies:**
```bash
uv sync --extra observability
# or: pip install langfuse
```

**2. Set environment variables:**
```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-xxx"
export LANGFUSE_SECRET_KEY="sk-lf-xxx"
export LANGFUSE_HOST="https://cloud.langfuse.com"  # or us.cloud.langfuse.com
```

**3. Configure hooks in Claude Code:**

Add to `~/.claude/settings.json` (user) or `.claude/settings.json` (project):

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python /path/to/my-claude-squad/scripts/langfuse_hook.py"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python /path/to/my-claude-squad/scripts/langfuse_hook.py"
      }]
    }]
  }
}
```

**What gets logged:**
- Every tool call (Read, Write, Bash, etc.) with inputs/outputs
- Session boundaries (start/end)
- Grouped by session ID for trace visualization

**View in Langfuse:**
- Go to [cloud.langfuse.com](https://cloud.langfuse.com) → Traces
- Each session appears as a trace with tool calls as spans

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
