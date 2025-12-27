"""FastMCP server for my-claude-squad orchestration."""

from typing import Any

from fastmcp import FastMCP

from orchestrator.agent_state import AgentStateManager
from orchestrator.coordinator import Coordinator
from orchestrator.events import get_event_bus, create_event
from orchestrator.metrics import get_metrics_collector
from orchestrator.paths import get_agents_dir, get_skills_dir, get_commands_dir
from orchestrator.scheduler import TaskScheduler
from orchestrator.tracing import get_langfuse, is_enabled as langfuse_enabled
from orchestrator.types import (
    AgentEventType,
    AgentStatus,
    DecompositionResult,
    ExecutionMode,
    SessionStatus,
    Subtask,
    Task,
    TaskStatus,
    TopologyType,
)
from orchestrator.topology import TopologyManager
from orchestrator.session import SessionManager
from orchestrator.hooks import HooksManager, HookType, HookAbortError, get_hooks_manager
from orchestrator.semantic_memory import (
    SemanticMemory,
    SemanticSearchResult,
    is_available as semantic_is_available,
    get_semantic_memory,
)
from orchestrator import command_tools

# Initialize MCP server
mcp = FastMCP("my-claude-squad")

# Initialize singletons (will be set up on first use)
_coordinator: Coordinator | None = None
_agent_state_manager: AgentStateManager | None = None
_scheduler: TaskScheduler | None = None
_topology_manager: TopologyManager | None = None
_session_manager: SessionManager | None = None


def get_coordinator() -> Coordinator:
    """Get or create the coordinator singleton."""
    global _coordinator
    if _coordinator is None:
        _coordinator = Coordinator(agents_dir=get_agents_dir())
    return _coordinator


def get_agent_state_manager() -> AgentStateManager:
    """Get or create the agent state manager singleton."""
    global _agent_state_manager
    if _agent_state_manager is None:
        coordinator = get_coordinator()
        _agent_state_manager = AgentStateManager(coordinator.memory)
    return _agent_state_manager


def get_scheduler() -> TaskScheduler:
    """Get or create the task scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


def get_topology_manager() -> TopologyManager:
    """Get or create the topology manager singleton."""
    global _topology_manager
    if _topology_manager is None:
        coordinator = get_coordinator()
        _topology_manager = TopologyManager(memory=coordinator.memory)
    return _topology_manager


def get_session_manager() -> SessionManager:
    """Get or create the session manager singleton."""
    global _session_manager
    if _session_manager is None:
        coordinator = get_coordinator()
        topology_mgr = get_topology_manager()
        _session_manager = SessionManager(
            memory=coordinator.memory,
            topology_manager=topology_mgr,
        )
    return _session_manager


# === MCP Tools ===


@mcp.tool()
def list_agents() -> dict[str, Any]:
    """List all available agents with their specialties.

    Returns a list of all 19 agents registered in the squad,
    including their names, descriptions, models, and trigger keywords.
    """
    coordinator = get_coordinator()
    agents = coordinator.registry.list_agents()

    return {
        "total": len(agents),
        "agents": [
            {
                "name": agent.name,
                "description": agent.description[:200] + "..." if len(agent.description) > 200 else agent.description,
                "model": agent.model.value,
                "color": agent.color,
                "triggers": agent.triggers[:5],  # Limit triggers shown
            }
            for agent in agents
        ],
    }


@mcp.tool()
def route_task(task: str) -> dict[str, Any]:
    """Find the best agent to handle a given task.

    Analyzes the task description and routes it to the most
    appropriate specialist agent based on keywords and expertise.

    Args:
        task: Description of the task to be performed

    Returns:
        Agent recommendation with routing details
    """
    coordinator = get_coordinator()
    agent = coordinator.route_task(task)

    if agent is None:
        return {
            "success": False,
            "message": "No suitable agent found for this task",
            "suggestion": "Try being more specific or use list_agents to see available specialists",
        }

    return {
        "success": True,
        "recommended_agent": agent.name,
        "agent_model": agent.model.value,
        "agent_description": agent.description[:200] + "..." if len(agent.description) > 200 else agent.description,
        "confidence": "high" if any(t in task.lower() for t in agent.triggers) else "medium",
    }


@mcp.tool()
def spawn_agent(agent_name: str, task: str) -> dict[str, Any]:
    """Spawn a specific agent to perform a task.

    Creates a task assignment for the named agent. The agent's
    full instructions are in agents/{agent_name}.md.

    Args:
        agent_name: Name of the agent to spawn (e.g., 'python-developer')
        task: Task description for the agent

    Returns:
        Task creation result with agent instructions path
    """
    coordinator = get_coordinator()
    agent = coordinator.registry.get_agent(agent_name)

    if agent is None:
        available = [a.name for a in coordinator.registry.list_agents()]
        return {
            "success": False,
            "error": f"Agent '{agent_name}' not found",
            "available_agents": available,
        }

    # Create and start task
    task_obj = coordinator.create_task(task, agent_name=agent_name)
    run = coordinator.start_task(task_obj.id)

    # Record task start in agent state manager (emits TASK_START event)
    state_manager = get_agent_state_manager()
    state_manager.record_task_start(agent_name, task_obj.id)

    return {
        "success": True,
        "task_id": task_obj.id,
        "agent": agent_name,
        "agent_file": agent.file_path,
        "model": agent.model.value,
        "instructions": f"Read agents/{agent_name}.md for complete agent instructions",
        "run_id": run.id if run else None,
    }


@mcp.tool()
def decompose_task(task: str) -> dict[str, Any]:
    """Decompose a complex task into subtasks with agent assignments.

    Returns a structured prompt for Claude Code to analyze the task
    and produce a decomposition. Claude Code should analyze the task,
    identify subtasks, dependencies, and appropriate agents, then call
    submit_decomposition with the result.

    Args:
        task: Complex task description to decompose

    Returns:
        Decomposition prompt with available agents and expected schema
    """
    coordinator = get_coordinator()
    agents = coordinator.registry.list_agents()

    # Build agent summary for Claude Code
    agent_summary = []
    for agent in agents:
        agent_summary.append({
            "name": agent.name,
            "specialty": agent.description[:150].split("\n")[0],
            "model": agent.model.value,
            "keywords": agent.triggers[:5],
        })

    return {
        "action": "analyze_and_decompose",
        "task": task,
        "instructions": """Analyze this task and decompose it into subtasks.

For each subtask, determine:
1. A clear, actionable description
2. The best agent from the available list
3. Dependencies on other subtasks (by ID)
4. Whether it can run in parallel with siblings

After analysis, call `submit_decomposition` with your structured result.

