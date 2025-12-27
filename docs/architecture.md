# Architecture

This document describes the internal architecture of my-claude-squad, a pure MCP-based multi-agent orchestration system.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Claude Code                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      MCP Client                              ││
│  └───────────────────────────┬─────────────────────────────────┘│
└──────────────────────────────┼──────────────────────────────────┘
                               │ stdio
┌──────────────────────────────┼──────────────────────────────────┐
│                         MCP Server                               │
│  ┌───────────────────────────┴─────────────────────────────────┐│
│  │                     FastMCP (server.py)                      ││
│  │              64 Tools + 6 Resources                          ││
│  └───────┬───────────┬───────────┬───────────┬─────────────────┘│
│          │           │           │           │                   │
│  ┌───────┴───┐ ┌─────┴─────┐ ┌───┴───┐ ┌─────┴─────┐            │
│  │Coordinator│ │ Scheduler │ │Session│ │ Topology  │            │
│  │           │ │           │ │Manager│ │  Manager  │            │
│  └─────┬─────┘ └─────┬─────┘ └───┬───┘ └─────┬─────┘            │
│        │             │           │           │                   │
│  ┌─────┴─────────────┴───────────┴───────────┴─────┐            │
│  │                  SwarmMemory (DuckDB)            │            │
│  │    .swarm/memory.duckdb                          │            │
│  └──────────────────────────────────────────────────┘            │
│                                                                   │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Agent Registry │  │ Hooks Manager│  │  Event Bus   │          │
│  │  agents/*.md   │  │              │  │              │          │
│  └────────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

The orchestrator consists of 19 Python modules:

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `server.py` | ~3000 | FastMCP entry point, 64 tools, 6 resources |
| `coordinator.py` | ~450 | Task routing, agent matching, lifecycle |
| `agent_registry.py` | ~300 | Load agents/*.md, extract triggers |
| `types.py` | ~340 | Pydantic models, enums |
| `memory.py` | ~200 | DuckDB persistence layer |
| `scheduler.py` | ~200 | Task dependencies, circuit breaker |
| `topology.py` | ~200 | Swarm topologies (hierarchical, mesh, ring, star) |
| `session.py` | ~200 | Persistent, resumable workflows |
| `hooks.py` | ~150 | Pre/post operation interceptors |
| `agent_state.py` | ~150 | Health tracking, heartbeats |
| `events.py` | ~150 | Pub/sub event bus |
| `semantic_memory.py` | ~150 | Vector embeddings for similarity search |
| `metrics.py` | ~100 | Counters, gauges, histograms |
| `command_tools.py` | ~100 | Command generation helpers |
| `tracing.py` | ~80 | Langfuse observability |
| `paths.py` | ~50 | Resource path resolution |
| `config.py` | ~30 | Environment configuration |
| `retry.py` | ~30 | Exponential backoff |

## Core Components

### 1. Coordinator

The coordinator handles task routing and lifecycle management.

**Task Routing Flow:**
```
Task Description
     │
     ▼
┌────────────────┐
│ Keyword Rules  │ ─── 80+ rules like "snowflake" → snowflake-specialist
└───────┬────────┘
        │ (no match)
        ▼
┌────────────────┐
│ Agent Registry │ ─── Trigger extraction from agent files
└───────┬────────┘
        │ (no match)
        ▼
┌────────────────┐
│ Default Agent  │ ─── squad-orchestrator
└────────────────┘
```

**Key Methods:**
- `route_task(description)` - Match task to best agent
- `create_task(description, agent_name)` - Create task with routing
- `start_task(task_id)` - Begin execution, log to database
- `complete_task(task_id, result)` - Finalize with Langfuse trace

### 2. Agent Registry

Loads agent definitions from markdown files and extracts routing triggers.

**Trigger Extraction Sources:**
1. `<example>` tags in descriptions
2. Bold text (`**keyword**`)
3. Section headings (`##`, `###`)
4. Table first columns
5. Python imports
6. Technology patterns (PySpark, Delta Lake, etc.)
7. Known technology keywords

### 3. Task Scheduler

Manages task dependencies with a directed acyclic graph (DAG).

```
Task A ───┐
          ├──▶ Task C ───▶ Task D
Task B ───┘
```

**Features:**
- Topological sort for execution order
- Circuit breaker per agent (CLOSED → OPEN → HALF_OPEN)
- Parallel execution of independent tasks
- Dependency validation (cycle detection)

### 4. Topology Manager

Coordinates multi-agent swarms with different communication patterns.

| Topology | Pattern | Use Case |
|----------|---------|----------|
| **Hierarchical** | Queen-Worker | Complex tasks with central coordination |
| **Mesh** | Peer-to-Peer | Democratic decision-making |
| **Ring** | Pipeline A→B→C | ETL workflows, sequential processing |
| **Star** | Hub-Spoke | Specialized workers with central routing |

### 5. Session Manager

Provides persistent, resumable multi-task workflows.

**Session Lifecycle:**
```
ACTIVE ──▶ PAUSED ──▶ ACTIVE ──▶ COMPLETED
   │
   ├──────▶ CANCELLED
   │
   └──────▶ FAILED (if task fails)
```

**Features:**
- Survives restarts (DuckDB persistence)
- Progress tracking (percentage, current task)
- Swarm integration for topology-aware execution

### 6. Hooks Manager

Intercepts operations before/after execution.

**Hook Types (13):**
| Category | Hook Types |
|----------|------------|
| Task | `pre_task`, `post_task` |
| Agent | `pre_spawn`, `post_spawn`, `on_agent_error` |
| Session | `pre_session`, `post_session`, `on_session_pause`, `on_session_resume` |
| Routing | `pre_route`, `post_route` |
| Memory | `pre_memory_store`, `post_memory_query` |

**Capabilities:**
- Modify input data before operations
- Abort operations via `HookAbortError`
- Priority-based execution order
- Enable/disable without unregistering

### 7. Event Bus

Pub/sub notification system for agent lifecycle events.

**Event Types:**
- `heartbeat` - Periodic agent liveness
- `status_change` - Agent status updates
- `task_start` - Task execution begins
- `task_complete` - Task finishes successfully
- `task_failed` - Task fails
- `error` - General errors

**Features:**
- Sync and async handlers
- Circular history buffer (1000 events max)
- Type-specific and global handlers

### 8. Semantic Memory

Vector-based similarity search using sentence-transformers.

**Model:** all-MiniLM-L6-v2 (384 dimensions, ~80MB)

```python
# Store with embedding
semantic_store("doc1", "Python is a programming language")

# Search by meaning (not just keywords)
results = semantic_search("coding languages", top_k=5)
```

**Features:**
- Graceful degradation if unavailable
- Lazy model loading
- Batch operations for efficiency
- Cosine similarity (0-1 scale)

## Database Schema

The DuckDB database (`.swarm/memory.duckdb`) contains 7 tables:

```sql
-- Key-value store with namespaces
CREATE TABLE memories (
    key VARCHAR PRIMARY KEY,
    value VARCHAR,
    namespace VARCHAR DEFAULT 'default',
    metadata JSON,
    created_at TIMESTAMP
);

-- Vector embeddings for semantic search
CREATE TABLE memory_embeddings (
    key VARCHAR PRIMARY KEY,
    embedding JSON,  -- 384-dim float array
    namespace VARCHAR,
    created_at TIMESTAMP
);

-- Execution history
CREATE TABLE agent_runs (
    id VARCHAR PRIMARY KEY,
    agent_name VARCHAR,
    task VARCHAR,
    status VARCHAR,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    tokens_used INTEGER,
    result VARCHAR
);

-- Task tracking
CREATE TABLE task_log (
    id VARCHAR PRIMARY KEY,
    description VARCHAR,
    agent_name VARCHAR,
    status VARCHAR,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    result VARCHAR
);

-- Runtime health metrics
CREATE TABLE agent_health (
    agent_name VARCHAR PRIMARY KEY,
    status VARCHAR,
    health_score REAL,
    last_heartbeat TIMESTAMP,
    current_task_id VARCHAR,
    error_count INTEGER,
    success_count INTEGER,
    total_execution_time_ms REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Event audit trail
CREATE TABLE agent_events (
    id VARCHAR PRIMARY KEY,
    agent_name VARCHAR,
    event_type VARCHAR,
    event_data JSON,
    timestamp TIMESTAMP
);

-- Persistent sessions
CREATE TABLE sessions (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    description VARCHAR,
    status VARCHAR,
    swarm_id VARCHAR,
    tasks JSON,
    current_task_index INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    paused_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSON
);
```

## Data Flow

### Task Execution Flow

```
1. MCP Tool Call (spawn_agent or route_task)
        │
        ▼
2. Coordinator.create_task(description)
   ├── route_task() if no agent specified
   ├── Create Task object (PENDING)
   └── Cache in _active_tasks
        │
        ▼
3. Coordinator.start_task(task_id)
   ├── Update status → IN_PROGRESS
   ├── memory.log_run_start() → agent_runs
   ├── AgentStateManager.record_task_start()
   └── Return AgentRun for tracing
        │
        ▼
4. Agent executes (Claude Code reads agent/*.md)
        │
        ▼
5. complete_run(task_id, result, success)
   ├── Coordinator.complete_task()
   │   ├── Update status → COMPLETED/FAILED
   │   ├── memory.log_run_complete()
   │   └── Langfuse span update
   └── AgentStateManager.record_task_complete()
```

### Task Decomposition Flow

```
1. decompose_task(complex_task)
   │
   ▼
   Returns instruction prompt with:
   ├── Available agents + specialties
   ├── JSON response schema
   └── Example decomposition
   │
   ▼
2. Claude Code analyzes and produces JSON
   │
   ▼
3. submit_decomposition(subtasks, depends_on, parallel_groups)
   ├── Validate agents exist
   ├── Create Task objects for each subtask
   ├── Map submitted IDs → generated UUIDs
   ├── Resolve dependency IDs
   ├── TaskScheduler.add_task() for each
   └── Return ready_to_execute tasks
```

## Design Patterns

### 1. Singleton with Lazy Initialization

All core managers are singletons created on first tool call:

```python
_coordinator: Coordinator | None = None

def get_coordinator() -> Coordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = Coordinator(agents_dir, memory)
    return _coordinator
```

### 2. Pure MCP Design

No traditional API layer - all coordination through MCP tools:
- Tools for operations (64 total)
- Resources for documentation (6 total)

### 3. Event-Driven Architecture

Components communicate via EventBus:
- AgentStateManager emits events on state changes
- Subscribers react asynchronously
- Full audit trail in database

### 4. Circuit Breaker Pattern

Fault tolerance for agent failures:
```
CLOSED (normal) ─────▶ OPEN (failing) ─────▶ HALF_OPEN (testing)
       ▲                                              │
       └──────────────────────────────────────────────┘
                    (success: reset)
```

### 5. Two-Phase Decomposition

Complex tasks use semantic decomposition:
1. `decompose_task()` returns prompt with schema
2. Claude Code analyzes and reasons about task
3. `submit_decomposition()` validates and schedules

This leverages Claude's semantic understanding rather than regex patterns.

## External Integrations

### Langfuse (Optional)

Observability integration for tracing:

```bash
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

Traces include:
- Task creation and routing
- Agent execution spans
- Token usage
- Success/failure status

### External MCP Tools for Research

Agents use these MCPs for documentation lookup:
- `mcp__upstash-context7-mcp__resolve-library-id`
- `mcp__upstash-context7-mcp__get-library-docs`
- `mcp__exa__get_code_context_exa`
- `mcp__exa__web_search_exa`

## Directory Structure

```
my-claude-squad/
├── orchestrator/           # MCP Server (Python/FastMCP)
│   ├── server.py           # 64 MCP tools + 6 MCP resources
│   ├── coordinator.py      # Task routing, decomposition
│   ├── agent_registry.py   # Loads agents/*.md
│   ├── memory.py           # DuckDB persistence
│   ├── semantic_memory.py  # Vector embeddings
│   ├── scheduler.py        # Task dependencies, CircuitBreaker
│   ├── topology.py         # Swarm topologies
│   ├── session.py          # Persistent sessions
│   ├── hooks.py            # Pre/post hooks
│   ├── agent_state.py      # Health tracking
│   ├── events.py           # EventBus
│   ├── metrics.py          # Instrumentation
│   ├── tracing.py          # Langfuse
│   ├── paths.py            # Resource paths
│   ├── types.py            # Pydantic models
│   └── command_tools.py    # Command helpers
│
├── agents/                 # 17 specialist agents (markdown)
│   ├── squad-orchestrator.md
│   ├── python-developer.md
│   ├── sql-specialist.md
│   └── ... (14 more)
│
├── skills/                 # 10 knowledge skills
│   ├── data-pipeline-patterns/SKILL.md
│   ├── sql-optimization/SKILL.md
│   └── ... (8 more)
│
├── commands/               # 30 command templates
│   ├── orchestration/
│   ├── data-engineering/
│   ├── documentation/
│   └── ... (more categories)
│
├── tests/                  # Test suite (400+ tests)
│   ├── unit/
│   └── integration/
│
└── .swarm/                 # Persistent state
    └── memory.duckdb       # DuckDB database
```
