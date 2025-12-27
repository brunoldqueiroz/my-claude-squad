# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A **pure MCP-based** orchestration system with 17 specialized AI agents for Data Engineering, AI Engineering, and Plugin Development. The `squad-orchestrator` decomposes complex tasks and coordinates agents in parallel.

**Architecture**: All functionality exposed via MCP tools and resources. No Claude Code plugin layer.

## Development Commands

```bash
uv sync                              # Install dependencies
uv sync --extra dev                  # Install with test dependencies
uv sync --extra semantic             # Install semantic memory (sentence-transformers)
uv run squad-mcp                     # Run MCP server directly
claude mcp add squad uv run squad-mcp # Register with Claude Code
```

### Testing

```bash
uv run pytest                        # Run all tests
uv run pytest tests/unit/            # Unit tests only
uv run pytest tests/unit/test_server.py -v  # Single module
uv run pytest -k "test_route"        # Tests matching pattern
uv run pytest -m "not slow"          # Exclude slow tests
uv run pytest --cov=orchestrator --cov-report=html  # Coverage
```

## Architecture

**Pure MCP design** - all coordination happens through the MCP server:

```
my-claude-squad/
├── orchestrator/           # MCP Server (Python/FastMCP)
│   ├── server.py           # 64 MCP tools + 6 MCP resources
│   ├── coordinator.py      # Task routing, decomposition
│   ├── agent_registry.py   # Loads agents/*.md
│   ├── memory.py           # DuckDB persistence (.swarm/)
│   ├── semantic_memory.py  # Vector embeddings for similarity search
│   ├── scheduler.py        # Task dependencies, CircuitBreaker
│   ├── topology.py         # Swarm topologies (hierarchical, mesh, ring, star)
│   ├── session.py          # Persistent, resumable sessions
│   ├── hooks.py            # Pre/post operation hooks
│   ├── agent_state.py      # Health tracking, heartbeats
│   ├── events.py           # EventBus with handlers
│   ├── metrics.py          # Counters, gauges, histograms
│   ├── paths.py            # Resource path resolution
│   └── types.py            # Pydantic models
│
├── agents/                 # 17 specialist agents (markdown)
│   └── *.md                # Served via squad://agents/{name}
│
├── skills/                 # 10 knowledge skills (markdown)
│   └── */SKILL.md          # Served via squad://skills/{name}
│
├── commands/               # 30 command templates (markdown)
│   └── */*.md              # Served via squad://commands/{cat}/{name}
│
└── .swarm/                 # Persistent state
    └── memory.duckdb       # DuckDB database
```

### MCP Resources

Resources serve content directly to Claude Code:

| URI Pattern | Content |
|-------------|---------|
| `squad://agents` | List all agents with metadata |
| `squad://agents/{name}` | Full agent markdown file |
| `squad://skills` | List all skills |
| `squad://skills/{name}` | Full skill markdown file |
| `squad://commands` | List all commands by category |
| `squad://commands/{cat}/{name}` | Full command markdown file |

### Path Resolution

The MCP server finds resources via `orchestrator/paths.py`:

1. `SQUAD_ROOT` environment variable (if set)
2. Project root detection (finds `pyproject.toml`)
3. Current working directory

## Swarm Topologies

Four coordination patterns for multi-agent workflows (`orchestrator/topology.py`):

| Topology | Pattern | Use Case |
|----------|---------|----------|
| **Hierarchical** | Queen-Worker delegation | Complex tasks requiring central coordination |
| **Mesh** | Peer-to-peer collaboration | Democratic decision-making, consensus |
| **Ring** | Sequential pipeline (A→B→C) | ETL workflows, data processing chains |
| **Star** | Hub-spoke coordination | Specialized workers with central routing |

### Creating a Swarm

```python
# Create a ring topology for data pipeline
create_swarm(
    name="ETL Pipeline",
    topology="ring",
    agents=["spark-specialist", "sql-specialist", "snowflake-specialist"]
)

# Create hierarchical with squad-orchestrator as coordinator
create_swarm(
    name="Project Team",
    topology="hierarchical",
    agents=["squad-orchestrator", "python-developer", "sql-specialist"],
    coordinator="squad-orchestrator"
)
```

### Workflow Execution

Use `create_swarm_workflow` to generate topology-aware tasks:
- **Ring**: Sequential tasks with dependencies
- **Hierarchical/Star**: Coordinator task for delegation
- **Mesh**: Parallel collaborative tasks

## Session Management

Sessions provide persistent, resumable multi-task workflows (`orchestrator/session.py`):

### Session Lifecycle

```
ACTIVE → PAUSED → ACTIVE → COMPLETED
       ↘ CANCELLED
       ↘ FAILED (if any task fails)
```

### Creating Sessions