Consider:
- Natural task boundaries (action verbs, numbered steps, "then"/"after" connectors)
- Data dependencies (one task needs output from another)
- Parallelization opportunities (independent tasks can run together)
- Agent expertise matching (use agent keywords and specialties)""",
        "available_agents": agent_summary,
        "response_schema": {
            "subtasks": [
                {
                    "id": "string (short unique ID, e.g., 't1', 't2')",
                    "description": "string (clear, actionable task description)",
                    "agent": "string (agent name from available_agents)",
                    "depends_on": ["list of subtask IDs this depends on"],
                    "execution_mode": "parallel | sequential",
                    "priority": "int 1-10 (10=highest)",
                    "reasoning": "string (brief explanation of agent choice)",
                }
            ],
            "parallel_groups": [["list of task IDs that can run simultaneously"]],
            "execution_order": ["ordered list of task IDs respecting dependencies"],
            "analysis": "string (brief analysis of the overall task structure)",
        },
        "example": {
            "subtasks": [
                {
                    "id": "t1",
                    "description": "Extract data from Snowflake tables",
                    "agent": "snowflake-specialist",
                    "depends_on": [],
                    "execution_mode": "parallel",
                    "priority": 8,
                    "reasoning": "Snowflake extraction requires specialized knowledge",
                },
                {
                    "id": "t2",
                    "description": "Transform data with PySpark",
                    "agent": "spark-specialist",
                    "depends_on": ["t1"],
                    "execution_mode": "sequential",
                    "priority": 7,
                    "reasoning": "Depends on extracted data from t1",
                },
            ],
            "parallel_groups": [["t1"], ["t2"]],
            "execution_order": ["t1", "t2"],
            "analysis": "Pipeline with extraction then transformation phases",
        },
    }


@mcp.tool()
def submit_decomposition(
    original_task: str,
    subtasks: list[dict[str, Any]],
    parallel_groups: list[list[str]] | None = None,
    execution_order: list[str] | None = None,
    analysis: str | None = None,
    auto_schedule: bool = True,
) -> dict[str, Any]:
    """Submit a task decomposition from Claude Code's analysis.

    Receives the structured decomposition produced by Claude Code
    after analyzing a task via decompose_task.

    Args:
        original_task: The original complex task
        subtasks: List of subtask definitions with agent assignments
        parallel_groups: Groups of task IDs that can run simultaneously
        execution_order: Suggested execution order respecting dependencies
        analysis: Claude's analysis of the task structure
        auto_schedule: If True, automatically add tasks to scheduler

    Returns:
        Confirmation with created task IDs and workflow info
    """
    import uuid

    coordinator = get_coordinator()
    scheduler = get_scheduler()

    # Validate and create subtasks
    created_tasks: list[dict[str, Any]] = []
    id_mapping: dict[str, str] = {}  # Map submitted IDs to generated UUIDs
    validation_errors: list[str] = []

    for subtask_def in subtasks:
        submitted_id = subtask_def.get("id", str(uuid.uuid4())[:8])
        task_id = str(uuid.uuid4())[:8]
        id_mapping[submitted_id] = task_id

        description = subtask_def.get("description", "")
        agent_name = subtask_def.get("agent")

        # Validate agent exists
        if agent_name:
            agent = coordinator.registry.get_agent(agent_name)
            if agent is None:
                validation_errors.append(f"Agent '{agent_name}' not found for subtask '{submitted_id}'")
                agent_name = None  # Will be routed later

        # Parse execution mode
        mode_str = subtask_def.get("execution_mode", "sequential")
        try:
            exec_mode = ExecutionMode(mode_str)
        except ValueError:
            exec_mode = ExecutionMode.SEQUENTIAL

        created_tasks.append({
            "submitted_id": submitted_id,
            "task_id": task_id,
            "description": description,
            "agent": agent_name,
            "depends_on": subtask_def.get("depends_on", []),
            "execution_mode": exec_mode.value,
            "priority": subtask_def.get("priority", 5),
            "reasoning": subtask_def.get("reasoning"),
        })

    # Resolve dependency IDs
    for task_info in created_tasks:
        resolved_deps = []
        for dep_id in task_info["depends_on"]:
            if dep_id in id_mapping:
                resolved_deps.append(id_mapping[dep_id])
            else:
                validation_errors.append(f"Dependency '{dep_id}' not found for subtask '{task_info['submitted_id']}'")
        task_info["resolved_deps"] = resolved_deps

    # Add to scheduler if requested
    scheduled_ids: list[str] = []
    if auto_schedule and not validation_errors:
        for task_info in created_tasks:
            new_task = Task(
                id=task_info["task_id"],
                description=task_info["description"],
                agent_name=task_info["agent"],
                status=TaskStatus.PENDING,
            )
            scheduler.add_task(new_task, depends_on=task_info["resolved_deps"] or None)
            scheduled_ids.append(task_info["task_id"])

    # Resolve parallel groups IDs
    resolved_parallel_groups: list[list[str]] = []
    if parallel_groups:
        for group in parallel_groups:
            resolved_group = [id_mapping.get(tid, tid) for tid in group]
            resolved_parallel_groups.append(resolved_group)

    # Resolve execution order IDs
    resolved_execution_order: list[str] = []
    if execution_order:
        resolved_execution_order = [id_mapping.get(tid, tid) for tid in execution_order]

    # Get ready tasks
    ready_tasks = scheduler.get_ready_tasks() if auto_schedule else []

    result = {
        "success": len(validation_errors) == 0,
        "original_task": original_task,
        "subtask_count": len(created_tasks),
        "subtasks": [
            {
                "id": t["task_id"],
                "description": t["description"][:100],
                "agent": t["agent"],
                "depends_on": t["resolved_deps"],
                "execution_mode": t["execution_mode"],
            }
            for t in created_tasks
        ],
        "id_mapping": id_mapping,
        "parallel_groups": resolved_parallel_groups,
        "execution_order": resolved_execution_order,
        "analysis": analysis,
    }

    if auto_schedule:
        result["scheduled"] = True
        result["ready_to_execute"] = [t.id for t in ready_tasks]

    if validation_errors:
        result["validation_errors"] = validation_errors

    return result


@mcp.tool()
def memory_store(key: str, value: str, namespace: str = "default") -> dict[str, Any]:
    """Store a key-value pair in persistent memory.

    Stores information that persists across sessions in the
    DuckDB database at .swarm/memory.duckdb.

    Args:
        key: Unique key for the memory
        value: Value to store
        namespace: Optional namespace for organization

    Returns:
        Confirmation of storage
    """
    coordinator = get_coordinator()
    coordinator.memory.store(key, value, namespace)

    return {
        "success": True,
        "key": key,
        "namespace": namespace,
        "message": f"Stored '{key}' in namespace '{namespace}'",
    }


@mcp.tool()
def memory_query(pattern: str, namespace: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Query persistent memory by pattern.

    Searches for memories matching the given pattern in keys or values.

    Args:
        pattern: Search pattern (SQL LIKE style)
        namespace: Optional namespace filter
        limit: Maximum results to return

    Returns:
        List of matching memories
    """
    coordinator = get_coordinator()
    memories = coordinator.memory.query(pattern, namespace, limit)

    return {
        "pattern": pattern,
        "namespace": namespace,
        "count": len(memories),
        "memories": [
            {
                "key": m.key,
                "value": m.value[:100] + "..." if len(m.value) > 100 else m.value,
                "namespace": m.namespace,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ],
    }


@mcp.tool()
def get_storage_stats() -> dict[str, Any]:
    """Get storage statistics for the DuckDB database.

    Returns row counts for all tables, oldest/newest timestamps,
    and database file size. Useful for monitoring database growth
    and planning cleanup.

    Returns:
        Storage statistics including row counts and database size
    """
    coordinator = get_coordinator()
    stats = coordinator.memory.get_storage_stats()

    return {
        "success": True,
        "tables": {
            "memories": stats.get("memories_count", 0),
            "agent_runs": stats.get("agent_runs_count", 0),
            "task_log": stats.get("task_log_count", 0),
            "agent_health": stats.get("agent_health_count", 0),
            "agent_events": stats.get("agent_events_count", 0),
        },
        "time_ranges": {
            "agent_runs": {
                "oldest": stats.get("agent_runs_oldest"),
                "newest": stats.get("agent_runs_newest"),
            },
            "agent_events": {
                "oldest": stats.get("agent_events_oldest"),
                "newest": stats.get("agent_events_newest"),
            },
        },
        "database": {
            "size_bytes": stats.get("db_size_bytes", 0),
            "size_mb": stats.get("db_size_mb", 0),
        },
    }


@mcp.tool()
def cleanup_storage(
    runs_days: int = 30,
    events_days: int = 7,
    tasks_days: int = 30,
    memories_days: int | None = None,
    vacuum: bool = True,
) -> dict[str, Any]:
    """Clean up old data from the DuckDB database.

    Deletes data older than the specified retention periods.
    Use get_storage_stats first to see current database state.

    Args:
        runs_days: Delete agent runs older than this (default 30 days)
        events_days: Delete agent events older than this (default 7 days)
        tasks_days: Delete task log entries older than this (default 30 days)
        memories_days: Delete memories older than this (None = keep all memories)
        vacuum: Run VACUUM after cleanup to reclaim disk space (default True)

    Returns:
        Cleanup results with counts of deleted rows
    """
    coordinator = get_coordinator()

    # Get stats before cleanup
    stats_before = coordinator.memory.get_storage_stats()

    # Run cleanup
    deleted = coordinator.memory.run_full_cleanup(
        runs_days=runs_days,
        events_days=events_days,
        tasks_days=tasks_days,
        memories_days=memories_days,
    )

    # Vacuum is already called by run_full_cleanup, but can force additional if needed
    if vacuum:
        coordinator.memory.vacuum()

    # Get stats after cleanup
    stats_after = coordinator.memory.get_storage_stats()

    return {
        "success": True,
        "deleted": deleted,
        "retention_policy": {
            "runs_days": runs_days,
            "events_days": events_days,
            "tasks_days": tasks_days,
            "memories_days": memories_days,
        },
        "before": {
            "size_mb": stats_before.get("db_size_mb", 0),
            "total_rows": sum(
                stats_before.get(f"{t}_count", 0)
                for t in ["memories", "agent_runs", "task_log", "agent_events"]
            ),
        },
        "after": {
            "size_mb": stats_after.get("db_size_mb", 0),
            "total_rows": sum(
                stats_after.get(f"{t}_count", 0)
                for t in ["memories", "agent_runs", "task_log", "agent_events"]
            ),
        },
    }


@mcp.tool()
def swarm_status() -> dict[str, Any]:
    """Get current swarm status and statistics.

    Returns an overview of the swarm including agent count,
    active tasks, and recent agent runs.

    Returns:
        Swarm status with statistics
    """
    coordinator = get_coordinator()
    status = coordinator.get_swarm_status()
    stats = coordinator.memory.get_run_stats()

    return {
        "total_agents": status.total_agents,
        "active_tasks": status.active_tasks,
        "stats": {
            "total_runs": stats["total_runs"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "in_progress": stats["in_progress"],
            "total_tokens": stats["total_tokens"],
        },
        "recent_runs": [
            {
                "id": run.id,
                "agent": run.agent_name,
                "task": run.task[:50] + "..." if len(run.task) > 50 else run.task,
                "status": run.status.value,
                "started_at": run.started_at.isoformat(),
            }
            for run in status.recent_runs
        ],
    }


@mcp.tool()
def complete_run(
    task_id: str, result: str | None = None, success: bool = True, tokens_used: int = 0
) -> dict[str, Any]:
    """Mark a task/run as complete.

    Updates the task status and logs completion in the database.

    Args:
        task_id: Task ID to complete
        result: Optional result text
        success: Whether the task succeeded
        tokens_used: Number of tokens used (for tracking)

    Returns:
        Completion confirmation
    """
    from datetime import datetime

    coordinator = get_coordinator()

    # Get task info BEFORE completing (so we can access agent_name and calculate duration)
    task = coordinator._active_tasks.get(task_id)
    agent_name = task.agent_name if task else None
    duration_ms = 0.0
    if task:
        duration_ms = (datetime.now() - task.created_at).total_seconds() * 1000

    # Complete the task in coordinator
    coordinator.complete_task(task_id, result, success, tokens_used)

    # Record task completion in agent state manager (emits TASK_COMPLETE/TASK_FAILED event)
    if agent_name:
        state_manager = get_agent_state_manager()
        state_manager.record_task_complete(agent_name, success, duration_ms)

    return {
        "success": True,
        "task_id": task_id,
        "agent": agent_name,
        "status": "completed" if success else "failed",
        "result": result,
        "tokens_used": tokens_used,
        "duration_ms": round(duration_ms, 2),
    }


# === Agent Health Tools ===


@mcp.tool()
def get_agent_health(agent_name: str | None = None) -> dict[str, Any]:
    """Get health status for one or all agents.

    Returns runtime health information including status, health score,
    success rate, and recent activity.

    Args:
        agent_name: Optional specific agent to check. If None, returns all agents.

    Returns:
        Health status for the specified agent(s)
    """
    state_manager = get_agent_state_manager()
    coordinator = get_coordinator()

    if agent_name is not None:
        # Get health for specific agent
        health = state_manager.get_health(agent_name)
        if health is None:
            # Initialize health for this agent if not tracked yet
            agent = coordinator.registry.get_agent(agent_name)
            if agent is None:
                return {
                    "success": False,
                    "error": f"Agent '{agent_name}' not found",
                }
            health = state_manager.initialize_agent(agent_name)

        return {
            "success": True,
            "agent": {
                "name": health.agent_name,
                "status": health.status.value,
                "health_score": round(health.health_score, 2),
                "success_rate": round(health.success_rate, 2),
                "avg_execution_time_ms": round(health.avg_execution_time_ms, 2),
                "current_task_id": health.current_task_id,
                "error_count": health.error_count,
                "success_count": health.success_count,
                "last_heartbeat": health.last_heartbeat.isoformat(),
            },
        }
    else:
        # Get health for all agents
        all_health = state_manager.get_all_health()

        # Also include agents that don't have health records yet
        all_agent_names = {a.name for a in coordinator.registry.list_agents()}
        tracked_names = {h.agent_name for h in all_health}

        # Initialize health for untracked agents
        for name in all_agent_names - tracked_names:
            state_manager.initialize_agent(name)

        # Refresh the list
        all_health = state_manager.get_all_health()

        return {
            "success": True,
            "total": len(all_health),
            "available": len(state_manager.get_available_agents()),
            "busy": len(state_manager.get_busy_agents()),
            "agents": [
                {
                    "name": h.agent_name,
                    "status": h.status.value,
                    "health_score": round(h.health_score, 2),
                    "success_rate": round(h.success_rate, 2),
                    "current_task_id": h.current_task_id,
                }
                for h in all_health
            ],
        }


@mcp.tool()
def set_agent_status(agent_name: str, status: str, reason: str | None = None) -> dict[str, Any]:
    """Manually set an agent's status.

    Use this to pause, resume, or mark agents as offline/error.

    Args:
        agent_name: Name of the agent to update
        status: New status (idle, busy, paused, error, offline)
        reason: Optional reason for the status change

    Returns:
        Updated agent health status
    """
    state_manager = get_agent_state_manager()
    coordinator = get_coordinator()

    # Validate agent exists
    agent = coordinator.registry.get_agent(agent_name)
    if agent is None:
        return {
            "success": False,
            "error": f"Agent '{agent_name}' not found",
            "available_agents": [a.name for a in coordinator.registry.list_agents()],
        }

    # Validate status
    try:
        new_status = AgentStatus(status)
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid status '{status}'",
            "valid_statuses": [s.value for s in AgentStatus],
        }

    # Update status
    health = state_manager.set_status(agent_name, new_status, reason)

    return {
        "success": True,
        "agent": agent_name,
        "old_status": health.status.value,  # Note: this shows the new status since we updated it
        "new_status": new_status.value,
        "reason": reason,
        "health_score": round(health.health_score, 2),
    }


# === Task Scheduling Tools ===


@mcp.tool()
def create_dependent_task(
    task: str,
    depends_on: list[str] | None = None,
    agent_name: str | None = None,
    priority: int = 5,
) -> dict[str, Any]:
    """Create a task with dependencies on other tasks.

    The task will only be ready for execution after all its dependencies
    have completed successfully.

    Args:
        task: Task description
        depends_on: List of task IDs this task depends on
        agent_name: Optional agent to assign to this task
        priority: Priority level 1-10 (10 = highest)

    Returns:
        Created task information
    """
    import uuid

    scheduler = get_scheduler()
    coordinator = get_coordinator()

    # Validate dependencies exist
    if depends_on:
        for dep_id in depends_on:
            if dep_id not in scheduler._tasks:
                return {
                    "success": False,
                    "error": f"Dependency task '{dep_id}' not found",
                    "hint": "Use get_task_graph to see available tasks",
                }

    # Validate agent if specified
    if agent_name:
        agent = coordinator.registry.get_agent(agent_name)
        if agent is None:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "available_agents": [a.name for a in coordinator.registry.list_agents()],
            }

    # Create task
    task_id = str(uuid.uuid4())[:8]
    new_task = Task(
        id=task_id,
        description=task,
        agent_name=agent_name,
        status=TaskStatus.PENDING,
    )

    scheduler.add_task(new_task, depends_on=depends_on)

    return {
        "success": True,
        "task_id": task_id,
        "description": task,
        "agent": agent_name,
        "depends_on": depends_on or [],
        "priority": priority,
        "status": "pending",
    }


