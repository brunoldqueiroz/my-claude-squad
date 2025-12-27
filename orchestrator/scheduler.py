"""Advanced task scheduling with dependency resolution and fault tolerance.

Provides:
- TaskScheduler: Manages task dependencies and execution order
- CircuitBreaker: Prevents cascading failures
"""

import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, TypeVar

from .types import Task, TaskStatus

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """State of a circuit breaker."""

    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"  # Failures exceeded threshold, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Prevents cascading failures by blocking requests after repeated failures.

    States:
    - CLOSED: Normal operation, all requests allowed
    - OPEN: Too many failures, all requests blocked
    - HALF_OPEN: Testing recovery, allowing limited requests
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        reset_timeout_seconds: float = 60.0,
        half_open_max_requests: int = 1,
    ):
        """Initialize the circuit breaker.

        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of failures before opening
            reset_timeout_seconds: Seconds to wait before trying half-open
            half_open_max_requests: Max requests allowed in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.half_open_max_requests = half_open_max_requests

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_requests = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout-based transitions."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._half_open_requests = 0
                logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN (timeout reached)")
        return self._state

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.reset_timeout_seconds

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == CircuitState.OPEN

    def allow_request(self) -> bool:
        """Check if a request should be allowed through.

        Returns:
            True if request is allowed, False if blocked
        """
        state = self.state

        if state == CircuitState.CLOSED:
            return True

        if state == CircuitState.OPEN:
            return False

        # HALF_OPEN: allow limited requests
        if self._half_open_requests < self.half_open_max_requests:
            self._half_open_requests += 1
            return True

        return False

    def record_success(self) -> None:
        """Record a successful request."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_max_requests:
                self._reset()
                logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED (success)")
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._trip()
            logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (failure during recovery)")
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._trip()
                logger.warning(
                    f"Circuit {self.name}: CLOSED -> OPEN "
                    f"(failures: {self._failure_count}/{self.failure_threshold})"
                )

    def _trip(self) -> None:
        """Trip the circuit to OPEN state."""
        self._state = CircuitState.OPEN
        self._success_count = 0
        self._half_open_requests = 0

    def _reset(self) -> None:
        """Reset the circuit to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_requests = 0
        self._last_failure_time = None

    def get_status(self) -> dict[str, Any]:
        """Get current status of the circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "reset_timeout_seconds": self.reset_timeout_seconds,
            "last_failure": (
                datetime.fromtimestamp(self._last_failure_time).isoformat()
                if self._last_failure_time
                else None
            ),
        }


