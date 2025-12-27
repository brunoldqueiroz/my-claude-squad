"""FastMCP server for my-claude-squad orchestration."""

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .agent_state import AgentStateManager
from .coordinator import Coordinator
from .events import get_event_bus, create_event
from .metrics import get_metrics_collector
from .scheduler import TaskScheduler
from .tracing import get_langfuse, is_enabled as langfuse_enabled
from .types import (
    AgentEventType,
    AgentStatus,
    DecompositionResult,
    ExecutionMode,
    Subtask,
    Task,
    TaskStatus,
)

# Initialize MCP server
mcp = FastMCP("my-claude-squad")

# Initialize singletons (will be set up on first use)
_coordinator: Coordinator | None = None
_agent_state_manager: AgentStateManager | None = None
_scheduler: TaskScheduler | None = None


def get_coordinator() -> Coordinator:
    """Get or create the coordinator singleton."""
    global _coordinator
    if _coordinator is None:
        # Find the project root (where agents/ directory is)
        current = Path(__file__).parent.parent
        agents_dir = current / "agents"
        _coordinator = Coordinator(agents_dir=agents_dir)
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
    from .tracing import init as tracing_init

    if tracing_init():
        logging.getLogger(__name__).info("Langfuse tracing initialized successfully")
    else:
        logging.getLogger(__name__).warning("Langfuse tracing not available")

    mcp.run()


if __name__ == "__main__":
    main()