@mcp.tool()
def get_task_graph() -> dict[str, Any]:
    """Get the current task dependency graph.

    Shows all scheduled tasks, their dependencies, and circuit breaker states.

    Returns:
        Task graph with dependencies and status information
    """
    scheduler = get_scheduler()
    return scheduler.get_task_graph()


@mcp.tool()
def get_ready_tasks() -> dict[str, Any]:
    """Get tasks that are ready to execute.

    Returns tasks whose dependencies are all satisfied.

    Returns:
        List of tasks ready for execution
    """
    scheduler = get_scheduler()
    ready = scheduler.get_ready_tasks()

    return {
        "count": len(ready),
        "tasks": [
            {
                "id": t.id,
                "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
                "agent": t.agent_name,
            }
            for t in ready
        ],
    }


@mcp.tool()
def complete_scheduled_task(
    task_id: str,
    success: bool = True,
    result: str | None = None,
) -> dict[str, Any]:
    """Mark a scheduled task as complete.

    This updates the task status and unlocks dependent tasks.

    Args:
        task_id: ID of the task to complete
        success: Whether the task succeeded
        result: Optional result text

    Returns:
        Completion confirmation and newly ready tasks
    """
    scheduler = get_scheduler()

    if task_id not in scheduler._tasks:
        return {
            "success": False,
            "error": f"Task '{task_id}' not found",
        }

    task = scheduler._tasks[task_id]
    task.result = result
    scheduler.mark_completed(task_id, success=success)

    # Get newly ready tasks
    ready = scheduler.get_ready_tasks()

    return {
        "success": True,
        "task_id": task_id,
        "task_success": success,
        "newly_ready_tasks": len(ready),
        "ready_task_ids": [t.id for t in ready],
    }