class TaskScheduler:
    """Schedules tasks with dependency resolution and topological ordering.

    Features:
    - Task dependency graph management
    - Topological sort for execution order
    - Ready task detection (all dependencies satisfied)
    - Circuit breaker integration per agent
    """

    def __init__(self):
        """Initialize the task scheduler."""
        # Task storage
        self._tasks: dict[str, Task] = {}

        # Dependency graph: task_id -> set of task_ids it depends on
        self._dependencies: dict[str, set[str]] = defaultdict(set)

        # Reverse dependency graph: task_id -> set of task_ids that depend on it
        self._dependents: dict[str, set[str]] = defaultdict(set)

        # Completed tasks (for dependency resolution)
        self._completed: set[str] = set()

        # Failed tasks
        self._failed: set[str] = set()

        # Circuit breakers per agent
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

    def add_task(
        self,
        task: Task,
        depends_on: list[str] | None = None,
    ) -> None:
        """Add a task to the scheduler.

        Args:
            task: Task to add
            depends_on: List of task IDs this task depends on
        """
        self._tasks[task.id] = task

        if depends_on:
            for dep_id in depends_on:
                self._dependencies[task.id].add(dep_id)
                self._dependents[dep_id].add(task.id)

        logger.debug(
            f"Added task {task.id} with {len(depends_on or [])} dependencies"
        )

    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the scheduler.

        Args:
            task_id: ID of task to remove

        Returns:
            True if task was removed, False if not found
        """
        if task_id not in self._tasks:
            return False

        # Remove from dependency graphs
        for dep_id in self._dependencies[task_id]:
            self._dependents[dep_id].discard(task_id)
        del self._dependencies[task_id]

        for dependent_id in self._dependents[task_id]:
            self._dependencies[dependent_id].discard(task_id)
        del self._dependents[task_id]

        # Remove task
        del self._tasks[task_id]
        self._completed.discard(task_id)
        self._failed.discard(task_id)

        return True

    def get_ready_tasks(self) -> list[Task]:
        """Get tasks that are ready to execute (all dependencies satisfied).

        Returns:
            List of tasks ready for execution
        """
        ready = []
        for task_id, task in self._tasks.items():
            if task_id in self._completed or task_id in self._failed:
                continue

            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps = self._dependencies.get(task_id, set())
            if all(dep_id in self._completed for dep_id in deps):
                ready.append(task)

        return ready

    def topological_sort(self) -> list[Task]:
        """Get all tasks in topological order (respecting dependencies).

        Returns:
            Tasks sorted so dependencies come before dependents

        Raises:
            ValueError: If there's a circular dependency
        """
        # Kahn's algorithm
        in_degree: dict[str, int] = defaultdict(int)
        for task_id in self._tasks:
            in_degree[task_id] = len(self._dependencies.get(task_id, set()))

        # Start with tasks that have no dependencies
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        result: list[Task] = []

        while queue:
            task_id = queue.pop(0)
            result.append(self._tasks[task_id])

            # Reduce in-degree for dependents
            for dependent_id in self._dependents.get(task_id, set()):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        if len(result) != len(self._tasks):
            raise ValueError("Circular dependency detected in task graph")

        return result

    def mark_completed(self, task_id: str, success: bool = True) -> None:
        """Mark a task as completed.

        Args:
            task_id: ID of completed task
            success: Whether task succeeded
        """
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]

        if success:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            self._completed.add(task_id)

            # Record success on circuit breaker if agent assigned
            if task.agent_name and task.agent_name in self._circuit_breakers:
                self._circuit_breakers[task.agent_name].record_success()
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self._failed.add(task_id)

            # Record failure on circuit breaker if agent assigned
            if task.agent_name and task.agent_name in self._circuit_breakers:
                self._circuit_breakers[task.agent_name].record_failure()

    def can_execute(self, task_id: str) -> bool:
        """Check if a task can be executed.

        Considers both dependencies and circuit breaker state.

        Args:
            task_id: Task ID to check

        Returns:
            True if task can be executed
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]

        # Check dependencies
        deps = self._dependencies.get(task_id, set())
        if not all(dep_id in self._completed for dep_id in deps):
            return False

        # Check circuit breaker
        if task.agent_name:
            cb = self._circuit_breakers.get(task.agent_name)
            if cb and not cb.allow_request():
                logger.warning(
                    f"Task {task_id} blocked by circuit breaker for agent {task.agent_name}"
                )
                return False

        return True

    def get_circuit_breaker(self, agent_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            CircuitBreaker for the agent
        """
        if agent_name not in self._circuit_breakers:
            self._circuit_breakers[agent_name] = CircuitBreaker(
                name=f"agent-{agent_name}",
                failure_threshold=3,
                reset_timeout_seconds=60.0,
            )
        return self._circuit_breakers[agent_name]

    def get_task_graph(self) -> dict[str, Any]:
        """Get the current task dependency graph.

        Returns:
            Dictionary representation of the task graph
        """
        return {
            "total_tasks": len(self._tasks),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "pending": len(self._tasks) - len(self._completed) - len(self._failed),
            "tasks": [
                {
                    "id": task.id,
                    "description": task.description[:50] + "..." if len(task.description) > 50 else task.description,
                    "agent": task.agent_name,
                    "status": task.status.value,
                    "depends_on": list(self._dependencies.get(task.id, set())),
                    "dependents": list(self._dependents.get(task.id, set())),
                }
                for task in self._tasks.values()
            ],
            "circuit_breakers": [
                cb.get_status() for cb in self._circuit_breakers.values()
            ],
        }

    def clear(self) -> None:
        """Clear all tasks and reset state."""
        self._tasks.clear()
        self._dependencies.clear()
        self._dependents.clear()
        self._completed.clear()
        self._failed.clear()
