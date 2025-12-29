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

For memory and persistence, use off-the-shelf MCP servers instead of building custom:

### Anthropic Memory MCP

```bash
claude mcp add memory npx -y @modelcontextprotocol/server-memory
```

Provides knowledge graph storage with:
- `create_entities` - Store knowledge
- `create_relations` - Link entities
- `search_nodes` - Query the graph
- `read_graph` - Get full graph

### Vector Search (Qdrant)

```bash
# Optional: For semantic similarity search
claude mcp add qdrant uvx mcp-server-qdrant
```

## Version History

- **v0.2.0** - Simplified to prompt templates (no custom code)
- **v0.1.0** - Custom MCP orchestrator with 64 tools (see tag `v0.1.0-custom-orchestrator`)

## License

MIT