@mcp.tool()
def execute_workflow(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Execute a workflow of tasks with dependencies.

    Creates multiple tasks at once with their dependency relationships.

    Args:
        tasks: List of task definitions with format:
               [{"description": "...", "depends_on": ["task_id"], "agent": "..."}]

    Returns:
        Created workflow information
    """
    import uuid

    scheduler = get_scheduler()
    coordinator = get_coordinator()

    created_tasks = []
    id_mapping: dict[int, str] = {}  # Map list index to generated task ID

    # First pass: create all tasks and build ID mapping
    for i, task_def in enumerate(tasks):
        task_id = str(uuid.uuid4())[:8]
        id_mapping[i] = task_id

        description = task_def.get("description", f"Task {i + 1}")
        agent_name = task_def.get("agent")

        # Validate agent
        if agent_name:
            agent = coordinator.registry.get_agent(agent_name)
            if agent is None:
                return {
                    "success": False,
                    "error": f"Agent '{agent_name}' not found for task {i + 1}",
                }

        new_task = Task(
            id=task_id,
            description=description,
            agent_name=agent_name,
            status=TaskStatus.PENDING,
        )

        created_tasks.append({
            "index": i,
            "id": task_id,
            "task": new_task,
            "depends_on_indices": task_def.get("depends_on", []),
        })

    # Second pass: resolve dependencies and add to scheduler
    for task_info in created_tasks:
        depends_on = []
        for dep in task_info["depends_on_indices"]:
            if isinstance(dep, int) and dep in id_mapping:
                depends_on.append(id_mapping[dep])
            elif isinstance(dep, str):
                # Direct task ID reference
                depends_on.append(dep)

        scheduler.add_task(task_info["task"], depends_on=depends_on or None)

    # Get execution order
    try:
        execution_order = scheduler.topological_sort()
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
        }

    return {
        "success": True,
        "workflow_size": len(created_tasks),
        "tasks": [
            {
                "id": t["id"],
                "description": t["task"].description[:50] + "..." if len(t["task"].description) > 50 else t["task"].description,
                "agent": t["task"].agent_name,
            }
            for t in created_tasks
        ],
        "execution_order": [t.id for t in execution_order],
        "ready_now": [t.id for t in scheduler.get_ready_tasks()],
    }


@mcp.tool()
def clear_workflow() -> dict[str, Any]:
    """Clear all scheduled tasks.

    Removes all tasks from the scheduler. Use with caution.

    Returns:
        Confirmation of cleared tasks
    """
    scheduler = get_scheduler()
    count = len(scheduler._tasks)
    scheduler.clear()

    return {
        "success": True,
        "cleared_tasks": count,
        "message": "All scheduled tasks have been cleared",
    }


# === Health Check ===


@mcp.tool()
def get_health() -> dict[str, Any]:
    """Get system health status.

    Returns basic health info including agent count, run stats,
    and Langfuse connection status.

    Returns:
        Health status with component states
    """
    from datetime import datetime

    coordinator = get_coordinator()
    stats = coordinator.memory.get_run_stats()

    # Determine Langfuse status
    langfuse_client = get_langfuse()
    if langfuse_client is not None:
        langfuse_status = "connected"
    elif langfuse_enabled():
        langfuse_status = "enabled_not_connected"
    else:
        langfuse_status = "disabled"

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "coordinator": "ok",
            "memory": "ok",
            "langfuse": langfuse_status,
        },
        "stats": {
            "total_agents": len(coordinator.registry.list_agents()),
            "total_runs": stats["total_runs"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "in_progress": stats["in_progress"],
        },
    }


# === Events and Metrics Tools ===


@mcp.tool()
def get_metrics(reset: bool = False) -> dict[str, Any]:
    """Get orchestration metrics.

    Returns counters, gauges, and histograms tracking system performance.

    Args:
        reset: If True, reset all metrics after returning them

    Returns:
        Metrics summary with counters, gauges, and histograms
    """
    collector = get_metrics_collector()
    summary = collector.get_summary()

    if reset:
        collector.reset()
        summary["reset"] = True

    return summary


@mcp.tool()
def get_events(
    limit: int = 50,
    event_type: str | None = None,
    agent_name: str | None = None,
) -> dict[str, Any]:
    """Get recent events from the event bus.

    Returns recent events with optional filtering by type or agent.

    Args:
        limit: Maximum number of events to return
        event_type: Filter by event type (heartbeat, status_change, task_start, task_complete, task_failed, error)
        agent_name: Filter by agent name

    Returns:
        List of recent events
    """
    event_bus = get_event_bus()

    # Parse event type if provided
    parsed_event_type = None
    if event_type is not None:
        try:
            parsed_event_type = AgentEventType(event_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid event type '{event_type}'",
                "valid_types": [t.value for t in AgentEventType],
            }

    events = event_bus.get_history(
        event_type=parsed_event_type,
        agent_name=agent_name,
        limit=limit,
    )

    stats = event_bus.get_stats()

    return {
        "success": True,
        "count": len(events),
        "stats": stats,
        "events": [
            {
                "id": e.id,
                "agent": e.agent_name,
                "type": e.event_type.value,
                "data": e.event_data,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ],
    }


@mcp.tool()
def emit_event(
    agent_name: str,
    event_type: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit a custom event to the event bus.

    Allows agents to emit events that other handlers can react to.

    Args:
        agent_name: Name of the agent emitting the event
        event_type: Type of event (heartbeat, status_change, task_start, task_complete, task_failed, error)
        data: Optional event data payload

    Returns:
        Confirmation of event emission
    """
    event_bus = get_event_bus()

    # Parse event type
    try:
        parsed_type = AgentEventType(event_type)
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid event type '{event_type}'",
            "valid_types": [t.value for t in AgentEventType],
        }

    event = create_event(
        agent_name=agent_name,
        event_type=parsed_type,
        event_data=data,
    )

    # Emit synchronously (since MCP tools are sync)
    handler_count = event_bus.emit_sync(event)

    # Also persist to memory for history
    coordinator = get_coordinator()
    coordinator.memory.insert_agent_event(event)

    return {
        "success": True,
        "event_id": event.id,
        "agent": agent_name,
        "type": parsed_type.value,
        "handlers_called": handler_count,
    }


# === Command Tools (converted from markdown commands) ===


@mcp.tool()
def create_pipeline(
    source: str,
    target: str,
    name: str = "pipeline",
    incremental: bool = False,
    schedule: str | None = None,
    with_tests: bool = True,
) -> dict[str, Any]:
    """Generate data pipeline boilerplate for ETL/ELT workflows.

    Creates a complete pipeline structure with extraction, transformation,
    and loading components based on the specified source and target.

    Args:
        source: Data source type (api, s3, postgresql, mysql, files)
        target: Data target type (snowflake, redshift, s3, postgresql)
        name: Pipeline name for the directory
        incremental: Generate incremental loading logic with watermarks
        schedule: Cron expression for Airflow DAG (e.g., "0 6 * * *")
        with_tests: Include pytest test files

    Returns:
        Pipeline structure with file templates and next steps
    """
    return command_tools.create_pipeline(source, target, name, incremental, schedule, with_tests)


@mcp.tool()
def analyze_query(sql: str) -> dict[str, Any]:
    """Analyze SQL query and provide optimization recommendations.

    Checks for common anti-patterns including index issues, join problems,
    query structure issues, and performance concerns.

    Args:
        sql: SQL query to analyze (or description of slow query)

    Returns:
        Analysis with issues found and optimization suggestions
    """
    return command_tools.analyze_query(sql)


@mcp.tool()
def analyze_data(path: str, sample_size: int = 1000) -> dict[str, Any]:
    """Profile and analyze a dataset for quality and patterns.

    Returns analysis template and instructions for data profiling.

    Args:
        path: Path to the data file (CSV, Parquet, JSON)
        sample_size: Number of rows to sample for analysis

    Returns:
        Analysis template with profiling instructions
    """
    return command_tools.analyze_data(path, sample_size)


@mcp.tool()
def create_dockerfile(
    project_type: str = "python",
    optimize_for: str = "size",
    python_version: str = "3.11",
    include_dev: bool = False,
) -> dict[str, Any]:
    """Create optimized Dockerfile for a project.

    Generates a multi-stage Dockerfile with best practices including
    layer caching, non-root user, and health checks.

    Args:
        project_type: Type of project (python, node, java)
        optimize_for: Optimization target (size, speed)
        python_version: Python version for base image
        include_dev: Include development tools

    Returns:
        Dockerfile content and related files
    """
    return command_tools.create_dockerfile(project_type, optimize_for, python_version, include_dev)


@mcp.tool()
def create_k8s_manifest(
    app_name: str,
    replicas: int = 2,
    port: int = 8000,
    image: str = "app:latest",
    resources_preset: str = "small",
) -> dict[str, Any]:
    """Generate Kubernetes manifests for an application.

    Creates Deployment, Service, ConfigMap, and HorizontalPodAutoscaler
    with production-ready defaults.

    Args:
        app_name: Name of the application
        replicas: Number of replicas
        port: Container port
        image: Docker image to deploy
        resources_preset: Resource preset (small, medium, large)

    Returns:
        Kubernetes manifest files
    """
    return command_tools.create_k8s_manifest(app_name, replicas, port, image, resources_preset)


@mcp.tool()
def scaffold_rag(
    name: str,
    vectordb: str = "chromadb",
    framework: str = "langchain",
    embedding_model: str = "text-embedding-3-small",
) -> dict[str, Any]:
    """Generate RAG application boilerplate.

    Creates a complete RAG application structure with vector database
    integration, document ingestion, and retrieval chain.

    Args:
        name: Application name
        vectordb: Vector database (chromadb, qdrant, weaviate, pgvector)
        framework: RAG framework (langchain, llamaindex)
        embedding_model: Embedding model to use

    Returns:
        RAG application scaffold with all necessary files
    """
    return command_tools.scaffold_rag(name, vectordb, framework, embedding_model)