```python
# Basic session with manual tasks
create_session(
    name="Data Pipeline",
    tasks=[
        {"description": "Extract from S3", "agent_name": "aws-specialist"},
        {"description": "Transform data", "agent_name": "spark-specialist"},
        {"description": "Load to Snowflake", "agent_name": "snowflake-specialist"},
    ]
)

# Session from swarm topology
create_session_from_swarm(
    name="ETL Workflow",
    swarm_id="abc123",  # Ring swarm
    task_description="Process daily transactions"
)
```

### Session Tools

- **Lifecycle**: `create_session`, `pause_session`, `resume_session`, `cancel_session`
- **Task Management**: `add_session_task`, `start_session_task`, `complete_session_task`
- **Progress**: `get_session_info`, `get_session_progress`, `list_sessions_tool`
- **Swarm Integration**: `create_session_from_swarm`

### Key Features

- **Persistence**: Sessions survive restarts via DuckDB
- **Progress Tracking**: Automatic completion detection
- **Swarm Integration**: Generate tasks from topology patterns
- **Pause/Resume**: Continue work later from last position

## Adding/Modifying Routing Rules

Task routing uses keyword matching in `coordinator.py:route_task()`. To add routing:

```python
routing_rules = {
    "snowflake": "snowflake-specialist",
    "your_keyword": "your-agent-name",  # Add here
}
```

Fallback: `registry.find_agents_by_trigger()` uses `<example>` tags in agent files.

## Agent Files Format

Each agent in `agents/` follows this structure:

```markdown
---
name: agent-name
description: |
  Description with <example> tags for trigger matching
model: sonnet | opus | haiku
color: colorname
---

[Agent prompt with three sections:]
1. Core expertise and patterns
2. RESEARCH-FIRST PROTOCOL section
3. CONTEXT RESILIENCE section
```

**Model assignments:**
- `opus` - `squad-orchestrator` only
- `sonnet` - All technical specialists (15 agents)
- `haiku` - `git-commit-writer` only

## Command Files Format

Commands in `commands/` use YAML frontmatter:

```markdown
---
description: Command description
argument-hint: <expected arguments>
allowed-tools:
  - Bash
  - Read
---
```

**Note**: Commands are currently markdown templates served via MCP resources. Future: Convert to MCP tools for direct invocation.

## Critical Rules

### Git Commit Writer
The `git-commit-writer` agent and `/commit` command must **NEVER** include:
- "Generated with Claude Code" / "Generated by AI"
- "Co-Authored-By: Claude" or any AI attribution
- Robot emojis or AI-related symbols

### Research-First Protocol
All agents verify knowledge before acting:
1. Context7 MCP (`mcp__upstash-context7-mcp__*`) for library docs
2. Exa MCP (`mcp__exa__get_code_context_exa`) for code examples
3. Declare uncertainty explicitly when unsure

## DuckDB Schema

Persistent state in `.swarm/memory.duckdb`:

| Table | Purpose |
|-------|---------|
| `memories` | Key-value with namespace |
| `memory_embeddings` | Vector embeddings for semantic search (JSON array) |
| `agent_runs` | Execution history (agent, task, status, tokens, result) |
| `task_log` | Task lifecycle |
| `agent_health` | Health scores, success/error counts, heartbeats |
| `agent_events` | Event log with JSON data |
| `sessions` | Persistent sessions with tasks (JSON), status, swarm_id |

## Environment Variables

Optional Langfuse observability (`.env`):
```
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

Optional path override:
```
SQUAD_ROOT=/path/to/my-claude-squad
```

## Task Decomposition Flow

The `decompose_task` tool delegates to Claude Code for semantic analysis:

```
1. Call decompose_task(task) → Returns prompt with:
   - Available agents and their specialties
   - Instructions for analysis
   - Expected JSON schema
   - Example decomposition

2. Claude Code analyzes the task and produces structured JSON

3. Call submit_decomposition(original_task, subtasks, ...) → Creates workflow:
   - Validates agents exist
   - Resolves dependency IDs
   - Adds tasks to scheduler
   - Returns ready_to_execute tasks
