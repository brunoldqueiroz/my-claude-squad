# API Reference

Complete reference for all 64 MCP tools and 6 MCP resources.

## Quick Reference

| Category | Tool Count | Description |
|----------|------------|-------------|
| [Agent Management](#agent-management) | 5 | List, route, spawn, decompose agents |
| [Memory](#memory) | 2 | Key-value storage |
| [Storage](#storage) | 2 | Database management |
| [Health & Status](#health--status) | 6 | System and agent health |
| [Task Scheduling](#task-scheduling) | 6 | Dependencies and workflows |
| [Events](#events) | 2 | Event bus |
| [Swarm Topology](#swarm-topology) | 6 | Multi-agent coordination |
| [Sessions](#sessions) | 12 | Persistent workflows |
| [Hooks](#hooks) | 8 | Operation interceptors |
| [Semantic Memory](#semantic-memory) | 6 | Vector search |
| [Commands](#commands) | 9 | Utility generators |
| **Total** | **64** | |

---

## Agent Management

### list_agents

Lists all available agents with metadata.

**Parameters:** None

**Returns:**
```json
{
  "total": 17,
  "agents": [
    {
      "name": "python-developer",
      "description": "...",
      "model": "sonnet",
      "color": "green",
      "triggers": ["python", "pandas", "pytest"]
    }
  ]
}
```

### route_task

Routes a task to the best-matching agent.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task | string | Yes | Task description |

**Returns:**
```json
{
  "success": true,
  "recommended_agent": "snowflake-specialist",
  "agent_model": "sonnet",
  "confidence": "high"
}
```

### spawn_agent

Creates and starts a task for a specific agent.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent_name | string | Yes | Agent to spawn |
| task | string | Yes | Task description |

**Returns:**
```json
{
  "success": true,
  "task_id": "abc123",
  "agent": "python-developer",
  "status": "pending"
}
```

### decompose_task

Returns a decomposition prompt for complex tasks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task | string | Yes | Complex task to decompose |

**Returns:**
```json
{
  "action": "analyze_and_decompose",
  "task": "...",
  "instructions": "...",
  "available_agents": [...],
  "response_schema": {...}
}
```

### submit_decomposition

Processes Claude's task decomposition.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| original_task | string | Yes | Original task |
| subtasks | array | Yes | List of subtask definitions |
| parallel_groups | array | No | Groups of parallel task IDs |
| execution_order | array | No | Ordered task IDs |
| analysis | string | No | Claude's analysis |
| auto_schedule | boolean | No | Add to scheduler (default: true) |

**Returns:**
```json
{
  "success": true,
  "subtask_count": 5,
  "id_mapping": {"t1": "abc123", "t2": "def456"},
  "ready_to_execute": ["abc123", "def456"]
}
```

---

## Memory

### memory_store

Stores key-value pair in persistent memory.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| key | string | Yes | Unique key |
| value | string | Yes | Value to store |
| namespace | string | No | Namespace (default: "default") |

**Returns:**
```json
{
  "success": true,
  "key": "my-key",
  "namespace": "default"
}
```

### memory_query

Queries memory by pattern.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| pattern | string | Yes | SQL LIKE pattern |
| namespace | string | No | Namespace filter |
| limit | integer | No | Max results (default: 10) |

**Returns:**
```json
{
  "success": true,
  "count": 3,
  "memories": [
    {"key": "...", "value": "...", "namespace": "..."}
  ]
}
```

---

## Storage

### get_storage_stats

Returns database statistics.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "tables": {
    "memories": {"count": 50},
    "agent_runs": {"count": 100},
    "sessions": {"count": 5}
  },
  "database_size_mb": 2.5
}
```

### cleanup_storage

Deletes old data with configurable retention.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| runs_days | integer | No | Delete runs older than (default: 30) |
| events_days | integer | No | Delete events older than (default: 7) |
| tasks_days | integer | No | Delete tasks older than (default: 30) |
| memories_days | integer | No | Delete memories older than (default: null = keep all) |
| vacuum | boolean | No | Run VACUUM after (default: true) |

**Returns:**
```json
{
  "success": true,
  "deleted": {
    "agent_runs": 50,
    "agent_events": 200
  }
}
```

---

## Health & Status

### swarm_status

Returns current swarm overview.

**Parameters:** None

**Returns:**
```json
{
  "agent_count": 17,
  "active_tasks": 2,
  "total_runs": 150,
  "success_rate": 0.95
}
```

### complete_run

Marks a task as completed.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | Yes | Task to complete |
| result | string | No | Result text |
| success | boolean | No | Success status (default: true) |
| tokens_used | integer | No | Tokens consumed (default: 0) |

**Returns:**
```json
{
  "success": true,
  "task_id": "abc123",
  "status": "completed"
}
```

### get_health

Returns system health status.

**Parameters:** None

**Returns:**
```json
{
  "status": "healthy",
  "components": {
    "database": "ok",
    "langfuse": "connected"
  },
  "agent_count": 17
}
```

### get_metrics

Returns instrumentation metrics.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| reset | boolean | No | Reset after returning (default: false) |

**Returns:**
```json
{
  "counters": {"tasks_created": 50},
  "gauges": {"active_tasks": 2},
  "histograms": {"task_duration_ms": {...}}
}
```

### get_agent_health

Returns health status for agents.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent_name | string | No | Specific agent (default: all) |

**Returns:**
```json
{
  "agents": [{
    "name": "python-developer",
    "status": "idle",
    "health_score": 0.95,
    "success_rate": 0.98,
    "error_count": 1
  }]
}
```

### set_agent_status

Sets agent status manually.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent_name | string | Yes | Agent name |
| status | string | Yes | Status: idle, busy, paused, error, offline |
| reason | string | No | Reason for status change |

**Returns:**
```json
{
  "success": true,
  "agent": "python-developer",
  "status": "paused"
}
```

---

## Task Scheduling

### create_dependent_task

Creates a task with dependencies.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task | string | Yes | Task description |
| depends_on | array | No | List of task IDs |
| agent_name | string | No | Agent to assign |
| priority | integer | No | Priority 1-10 (default: 5) |

**Returns:**
```json
{
  "success": true,
  "task_id": "abc123",
  "depends_on": ["def456"],
  "is_ready": false
}
```

### get_task_graph

Returns the task dependency graph.

**Parameters:** None

**Returns:**
```json
{
  "tasks": [...],
  "dependencies": {"abc123": ["def456"]},
  "circuit_breakers": {...}
}
```

### get_ready_tasks

Returns tasks ready for execution.

**Parameters:** None

**Returns:**
```json
{
  "count": 3,
  "tasks": [
    {"id": "abc123", "description": "...", "agent": "..."}
  ]
}
```

### complete_scheduled_task

Marks a scheduled task complete.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | string | Yes | Task to complete |
| success | boolean | No | Success status (default: true) |
| result | string | No | Result text |

**Returns:**
```json
{
  "success": true,
  "newly_ready_tasks": 2,
  "ready_task_ids": ["ghi789", "jkl012"]
}
```

### execute_workflow

Creates multiple tasks with dependencies.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| tasks | array | Yes | Task definitions with depends_on |

**Returns:**
```json
{
  "success": true,
  "created": 5,
  "ready": ["task1", "task2"]
}
```

### clear_workflow

Removes all scheduled tasks.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "cleared": 10
}
```

---

## Events

### get_events

Returns recent events.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| limit | integer | No | Max events (default: 50) |
| event_type | string | No | Filter by type |
| agent_name | string | No | Filter by agent |

**Returns:**
```json
{
  "events": [{
    "id": "...",
    "agent_name": "...",
    "event_type": "task_complete",
    "event_data": {...},
    "timestamp": "..."
  }]
}
```

### emit_event

Emits a custom event.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent_name | string | Yes | Emitting agent |
| event_type | string | Yes | Event type |
| data | object | No | Event payload |

**Returns:**
```json
{
  "success": true,
  "event_id": "abc123"
}
```

---

## Swarm Topology

### create_swarm

Creates a multi-agent swarm.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Swarm name |
| topology | string | Yes | hierarchical, mesh, ring, star |
| agents | array | Yes | Agent names |
| coordinator | string | No | Coordinator agent (required for hierarchical/star) |

**Returns:**
```json
{
  "success": true,
  "swarm_id": "abc123",
  "topology": "ring",
  "members": [...]
}
```

### list_swarms

Lists all swarms.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| active_only | boolean | No | Filter active only (default: true) |

**Returns:**
```json
{
  "swarms": [{
    "id": "...",
    "name": "...",
    "topology": "ring",
    "member_count": 3
  }]
}
```

### get_swarm

Returns detailed swarm information.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| swarm_id | string | Yes | Swarm ID |

**Returns:**
```json
{
  "id": "...",
  "name": "...",
  "topology": "ring",
  "members": [...],
  "active": true
}
```

### delete_swarm

Deletes or deactivates a swarm.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| swarm_id | string | Yes | Swarm ID |
| force | boolean | No | Permanently delete (default: false) |

**Returns:**
```json
{
  "success": true,
  "action": "deactivated"
}
```

### get_swarm_delegation

Returns delegation target for a task.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| swarm_id | string | Yes | Swarm ID |
| from_agent | string | Yes | Delegating agent |
| task_description | string | Yes | Task being delegated |

**Returns:**
```json
{
  "target_agent": "sql-specialist",
  "routing": "ring_next"
}
```

### create_swarm_workflow

Creates topology-aware workflow tasks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| swarm_id | string | Yes | Swarm ID |
| task_description | string | Yes | Overall task |

**Returns:**
```json
{
  "success": true,
  "tasks_created": 3,
  "topology_pattern": "sequential"
}
```

---

## Sessions

### create_session

Creates a persistent session.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Session name |
| tasks | array | No | Initial tasks |
| description | string | No | Description |
| swarm_id | string | No | Associated swarm |

**Returns:**
```json
{
  "success": true,
  "session_id": "abc123",
  "status": "active"
}
```

### create_session_from_swarm

Creates session with swarm-generated tasks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Session name |
| swarm_id | string | Yes | Swarm ID |
| task_description | string | Yes | Task description |
| description | string | No | Session description |

**Returns:**
```json
{
  "success": true,
  "session_id": "abc123",
  "task_count": 3
}
```

### get_session_info

Returns session details.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |

**Returns:**
```json
{
  "id": "...",
  "name": "...",
  "status": "active",
  "tasks": [...],
  "progress": 0.33
}
```

### list_sessions_tool

Lists sessions with filtering.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| status | string | No | Filter by status |
| active_only | boolean | No | Active/paused only (default: false) |
| limit | integer | No | Max results (default: 50) |

**Returns:**
```json
{
  "sessions": [...],
  "count": 5
}
```

### pause_session

Pauses an active session.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |

**Returns:**
```json
{
  "success": true,
  "status": "paused"
}
```

### resume_session

Resumes a paused session.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |

**Returns:**
```json
{
  "success": true,
  "status": "active",
  "next_task": {...}
}
```

### cancel_session

Cancels a session (cannot be resumed).

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |

**Returns:**
```json
{
  "success": true,
  "status": "cancelled"
}
```

### add_session_task

Adds a task to an existing session.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |
| description | string | Yes | Task description |
| agent_name | string | No | Agent to assign |

**Returns:**
```json
{
  "success": true,
  "task_id": "task_5"
}
```

### start_session_task

Marks a session task as in-progress.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |
| task_id | string | Yes | Task ID |

**Returns:**
```json
{
  "success": true,
  "task_status": "in_progress"
}
```

### complete_session_task

Completes a session task.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |
| task_id | string | Yes | Task ID |
| result | string | No | Result text |
| success | boolean | No | Success status (default: true) |

**Returns:**
```json
{
  "success": true,
  "session_status": "active",
  "all_complete": false
}
```

### get_session_progress

Returns detailed progress.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |

**Returns:**
```json
{
  "total": 5,
  "completed": 2,
  "in_progress": 1,
  "pending": 2,
  "progress": 0.4,
  "current_task": {...}
}
```

### delete_session_tool

Deletes a session permanently.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Session ID |

**Returns:**
```json
{
  "success": true
}
```

---

## Hooks

### list_hooks

Lists registered hooks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| hook_type | string | No | Filter by type |
| enabled_only | boolean | No | Filter enabled (default: false) |

**Returns:**
```json
{
  "hooks": [{
    "name": "validate-task",
    "type": "pre_task",
    "priority": 10,
    "enabled": true
  }]
}
```

### get_hook_info

Returns hook details.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Hook name |

**Returns:**
```json
{
  "name": "...",
  "type": "pre_task",
  "priority": 10,
  "enabled": true,
  "call_count": 50,
  "error_count": 0
}
```

### enable_hook

Enables a disabled hook.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Hook name |

**Returns:**
```json
{
  "success": true,
  "enabled": true
}
```

### disable_hook

Disables a hook without removing.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Hook name |

**Returns:**
```json
{
  "success": true,
  "enabled": false
}
```

### unregister_hook

Permanently removes a hook.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Hook name |

**Returns:**
```json
{
  "success": true
}
```

### get_hooks_stats

Returns hooks system statistics.

**Parameters:** None

**Returns:**
```json
{
  "total_hooks": 5,
  "enabled": 4,
  "disabled": 1,
  "total_calls": 200,
  "total_errors": 2
}
```

### clear_hooks

Clears registered hooks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| hook_type | string | No | Type to clear (default: all) |

**Returns:**
```json
{
  "cleared": 5
}
```

### list_hook_types

Lists available hook types.

**Parameters:** None

**Returns:**
```json
{
  "hook_types": [
    {"type": "pre_task", "description": "Before task execution"},
    {"type": "post_task", "description": "After task execution"}
  ]
}
```

---

## Semantic Memory

### semantic_store

Stores memory with vector embedding.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| key | string | Yes | Unique key |
| value | string | Yes | Value to store and embed |
| namespace | string | No | Namespace (default: "default") |
| metadata | object | No | Additional metadata |

**Returns:**
```json
{
  "success": true,
  "key": "...",
  "embedded": true
}
```

### semantic_search

Searches by semantic similarity.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | Yes | Search query |
| namespace | string | No | Namespace filter |
| top_k | integer | No | Max results (default: 5) |
| min_similarity | float | No | Minimum similarity 0-1 (default: 0) |

**Returns:**
```json
{
  "results": [{
    "key": "...",
    "value": "...",
    "similarity": 0.85
  }]
}
```

### semantic_store_batch

Batch stores multiple memories.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| items | array | Yes | List of {key, value, metadata} |
| namespace | string | No | Namespace (default: "default") |

**Returns:**
```json
{
  "success": true,
  "stored": 10,
  "embedded": 10
}
```

### semantic_stats

Returns semantic memory statistics.

**Parameters:** None

**Returns:**
```json
{
  "total_memories": 100,
  "with_embeddings": 95,
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384,
  "namespaces": {"default": 50, "docs": 45}
}
```

### semantic_reindex

Regenerates all embeddings.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "reindexed": 95
}
```

### semantic_delete

Deletes memory and embedding.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| key | string | Yes | Key to delete |

**Returns:**
```json
{
  "success": true
}
```

---

## Commands

### create_pipeline

Generates data pipeline boilerplate.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| source | string | Yes | api, s3, postgresql, mysql, files |
| target | string | Yes | snowflake, redshift, s3, postgresql |
| name | string | No | Pipeline name (default: "pipeline") |
| incremental | boolean | No | Incremental loading |
| schedule | string | No | Cron expression |
| with_tests | boolean | No | Include tests (default: true) |

### analyze_query

Analyzes SQL for optimization.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sql | string | Yes | SQL query to analyze |

### analyze_data

Profiles a data file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| path | string | Yes | Path to CSV, Parquet, or JSON |
| sample_size | integer | No | Sample rows (default: 1000) |

### create_dockerfile

Generates optimized Dockerfile.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| project_type | string | No | python, node, java (default: "python") |
| optimize_for | string | No | size, speed (default: "size") |
| python_version | string | No | Python version (default: "3.11") |
| include_dev | boolean | No | Include dev tools |

### create_k8s_manifest

Generates Kubernetes manifests.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| app_name | string | Yes | Application name |
| replicas | integer | No | Replicas (default: 2) |
| port | integer | No | Container port (default: 8000) |
| image | string | No | Docker image (default: "app:latest") |
| resources_preset | string | No | small, medium, large (default: "small") |

### scaffold_rag

Generates RAG application structure.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Application name |
| vectordb | string | No | chromadb, qdrant, weaviate, pgvector |
| framework | string | No | langchain, llamaindex |
| embedding_model | string | No | Model name |

### scaffold_mcp_server

Generates MCP server template.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Server name |
| tools | array | Yes | Tool names to create |
| transport | string | No | stdio, http (default: "stdio") |

### generate_commit_message

Generates conventional commit message.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| changes_summary | string | Yes | Description of changes |
| change_type | string | No | feat, fix, docs, etc. (default: "feat") |
| scope | string | No | Commit scope |
| breaking | boolean | No | Breaking change |

**Note:** Never includes AI attribution.

### lookup_docs

Returns documentation lookup instructions.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| library | string | Yes | Library name |
| topic | string | No | Specific topic |

---

## MCP Resources

### squad://agents

Lists all agents with metadata.

**Response:** YAML list of agents

### squad://agents/{agent_name}

Returns full agent markdown file.

**Parameters:** `agent_name` - Agent name (e.g., "python-developer")

**Response:** Markdown content

### squad://skills

Lists all skills.

**Response:** YAML list of skills

### squad://skills/{skill_name}

Returns full skill SKILL.md file.

**Parameters:** `skill_name` - Skill name (e.g., "data-pipeline-patterns")

**Response:** Markdown content

### squad://commands

Lists all commands by category.

**Response:** YAML list of commands

### squad://commands/{category}/{command_name}

Returns full command markdown file.

**Parameters:**
- `category` - Command category
- `command_name` - Command name

**Response:** Markdown content

---

## Error Responses

All tools return errors in this format:

```json
{
  "success": false,
  "error": "Descriptive error message",
  "hint": "Suggested remediation"
}
```

Common error types:
- `AgentNotFoundError` - Unknown agent name
- `TaskNotFoundError` - Unknown task ID
- `SessionNotFoundError` - Unknown session ID
- `SwarmNotFoundError` - Unknown swarm ID
- `HookAbortError` - Operation aborted by hook
- `CircuitBreakerOpenError` - Agent circuit breaker is open