@mcp.tool()
def scaffold_mcp_server(
    name: str,
    tools: list[str],
    transport: str = "stdio",
) -> dict[str, Any]:
    """Generate MCP server template.

    Creates a FastMCP server with specified tools.

    Args:
        name: Server name
        tools: List of tool names to create
        transport: Transport type (stdio, http)

    Returns:
        MCP server scaffold with tool stubs
    """
    return command_tools.scaffold_mcp_server(name, tools, transport)


@mcp.tool()
def generate_commit_message(
    changes_summary: str,
    change_type: str = "feat",
    scope: str | None = None,
    breaking: bool = False,
) -> dict[str, Any]:
    """Generate a conventional commit message.

    IMPORTANT: Never includes AI attribution, "Generated by Claude",
    or any Co-Authored-By headers.

    Args:
        changes_summary: Description of changes made
        change_type: Type (feat, fix, docs, style, refactor, perf, test, build, ci, chore)
        scope: Optional scope (e.g., api, auth, db)
        breaking: Whether this is a breaking change

    Returns:
        Formatted commit message ready for git commit
    """
    return command_tools.generate_commit_message(changes_summary, change_type, scope, breaking)


@mcp.tool()
def lookup_docs(library: str, topic: str | None = None) -> dict[str, Any]:
    """Look up documentation for a library or tool.

    Returns instructions for using Context7 and Exa MCPs to find
    up-to-date documentation.

    Args:
        library: Library or framework name
        topic: Specific topic to focus on

    Returns:
        Instructions for documentation lookup with MCP tool names
    """
    return command_tools.lookup_docs(library, topic)


# === Swarm Topology Tools ===