```

This approach uses Claude's semantic understanding instead of regex patterns.

## MCP Tools Summary

64 tools + 6 resources exposed via FastMCP:

**Orchestration Tools (23):**
- **Agent**: `list_agents`, `route_task`, `spawn_agent`, `decompose_task`, `submit_decomposition`
- **Memory**: `memory_store`, `memory_query`
- **Storage**: `get_storage_stats`, `cleanup_storage`
- **Scheduling**: `create_dependent_task`, `get_task_graph`, `get_ready_tasks`, `complete_scheduled_task`, `execute_workflow`, `clear_workflow`
- **Health**: `get_agent_health`, `set_agent_status`
- **Status**: `swarm_status`, `complete_run`, `get_health`, `get_metrics`
- **Events**: `get_events`, `emit_event`

**Topology Tools (6):**
- **Swarm Management**: `create_swarm`, `list_swarms`, `get_swarm`, `delete_swarm`
- **Coordination**: `get_swarm_delegation`, `create_swarm_workflow`

**Session Tools (12):**
- **Lifecycle**: `create_session`, `create_session_from_swarm`, `pause_session`, `resume_session`, `cancel_session`, `delete_session_tool`
- **Tasks**: `add_session_task`, `start_session_task`, `complete_session_task`
- **Status**: `get_session_info`, `get_session_progress`, `list_sessions_tool`

**Hooks Tools (8):**
- **Management**: `list_hooks`, `get_hook_info`, `enable_hook`, `disable_hook`, `unregister_hook`
- **Status**: `get_hooks_stats`, `clear_hooks`, `list_hook_types`

**Semantic Memory Tools (6):**
- **Store**: `semantic_store`, `semantic_store_batch`
- **Search**: `semantic_search`
- **Management**: `semantic_stats`, `semantic_reindex`, `semantic_delete`

**Command Tools (9):**
- **Data Engineering**: `create_pipeline`, `analyze_query`, `analyze_data`
- **DevOps**: `create_dockerfile`, `create_k8s_manifest`
- **AI Engineering**: `scaffold_rag`, `scaffold_mcp_server`
- **Documentation**: `generate_commit_message`
- **Research**: `lookup_docs`

**Resources (6):**
- `squad://agents`, `squad://agents/{name}`
- `squad://skills`, `squad://skills/{name}`
- `squad://commands`, `squad://commands/{category}/{name}`

## External MCP Tools for Research

- `mcp__upstash-context7-mcp__resolve-library-id` / `get-library-docs`
- `mcp__exa__get_code_context_exa` / `web_search_exa`

## Hooks System

Hooks are pre/post operation interceptors that can modify data or abort operations.

**Hook Types (13):**
- **Task**: `pre_task`, `post_task` - Before/after task execution
- **Agent**: `pre_spawn`, `post_spawn`, `on_agent_error` - Agent lifecycle
- **Session**: `pre_session`, `post_session`, `on_session_pause`, `on_session_resume`
- **Routing**: `pre_route`, `post_route` - Before/after routing decisions
- **Memory**: `pre_memory_store`, `post_memory_query` - Memory operations

**Key Features:**
- Hooks run in priority order (lower = earlier)
- Can modify input data before operations
- Can abort operations via `HookAbortError`
- Support for both sync and async handlers
- Enable/disable without unregistering

**Usage Pattern:**
```python
from orchestrator.hooks import HooksManager, HookType, HookContext, HookAbortError

hooks = get_hooks_manager()

def validate_task(ctx: HookContext) -> dict | None:
    if not ctx.data.get("description"):
        raise HookAbortError("Task must have a description")
    return None  # No modifications

hooks.register("validate-task", HookType.PRE_TASK, validate_task, priority=10)
```

## Semantic Memory

Semantic memory provides vector-based similarity search using sentence-transformers (`orchestrator/semantic_memory.py`).

### Installation

```bash
uv sync --extra semantic  # Install sentence-transformers + numpy
```

### Usage

Store memories with embeddings:
```python
semantic_store("doc1", "Python is a programming language", namespace="docs")
semantic_store("doc2", "JavaScript runs in browsers", namespace="docs")
```

Search by meaning (not just keywords):
```python
results = semantic_search("coding languages", namespace="docs", top_k=5)
# Returns most similar documents even without exact word matches
```

### Key Features

- **Graceful Degradation**: Works without sentence-transformers installed (returns helpful error)
- **Lazy Loading**: Model loaded only when first used (~80MB download)
- **Batch Operations**: `semantic_store_batch` for efficient bulk storage
- **Namespace Support**: Organize memories by domain
- **Reindexing**: `semantic_reindex` regenerates all embeddings (after model change)

### Technical Details

- **Model**: all-MiniLM-L6-v2 (384 dimensions, ~80MB)
- **Storage**: Embeddings stored as JSON arrays in DuckDB
- **Similarity**: Cosine similarity (0-1, higher = more similar)
- **Search**: In-memory similarity calculation (scales to ~10K memories)

### Tools

| Tool | Description |
|------|-------------|
| `semantic_store` | Store memory with embedding |
| `semantic_store_batch` | Batch store for efficiency |
| `semantic_search` | Search by semantic similarity |
| `semantic_stats` | Get statistics (counts, model info) |
| `semantic_reindex` | Regenerate all embeddings |
| `semantic_delete` | Remove memory and embedding |

## Roadmap

All planned enhancements complete:
- [x] Swarm topologies (hierarchical, mesh, ring, star) - 6 tools added
- [x] Session management (persistent/resumable) - 12 tools added
- [x] Hooks system (pre/post operation) - 8 tools added
- [x] Commands → MCP tools conversion (9 tools added)
- [x] Semantic memory search - 6 tools added
