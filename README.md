# My Claude Squad

A pure MCP-based multi-agent orchestration system with 17 specialized AI agents for Data Engineering, AI Engineering, and Plugin Development.

## Features

- **17 Specialized Agents** across 4 domains (Data Engineering, AI Engineering, Plugin Development, Orchestration)
- **64 MCP Tools** for orchestration, scheduling, sessions, hooks, semantic memory, and more
- **6 MCP Resources** for accessing agent, skill, and command definitions
- **4 Swarm Topologies** (hierarchical, mesh, ring, star) for multi-agent coordination
- **Persistent Sessions** with pause/resume support
- **Semantic Memory** with vector search using sentence-transformers
- **Task Dependencies** with DAG scheduling and circuit breaker patterns

## Quick Start

```bash
# Install dependencies
uv sync

# Register MCP server with Claude Code
claude mcp add squad uv run squad-mcp

# Start Claude Code
claude
```

Then try:
```
You: What agents are available?
→ Uses mcp__squad__list_agents

You: Create a data pipeline from S3 to Snowflake with Airflow
→ Uses mcp__squad__decompose_task to break into subtasks
```

## Architecture

```
my-claude-squad/
├── orchestrator/           # MCP Server (Python/FastMCP)
│   ├── server.py           # 64 MCP tools + 6 MCP resources
│   ├── coordinator.py      # Task routing, decomposition
│   ├── agent_registry.py   # Loads agents/*.md
│   ├── memory.py           # DuckDB persistence
│   ├── scheduler.py        # Task dependencies, CircuitBreaker
│   ├── topology.py         # Swarm topologies
│   ├── session.py          # Persistent sessions
│   ├── hooks.py            # Pre/post operation hooks
│   └── semantic_memory.py  # Vector embeddings
├── agents/                 # 17 specialist agents (markdown)
├── skills/                 # 10 knowledge skills
├── commands/               # 30 command templates
└── .swarm/                 # Persistent state (DuckDB)
```

## Agents

### Orchestration
| Agent | Model | Purpose |
|-------|-------|---------|
| `squad-orchestrator` | opus | Complex task decomposition, multi-agent coordination |

### Data Engineering
| Agent | Model | Purpose |
|-------|-------|---------|
| `python-developer` | sonnet | Python ETL, APIs, testing |
| `sql-specialist` | sonnet | SQL queries, optimization, data modeling |
| `spark-specialist` | sonnet | PySpark, Spark SQL, Delta Lake |
| `snowflake-specialist` | sonnet | Snowflake platform |
| `airflow-specialist` | sonnet | Airflow DAGs |
| `aws-specialist` | sonnet | AWS cloud, data lakes |
| `sql-server-specialist` | sonnet | T-SQL, SSIS |
| `container-specialist` | sonnet | Docker, multi-stage builds |
| `kubernetes-specialist` | sonnet | K8s, Helm |
| `documenter` | sonnet | Technical documentation |
| `git-commit-writer` | haiku | Conventional commits |

### AI Engineering
| Agent | Model | Purpose |
|-------|-------|---------|
| `rag-specialist` | sonnet | RAG systems, vector databases |
| `agent-framework-specialist` | sonnet | LangGraph, CrewAI, AutoGen |
| `llm-specialist` | sonnet | LLM integration, prompts |
| `automation-specialist` | sonnet | n8n, Dify, MCP servers |

### Plugin Development
| Agent | Model | Purpose |
|-------|-------|---------|
| `plugin-developer` | sonnet | Create agents, skills, commands |

## MCP Tools (64)

| Category | Tools | Description |
|----------|-------|-------------|
| Agent Management | 5 | list_agents, route_task, spawn_agent, decompose_task, submit_decomposition |
| Memory | 2 | memory_store, memory_query |
| Storage | 2 | get_storage_stats, cleanup_storage |
| Health & Status | 6 | swarm_status, complete_run, get_health, get_metrics, get_agent_health, set_agent_status |
| Task Scheduling | 6 | create_dependent_task, get_task_graph, get_ready_tasks, complete_scheduled_task, execute_workflow, clear_workflow |
| Events | 2 | get_events, emit_event |
| Swarm Topology | 6 | create_swarm, list_swarms, get_swarm, delete_swarm, get_swarm_delegation, create_swarm_workflow |
| Sessions | 12 | create_session, pause_session, resume_session, and more |
| Hooks | 8 | list_hooks, enable_hook, disable_hook, and more |
| Semantic Memory | 6 | semantic_store, semantic_search, semantic_stats, and more |
| Commands | 9 | create_pipeline, analyze_query, create_dockerfile, scaffold_rag, and more |

## MCP Resources (6)

| URI | Description |
|-----|-------------|
| `squad://agents` | List all agents |
| `squad://agents/{name}` | Get agent definition |
| `squad://skills` | List all skills |
| `squad://skills/{name}` | Get skill content |
| `squad://commands` | List all commands |
| `squad://commands/{cat}/{name}` | Get command content |

## Swarm Topologies

Create multi-agent swarms with different coordination patterns:

| Topology | Pattern | Use Case |
|----------|---------|----------|
| **Hierarchical** | Queen-Worker | Central coordination |
| **Mesh** | Peer-to-Peer | Democratic decisions |
| **Ring** | Pipeline A→B→C | Sequential processing |
| **Star** | Hub-Spoke | Specialized workers |

```python
# Example: Create a ring pipeline
create_swarm(
    name="ETL Pipeline",
    topology="ring",
    agents=["aws-specialist", "spark-specialist", "snowflake-specialist"]
)
```

## Sessions

Create persistent, resumable workflows:

```python
# Create session
create_session(
    name="Data Migration",
    tasks=[
        {"description": "Extract from S3", "agent_name": "aws-specialist"},
        {"description": "Transform data", "agent_name": "spark-specialist"},
        {"description": "Load to Snowflake", "agent_name": "snowflake-specialist"}
    ]
)

# Pause/resume anytime
pause_session(session_id)
resume_session(session_id)
```

## Semantic Memory

Store and search by meaning:

```python
# Store with embedding
semantic_store("pattern1", "Use incremental loads for fact tables")

# Search by meaning (not just keywords)
semantic_search("how to load data efficiently")
```

Requires: `uv sync --extra semantic`

## Installation

```bash
# Clone
git clone https://github.com/yourusername/my-claude-squad.git
cd my-claude-squad

# Install
uv sync

# Optional: semantic memory support
uv sync --extra semantic

# Register with Claude Code
claude mcp add squad uv run squad-mcp
```

## Testing

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# With coverage
uv run pytest --cov=orchestrator --cov-report=html
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Architecture](docs/architecture.md)
- [Agent Catalog](docs/agents.md)
- [API Reference](docs/api-reference.md)
- [Developer Guide](docs/developer-guide.md)
- [Tutorials](docs/tutorials/)

## Environment Variables

```bash
# Optional: Langfuse observability
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com

# Optional: Custom path
SQUAD_ROOT=/path/to/my-claude-squad
```

## License

MIT