@mcp.tool()
def create_swarm(
    name: str,
    topology: str,
    agents: list[str],
    coordinator: str | None = None,
) -> dict[str, Any]:
    """Create a new swarm with the specified topology.

    Swarms coordinate multiple agents using different patterns:
    - hierarchical: Queen-Worker delegation (coordinator delegates to workers)
    - mesh: Peer-to-peer collaboration (all agents can communicate)
    - ring: Sequential pipeline processing (A -> B -> C)
    - star: Hub-spoke coordination (hub delegates to spokes)

    Args:
        name: Human-readable swarm name
        topology: Topology pattern (hierarchical, mesh, ring, star)
        agents: List of agent names to include
        coordinator: Agent to act as coordinator (required for hierarchical/star)

    Returns:
        Created swarm with member details
    """
    topology_mgr = get_topology_manager()
    coord = get_coordinator()

    # Validate topology
    try:
        topo_type = TopologyType(topology)
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid topology '{topology}'",
            "valid_topologies": [t.value for t in TopologyType],
        }

    # Validate agents exist
    for agent_name in agents:
        agent = coord.registry.get_agent(agent_name)
        if agent is None:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "available_agents": [a.name for a in coord.registry.list_agents()],
            }

    # Validate coordinator for topologies that need one
    if topo_type in (TopologyType.HIERARCHICAL, TopologyType.STAR):
        if coordinator and coordinator not in agents:
            return {
                "success": False,
                "error": f"Coordinator '{coordinator}' must be in the agents list",
            }

    try:
        swarm = topology_mgr.create_swarm(name, topo_type, agents, coordinator)
        return {
            "success": True,
            "swarm_id": swarm.id,
            "name": swarm.name,
            "topology": swarm.topology.value,
            "member_count": len(swarm.members),
            "members": [
                {
                    "agent": m.agent_name,
                    "role": m.role.value,
                    "can_delegate_to": m.can_delegate_to,
                    "reports_to": m.reports_to,
                }
                for m in swarm.members
            ],
            "coordinator": (
                swarm.get_coordinator().agent_name if swarm.get_coordinator() else None
            ),
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def list_swarms(active_only: bool = True) -> dict[str, Any]:
    """List all swarms.

    Args:
        active_only: If True, only return active swarms

    Returns:
        List of swarms with their topologies and member counts
    """
    topology_mgr = get_topology_manager()
    swarms = topology_mgr.list_swarms(active_only=active_only)

    return {
        "success": True,
        "count": len(swarms),
        "swarms": [
            {
                "id": s.id,
                "name": s.name,
                "topology": s.topology.value,
                "member_count": len(s.members),
                "active": s.active,
                "coordinator": (
                    s.get_coordinator().agent_name if s.get_coordinator() else None
                ),
            }
            for s in swarms
        ],
    }


@mcp.tool()
def get_swarm(swarm_id: str) -> dict[str, Any]:
    """Get detailed information about a swarm.

    Args:
        swarm_id: ID of the swarm

    Returns:
        Swarm details including all members and their roles
    """
    topology_mgr = get_topology_manager()
    status = topology_mgr.get_swarm_status(swarm_id)

    if "error" in status:
        return {
            "success": False,
            "error": status["error"],
        }

    return {
        "success": True,
        **status,
    }


@mcp.tool()
def delete_swarm(swarm_id: str, force: bool = False) -> dict[str, Any]:
    """Delete or deactivate a swarm.

    Args:
        swarm_id: ID of the swarm to delete
        force: If True, permanently delete. If False, just deactivate.

    Returns:
        Confirmation of deletion/deactivation
    """
    topology_mgr = get_topology_manager()

    swarm = topology_mgr.get_swarm(swarm_id)
    if not swarm:
        return {
            "success": False,
            "error": f"Swarm '{swarm_id}' not found",
        }

    if force:
        topology_mgr.delete_swarm(swarm_id)
        return {
            "success": True,
            "action": "deleted",
            "swarm_id": swarm_id,
            "swarm_name": swarm.name,
        }
    else:
        topology_mgr.deactivate_swarm(swarm_id)
        return {
            "success": True,
            "action": "deactivated",
            "swarm_id": swarm_id,
            "swarm_name": swarm.name,
            "message": "Use force=True to permanently delete",
        }


@mcp.tool()
def get_swarm_delegation(
    swarm_id: str,
    from_agent: str,
    task_description: str,
) -> dict[str, Any]:
    """Get the delegation target for a task within a swarm.

    Based on the swarm's topology, determines which agent should
    receive a delegated task.

    Args:
        swarm_id: ID of the swarm
        from_agent: Agent delegating the task
        task_description: Description of the task being delegated

    Returns:
        Delegation target and routing information
    """
    import uuid

    topology_mgr = get_topology_manager()

    swarm = topology_mgr.get_swarm(swarm_id)
    if not swarm:
        return {
            "success": False,
            "error": f"Swarm '{swarm_id}' not found",
        }

    # Find the member
    member = next((m for m in swarm.members if m.agent_name == from_agent), None)
    if not member:
        return {
            "success": False,
            "error": f"Agent '{from_agent}' is not a member of swarm '{swarm_id}'",
            "swarm_members": [m.agent_name for m in swarm.members],
        }

    # Create a dummy task for routing
    task = Task(
        id=str(uuid.uuid4())[:8],
        description=task_description,
        agent_name=from_agent,
    )

    target = topology_mgr.get_delegation_target(swarm_id, from_agent, task)

    if not target:
        return {
            "success": False,
            "error": f"Agent '{from_agent}' cannot delegate tasks in this topology",
            "agent_role": member.role.value,
            "can_delegate_to": member.can_delegate_to,
        }

    return {
        "success": True,
        "from_agent": from_agent,
        "delegate_to": target,
        "topology": swarm.topology.value,
        "from_role": member.role.value,
    }


@mcp.tool()
def create_swarm_workflow(
    swarm_id: str,
    task_description: str,
) -> dict[str, Any]:
    """Create workflow tasks for a swarm based on its topology.

    Generates appropriate tasks based on the swarm's structure:
    - Ring: Sequential tasks through the pipeline
    - Hierarchical/Star: Coordinator task for delegation
    - Mesh: Collaborative tasks for all peers

    Args:
        swarm_id: ID of the swarm
        task_description: Description of the overall task

    Returns:
        Created workflow tasks ready for execution
    """
    topology_mgr = get_topology_manager()
    scheduler = get_scheduler()

    swarm = topology_mgr.get_swarm(swarm_id)
    if not swarm:
        return {
            "success": False,
            "error": f"Swarm '{swarm_id}' not found",
        }

    # Create tasks based on topology
    tasks = topology_mgr.create_workflow_tasks(swarm_id, task_description)

    if not tasks:
        return {
            "success": False,
            "error": "No tasks could be created for this swarm",
        }

    # For ring topology, add dependencies (sequential)
    if swarm.topology == TopologyType.RING:
        for i, task in enumerate(tasks):
            deps = [tasks[i - 1].id] if i > 0 else None
            scheduler.add_task(task, depends_on=deps)
    else:
        # For other topologies, add all tasks without dependencies
        for task in tasks:
            scheduler.add_task(task)

    ready = scheduler.get_ready_tasks()

    return {
        "success": True,
        "swarm_id": swarm_id,
        "swarm_name": swarm.name,
        "topology": swarm.topology.value,
        "task_count": len(tasks),
        "tasks": [
            {
                "id": t.id,
                "description": t.description[:80],
                "agent": t.agent_name,
            }
            for t in tasks
        ],
        "ready_to_execute": [t.id for t in ready],
        "execution_pattern": (
            "sequential" if swarm.topology == TopologyType.RING else "parallel"
        ),
    }


# === Session Management Tools ===


@mcp.tool()
def create_session(
    name: str,
    tasks: list[dict[str, Any]] | None = None,
    description: str | None = None,
    swarm_id: str | None = None,
) -> dict[str, Any]:
    """Create a new persistent, resumable work session.

    Sessions track multi-task workflows that can be paused, resumed,
    and persist across restarts.

    Args:
        name: Human-readable session name
        tasks: Optional list of task dicts with 'description' and optional 'agent_name'
        description: Optional session description
        swarm_id: Optional swarm ID for topology-aware execution

    Returns:
        Created session with ID and initial state
    """
    session_mgr = get_session_manager()

    # Validate swarm if provided
    if swarm_id:
        topology_mgr = get_topology_manager()
        swarm = topology_mgr.get_swarm(swarm_id)
        if not swarm:
            return {
                "success": False,
                "error": f"Swarm '{swarm_id}' not found",
            }

    session = session_mgr.create_session(
        name=name,
        tasks=tasks,
        description=description,
        swarm_id=swarm_id,
    )

    return {
        "success": True,
        "session_id": session.id,
        "name": session.name,
        "description": session.description,
        "status": session.status.value,
        "task_count": len(session.tasks),
        "swarm_id": session.swarm_id,
        "created_at": session.created_at.isoformat(),
    }


@mcp.tool()
def create_session_from_swarm(
    name: str,
    swarm_id: str,
    task_description: str,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a session with tasks generated from a swarm's topology.

    Uses the swarm's coordination pattern to generate appropriate tasks:
    - Ring: Sequential tasks through the pipeline
    - Hierarchical/Star: Coordinator task for delegation
    - Mesh: Collaborative tasks for all peers

    Args:
        name: Human-readable session name
        swarm_id: ID of the swarm to use
        task_description: Description of the overall task
        description: Optional session description

    Returns:
        Created session with topology-generated tasks
    """
    session_mgr = get_session_manager()

    session = session_mgr.create_session_from_swarm(
        name=name,
        swarm_id=swarm_id,
        task_description=task_description,
        description=description,
    )

    if not session:
        return {
            "success": False,
            "error": f"Could not create session from swarm '{swarm_id}'",
            "hint": "Ensure the swarm exists and has at least one member",
        }

    return {
        "success": True,
        "session_id": session.id,
        "name": session.name,
        "status": session.status.value,
        "task_count": len(session.tasks),
        "tasks": [
            {
                "task_id": t.task_id,
                "description": t.description[:80],
                "agent": t.agent_name,
            }
            for t in session.tasks
        ],
        "swarm_id": session.swarm_id,
    }


@mcp.tool()
def get_session_info(session_id: str) -> dict[str, Any]:
    """Get detailed information about a session.

    Args:
        session_id: ID of the session

    Returns:
        Session details including tasks and progress
    """
    session_mgr = get_session_manager()
    status = session_mgr.get_session_status(session_id)

    if "error" in status:
        return {
            "success": False,
            **status,
        }

    return {
        "success": True,
        **status,
    }


@mcp.tool()
def list_sessions_tool(
    status: str | None = None,
    active_only: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """List sessions with optional filtering.

    Args:
        status: Optional status filter (active, paused, completed, failed, cancelled)
        active_only: If True, only return active/paused sessions
        limit: Maximum results to return

    Returns:
        List of sessions with summary information
    """
    session_mgr = get_session_manager()

    # Parse status if provided
    parsed_status = None
    if status is not None:
        try:
            parsed_status = SessionStatus(status)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid status '{status}'",
                "valid_statuses": [s.value for s in SessionStatus],
            }

    sessions = session_mgr.list_sessions(
        status=parsed_status,
        active_only=active_only,
        limit=limit,
    )

    return {
        "success": True,
        "count": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "name": s.name,
                "status": s.status.value,
                "progress": round(s.progress, 2),
                "task_count": len(s.tasks),
                "swarm_id": s.swarm_id,
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ],
    }


@mcp.tool()
def pause_session(session_id: str) -> dict[str, Any]:
    """Pause an active session.

    Paused sessions can be resumed later to continue where they left off.

    Args:
        session_id: ID of the session to pause

    Returns:
        Updated session status
    """
    session_mgr = get_session_manager()
    session = session_mgr.pause_session(session_id)

    if not session:
        return {
            "success": False,
            "error": f"Could not pause session '{session_id}'",
            "hint": "Session may not exist or may not be active",
        }

    return {
        "success": True,
        "session_id": session.id,
        "name": session.name,
        "status": session.status.value,
        "paused_at": session.paused_at.isoformat() if session.paused_at else None,
        "progress": round(session.progress, 2),
    }


@mcp.tool()
def resume_session(session_id: str) -> dict[str, Any]:
    """Resume a paused session.

    Continues the session from where it was paused.

    Args:
        session_id: ID of the session to resume

    Returns:
        Updated session status with next task info
    """
    session_mgr = get_session_manager()
    session = session_mgr.resume_session(session_id)

    if not session:
        return {
            "success": False,
            "error": f"Could not resume session '{session_id}'",
            "hint": "Session may not exist or may not be paused",
        }

    current_task = session.current_task

    return {
        "success": True,
        "session_id": session.id,
        "name": session.name,
        "status": session.status.value,
        "progress": round(session.progress, 2),
        "current_task": {
            "task_id": current_task.task_id,
            "description": current_task.description,
            "agent": current_task.agent_name,
        } if current_task else None,
    }


@mcp.tool()
def cancel_session(session_id: str) -> dict[str, Any]:
    """Cancel a session.

    Cancelled sessions cannot be resumed.

    Args:
        session_id: ID of the session to cancel

    Returns:
        Confirmation of cancellation
    """
    session_mgr = get_session_manager()
    session = session_mgr.cancel_session(session_id)

    if not session:
        return {
            "success": False,
            "error": f"Could not cancel session '{session_id}'",
        }

    return {
        "success": True,
        "session_id": session.id,
        "name": session.name,
        "status": session.status.value,
        "cancelled_at": session.completed_at.isoformat() if session.completed_at else None,
    }


@mcp.tool()
def add_session_task(
    session_id: str,
    description: str,
    agent_name: str | None = None,
) -> dict[str, Any]:
    """Add a new task to an existing session.

    Args:
        session_id: ID of the session
        description: Task description
        agent_name: Optional agent to assign

    Returns:
        Created task information
    """
    session_mgr = get_session_manager()
    coordinator = get_coordinator()

    # Validate agent if provided
    if agent_name:
        agent = coordinator.registry.get_agent(agent_name)
        if agent is None:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "available_agents": [a.name for a in coordinator.registry.list_agents()],
            }

    task = session_mgr.add_task(session_id, description, agent_name)

    if not task:
        return {
            "success": False,
            "error": f"Could not add task to session '{session_id}'",
            "hint": "Session may not exist or may be completed/cancelled",
        }

    return {
        "success": True,
        "session_id": session_id,
        "task_id": task.task_id,
        "description": task.description,
        "agent": task.agent_name,
        "order": task.order,
    }


@mcp.tool()
def start_session_task(session_id: str, task_id: str) -> dict[str, Any]:
    """Mark a session task as in progress.

    Args:
        session_id: ID of the session
        task_id: ID of the task to start

    Returns:
        Updated task status
    """
    session_mgr = get_session_manager()
    task = session_mgr.start_task(session_id, task_id)

    if not task:
        return {
            "success": False,
            "error": f"Could not start task '{task_id}'",
            "hint": "Task may not exist or may not be pending",
        }

    return {
        "success": True,
        "session_id": session_id,
        "task_id": task.task_id,
        "description": task.description,
        "status": task.status.value,
        "started_at": task.started_at.isoformat() if task.started_at else None,
    }


@mcp.tool()
def complete_session_task(
    session_id: str,
    task_id: str,
    result: str | None = None,
    success: bool = True,
) -> dict[str, Any]:
    """Mark a session task as completed or failed.

    If all tasks are complete, the session will be marked as completed
    (or failed if any task failed).

    Args:
        session_id: ID of the session
        task_id: ID of the task to complete
        result: Optional result text or error message
        success: Whether the task succeeded

    Returns:
        Updated task and session status
    """
    session_mgr = get_session_manager()
    task = session_mgr.complete_task(session_id, task_id, result, success)

    if not task:
        return {
            "success": False,
            "error": f"Could not complete task '{task_id}'",
        }

    # Get updated session info
    session = session_mgr.get_session(session_id)
    progress_info = session_mgr.get_session_progress(session_id)

    return {
        "success": True,
        "session_id": session_id,
        "task_id": task.task_id,
        "task_status": task.status.value,
        "task_result": task.result[:100] if task.result and len(task.result) > 100 else task.result,
        "session_status": session.status.value if session else "unknown",
        "session_progress": progress_info["progress"] if progress_info else 0,
        "next_task": progress_info.get("current_task") if progress_info else None,
    }


@mcp.tool()
def get_session_progress(session_id: str) -> dict[str, Any]:
    """Get detailed progress information for a session.

    Args:
        session_id: ID of the session

    Returns:
        Progress details including task counts and current task
    """
    session_mgr = get_session_manager()
    progress = session_mgr.get_session_progress(session_id)

    if not progress:
        return {
            "success": False,
            "error": f"Session '{session_id}' not found",
        }

    return {
        "success": True,
        **progress,
    }


@mcp.tool()
def delete_session_tool(session_id: str) -> dict[str, Any]:
    """Delete a session.

    Args:
        session_id: ID of the session to delete

    Returns:
        Confirmation of deletion
    """
    session_mgr = get_session_manager()
    session = session_mgr.get_session(session_id)

    if not session:
        return {
            "success": False,
            "error": f"Session '{session_id}' not found",
        }

    session_name = session.name
    deleted = session_mgr.delete_session(session_id)

    return {
        "success": deleted,
        "session_id": session_id,
        "session_name": session_name,
        "message": "Session deleted" if deleted else "Failed to delete session",
    }


# === Hooks Tools ===


@mcp.tool()
def list_hooks(
    hook_type: str | None = None,
    enabled_only: bool = False,
) -> dict[str, Any]:
    """List all registered hooks.

    Hooks are pre/post operation interceptors that can modify data
    or abort operations.

    Args:
        hook_type: Optional filter by hook type
        enabled_only: If True, only return enabled hooks

    Returns:
        List of registered hooks with metadata
    """
    hooks_mgr = get_hooks_manager()

    # Parse hook type if provided
    parsed_type = None
    if hook_type is not None:
        try:
            parsed_type = HookType(hook_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid hook type '{hook_type}'",
                "valid_types": [t.value for t in HookType],
            }

    hooks = hooks_mgr.list_hooks(hook_type=parsed_type, enabled_only=enabled_only)

    return {
        "success": True,
        "count": len(hooks),
        "hooks": [
            {
                "name": h.name,
                "type": h.hook_type.value,
                "priority": h.priority,
                "enabled": h.enabled,
                "call_count": h.call_count,
                "error_count": h.error_count,
            }
            for h in hooks
        ],
    }


@mcp.tool()
def get_hook_info(name: str) -> dict[str, Any]:
    """Get detailed information about a hook.

    Args:
        name: Name of the hook

    Returns:
        Hook details including stats and configuration
    """
    hooks_mgr = get_hooks_manager()
    info = hooks_mgr.get_hook_info(name)

    if not info:
        return {
            "success": False,
            "error": f"Hook '{name}' not found",
        }

    return {
        "success": True,
        **info,
    }


@mcp.tool()
def enable_hook(name: str) -> dict[str, Any]:
    """Enable a disabled hook.

    Args:
        name: Name of the hook to enable

    Returns:
        Updated hook status
    """
    hooks_mgr = get_hooks_manager()

    if not hooks_mgr.enable(name):
        return {
            "success": False,
            "error": f"Hook '{name}' not found",
        }

    return {
        "success": True,
        "name": name,
        "enabled": True,
        "message": f"Hook '{name}' is now enabled",
    }


@mcp.tool()
def disable_hook(name: str) -> dict[str, Any]:
    """Disable a hook without removing it.

    Disabled hooks are skipped during execution but remain registered.

    Args:
        name: Name of the hook to disable

    Returns:
        Updated hook status
    """
    hooks_mgr = get_hooks_manager()

    if not hooks_mgr.disable(name):
        return {
            "success": False,
            "error": f"Hook '{name}' not found",
        }

    return {
        "success": True,
        "name": name,
        "enabled": False,
        "message": f"Hook '{name}' is now disabled",
    }


@mcp.tool()
def unregister_hook(name: str) -> dict[str, Any]:
    """Unregister and remove a hook.

    Args:
        name: Name of the hook to remove

    Returns:
        Confirmation of removal
    """
    hooks_mgr = get_hooks_manager()

    if not hooks_mgr.unregister(name):
        return {
            "success": False,
            "error": f"Hook '{name}' not found",
        }

    return {
        "success": True,
        "name": name,
        "message": f"Hook '{name}' has been unregistered",
    }


@mcp.tool()
def get_hooks_stats() -> dict[str, Any]:
    """Get hooks system statistics.

    Returns hook counts, run counts, and error statistics.

    Returns:
        Hooks system statistics
    """
    hooks_mgr = get_hooks_manager()
    stats = hooks_mgr.get_stats()

    return {
        "success": True,
        **stats,
    }


@mcp.tool()
def clear_hooks(hook_type: str | None = None) -> dict[str, Any]:
    """Clear registered hooks.

    Args:
        hook_type: Optional type to clear (None = clear all)

    Returns:
        Number of hooks cleared
    """
    hooks_mgr = get_hooks_manager()

    # Parse hook type if provided
    parsed_type = None
    if hook_type is not None:
        try:
            parsed_type = HookType(hook_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid hook type '{hook_type}'",
                "valid_types": [t.value for t in HookType],
            }

    count = hooks_mgr.clear(parsed_type)

    return {
        "success": True,
        "cleared": count,
        "hook_type": hook_type,
        "message": f"Cleared {count} hooks",
    }


@mcp.tool()
def list_hook_types() -> dict[str, Any]:
    """List all available hook types with descriptions.

    Returns:
        Available hook types and when they are triggered
    """
    hook_descriptions = {
        HookType.PRE_TASK: "Before task execution - can modify task or abort",
        HookType.POST_TASK: "After task completion - can process results",
        HookType.PRE_SPAWN: "Before spawning an agent",
        HookType.POST_SPAWN: "After spawning an agent",
        HookType.ON_AGENT_ERROR: "When an agent encounters an error",
        HookType.PRE_SESSION: "Before a session starts",
        HookType.POST_SESSION: "After a session ends",
        HookType.ON_SESSION_PAUSE: "When a session is paused",
        HookType.ON_SESSION_RESUME: "When a session is resumed",
        HookType.PRE_ROUTE: "Before routing decision",
        HookType.POST_ROUTE: "After routing - can modify agent selection",
        HookType.PRE_MEMORY_STORE: "Before storing to memory",
        HookType.POST_MEMORY_QUERY: "After querying memory - can filter results",
    }

    return {
        "success": True,
        "types": [
            {
                "type": ht.value,
                "description": hook_descriptions.get(ht, ""),
            }
            for ht in HookType
        ],
    }


# === Semantic Memory Tools ===


@mcp.tool()
def semantic_store(
    key: str,
    value: str,
    namespace: str = "default",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Store a memory with semantic embedding for similarity search.

    Stores both the key-value pair and a vector embedding of the value
    for semantic retrieval. Requires 'uv sync --extra semantic' to install
    sentence-transformers.

    Args:
        key: Unique key for the memory
        value: Value to store (this is what gets embedded)
        namespace: Optional namespace for organization
        metadata: Optional metadata dict

    Returns:
        Confirmation of storage with embedding status
    """
    if not semantic_is_available():
        return {
            "success": False,
            "error": "Semantic memory not available",
            "hint": "Install with: uv sync --extra semantic",
            "fallback": "Use memory_store for basic key-value storage",
        }

    memory = get_semantic_memory()
    if memory is None:
        return {
            "success": False,
            "error": "Failed to initialize semantic memory",
        }

    memory.store_semantic(key, value, namespace, metadata)

    return {
        "success": True,
        "key": key,
        "namespace": namespace,
        "has_embedding": True,
        "embedding_dimension": memory.dimension,
        "message": f"Stored '{key}' with semantic embedding in namespace '{namespace}'",
    }


@mcp.tool()
def semantic_search(
    query: str,
    namespace: str | None = None,
    top_k: int = 5,
    min_similarity: float = 0.0,
) -> dict[str, Any]:
    """Search memories by semantic similarity.

    Finds memories whose content is semantically similar to the query,
    even if they don't share exact keywords.

    Args:
        query: Search query text (will be embedded)
        namespace: Optional namespace to search within
        top_k: Maximum number of results to return
        min_similarity: Minimum similarity threshold (0-1)

    Returns:
        List of semantically similar memories with similarity scores
    """
    if not semantic_is_available():
        return {
            "success": False,
            "error": "Semantic memory not available",
            "hint": "Install with: uv sync --extra semantic",
            "fallback": "Use memory_query for pattern-based search",
        }

    memory = get_semantic_memory()
    if memory is None:
        return {
            "success": False,
            "error": "Failed to initialize semantic memory",
        }

    results = memory.search_semantic(query, namespace, top_k, min_similarity)

    return {
        "success": True,
        "query": query,
        "namespace": namespace,
        "count": len(results),
        "results": [
            {
                "key": r.key,
                "value": r.value[:200] + "..." if len(r.value) > 200 else r.value,
                "namespace": r.namespace,
                "similarity": round(r.similarity, 4),
                "metadata": r.metadata,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ],
    }


@mcp.tool()
def semantic_store_batch(
    items: list[dict[str, Any]],
    namespace: str = "default",
) -> dict[str, Any]:
    """Store multiple memories with embeddings efficiently.

    Uses batch embedding for better performance when storing many items.

    Args:
        items: List of dicts with 'key', 'value', and optional 'metadata'
        namespace: Namespace for all items

    Returns:
        Count of stored items with embedding stats
    """
    if not semantic_is_available():
        return {
            "success": False,
            "error": "Semantic memory not available",
            "hint": "Install with: uv sync --extra semantic",
        }

    memory = get_semantic_memory()
    if memory is None:
        return {
            "success": False,
            "error": "Failed to initialize semantic memory",
        }

    # Validate items
    if not items:
        return {
            "success": False,
            "error": "No items provided",
        }

    for i, item in enumerate(items):
        if "key" not in item or "value" not in item:
            return {
                "success": False,
                "error": f"Item {i} missing required 'key' or 'value' field",
            }

    count = memory.store_semantic_batch(items, namespace)

    return {
        "success": True,
        "stored_count": count,
        "namespace": namespace,
        "embedding_dimension": memory.dimension,
        "message": f"Stored {count} items with semantic embeddings",
    }


@mcp.tool()
def semantic_stats() -> dict[str, Any]:
    """Get semantic memory statistics.

    Returns counts of memories with embeddings, embedding model info,
    and namespace breakdown.

    Returns:
        Semantic memory statistics
    """
    if not semantic_is_available():
        return {
            "success": False,
            "available": False,
            "error": "Semantic memory not available",
            "hint": "Install with: uv sync --extra semantic",
        }

    memory = get_semantic_memory()
    if memory is None:
        return {
            "success": False,
            "available": True,
            "error": "Failed to initialize semantic memory",
        }

    stats = memory.get_stats()

    return {
        "success": True,
        "available": True,
        **stats,
    }


@mcp.tool()
def semantic_reindex() -> dict[str, Any]:
    """Regenerate embeddings for all memories.

    Useful after changing the embedding model or to ensure
    all memories have up-to-date embeddings.

    Returns:
        Count of reindexed memories
    """
    if not semantic_is_available():
        return {
            "success": False,
            "error": "Semantic memory not available",
            "hint": "Install with: uv sync --extra semantic",
        }

    memory = get_semantic_memory()
    if memory is None:
        return {
            "success": False,
            "error": "Failed to initialize semantic memory",
        }

    count = memory.reindex_all()

    return {
        "success": True,
        "reindexed_count": count,
        "embedding_dimension": memory.dimension,
        "message": f"Regenerated embeddings for {count} memories",
    }


@mcp.tool()
def semantic_delete(key: str) -> dict[str, Any]:
    """Delete a memory and its embedding.

    Removes both the key-value pair and its vector embedding.

    Args:
        key: Key of the memory to delete

    Returns:
        Confirmation of deletion
    """
    if not semantic_is_available():
        return {
            "success": False,
            "error": "Semantic memory not available",
            "hint": "Install with: uv sync --extra semantic",
        }

    memory = get_semantic_memory()
    if memory is None:
        return {
            "success": False,
            "error": "Failed to initialize semantic memory",
        }

    deleted = memory.delete_semantic(key)

    return {
        "success": deleted,
        "key": key,
        "message": f"Deleted memory '{key}'" if deleted else f"Memory '{key}' not found",
    }


# === MCP Resources ===


@mcp.resource("squad://agents")
def list_agents_resource() -> str:
    """List all available agents with their metadata.

    Returns a YAML-formatted list of all agents including their
    names, descriptions, models, colors, and trigger keywords.
    """
    import yaml

    coordinator = get_coordinator()
    agents = coordinator.registry.list_agents()

    agents_data = []
    for agent in agents:
        agents_data.append({
            "name": agent.name,
            "description": agent.description.split("\n")[0][:100],  # First line, max 100 chars
            "model": agent.model.value,
            "color": agent.color,
            "triggers": agent.triggers[:10],  # First 10 triggers
            "file": agent.file_path,
        })

    return yaml.dump({"agents": agents_data, "total": len(agents_data)}, default_flow_style=False)


@mcp.resource("squad://agents/{agent_name}")
def get_agent_resource(agent_name: str) -> str:
    """Get the full content of a specific agent file.

    Args:
        agent_name: Name of the agent (e.g., 'python-developer')

    Returns the complete markdown content of the agent definition.
    """
    coordinator = get_coordinator()
    agent = coordinator.registry.get_agent(agent_name)

    if agent is None:
        available = [a.name for a in coordinator.registry.list_agents()]
        return f"Agent '{agent_name}' not found.\n\nAvailable agents:\n" + "\n".join(f"- {a}" for a in available)

    # Read the full agent file
    from pathlib import Path
    agent_path = Path(agent.file_path)
    if agent_path.exists():
        return agent_path.read_text()
    return f"Agent file not found: {agent.file_path}"


@mcp.resource("squad://skills")
def list_skills_resource() -> str:
    """List all available skills.

    Returns a list of all skill directories and their SKILL.md files.
    """
    import yaml

    skills_dir = get_skills_dir()
    skills_data = []

    if skills_dir.exists():
        for skill_path in skills_dir.iterdir():
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    # Read first few lines for description
                    content = skill_file.read_text()
                    lines = content.split("\n")
                    title = lines[0].lstrip("# ") if lines else skill_path.name
                    description = ""
                    for line in lines[1:10]:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("---"):
                            description = line[:100]
                            break

                    skills_data.append({
                        "name": skill_path.name,
                        "title": title,
                        "description": description,
                        "file": str(skill_file),
                    })

    return yaml.dump({"skills": skills_data, "total": len(skills_data)}, default_flow_style=False)


@mcp.resource("squad://skills/{skill_name}")
def get_skill_resource(skill_name: str) -> str:
    """Get the full content of a specific skill file.

    Args:
        skill_name: Name of the skill directory (e.g., 'data-pipeline-patterns')

    Returns the complete markdown content of the SKILL.md file.
    """
    skills_dir = get_skills_dir()
    skill_file = skills_dir / skill_name / "SKILL.md"

    if skill_file.exists():
        return skill_file.read_text()

    # List available skills for helpful error message
    available = []
    if skills_dir.exists():
        available = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

    return f"Skill '{skill_name}' not found.\n\nAvailable skills:\n" + "\n".join(f"- {s}" for s in available)


@mcp.resource("squad://commands")
def list_commands_resource() -> str:
    """List all available commands organized by category.

    Returns a YAML-formatted list of all commands with their metadata.
    """
    import yaml

    commands_dir = get_commands_dir()
    commands_data = {}

    if commands_dir.exists():
        for category_path in commands_dir.iterdir():
            if category_path.is_dir():
                category = category_path.name
                commands_data[category] = []

                for cmd_file in category_path.glob("*.md"):
                    content = cmd_file.read_text()

                    # Parse frontmatter for description
                    description = ""
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            import yaml as yaml_parser
                            try:
                                fm = yaml_parser.safe_load(parts[1])
                                description = fm.get("description", "")[:100] if fm else ""
                            except Exception:
                                pass

                    commands_data[category].append({
                        "name": cmd_file.stem,
                        "description": description,
                        "file": str(cmd_file),
                    })

    return yaml.dump({"commands": commands_data, "total_categories": len(commands_data)}, default_flow_style=False)


@mcp.resource("squad://commands/{category}/{command_name}")
def get_command_resource(category: str, command_name: str) -> str:
    """Get the full content of a specific command file.

    Args:
        category: Command category (e.g., 'data-engineering')
        command_name: Name of the command (without .md extension)

    Returns the complete markdown content of the command file.
    """
    commands_dir = get_commands_dir()
    cmd_file = commands_dir / category / f"{command_name}.md"

    if cmd_file.exists():
        return cmd_file.read_text()

    # Try without .md extension in name
    if not command_name.endswith(".md"):
        cmd_file_alt = commands_dir / category / command_name
        if cmd_file_alt.exists():
            return cmd_file_alt.read_text()

    # List available for helpful error message
    available = []
    if commands_dir.exists():
        for cat_path in commands_dir.iterdir():
            if cat_path.is_dir():
                for f in cat_path.glob("*.md"):
                    available.append(f"{cat_path.name}/{f.stem}")

    return f"Command '{category}/{command_name}' not found.\n\nAvailable commands:\n" + "\n".join(f"- {c}" for c in available)


def main():
    """Run the MCP server."""
    import logging

    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize tracing (handles its own cleanup via signal handlers)
    from orchestrator.tracing import init as tracing_init

    if tracing_init():
        logging.getLogger(__name__).info("Langfuse tracing initialized successfully")
    else:
        logging.getLogger(__name__).warning("Langfuse tracing not available")

    mcp.run()


if __name__ == "__main__":
    main()
