"""Tests for orchestrator/scheduler.py - TaskScheduler and CircuitBreaker."""

import time

import pytest

from orchestrator.scheduler import CircuitBreaker, CircuitState, TaskScheduler
from orchestrator.types import Task, TaskStatus


class TestCircuitBreakerState:
    """Tests for CircuitBreaker state management."""

    def test_starts_closed(self, circuit_breaker):
        """Circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitState.CLOSED

    def test_allow_request_closed(self, circuit_breaker):
        """Requests are allowed when circuit is CLOSED."""
        assert circuit_breaker.allow_request() is True

    def test_trips_after_threshold(self, circuit_breaker):
        """Circuit opens after failure threshold is reached."""
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == CircuitState.OPEN

    def test_blocks_when_open(self, circuit_breaker):
        """Requests are blocked when circuit is OPEN."""
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.allow_request() is False

    def test_half_open_after_timeout(self, circuit_breaker):
        """Circuit transitions to HALF_OPEN after reset timeout."""
        for _ in range(3):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == CircuitState.OPEN

        # Wait for timeout (0.1s in test fixture)
        time.sleep(0.15)

        # Accessing state property triggers timeout check
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    def test_closes_on_success_in_half_open(self, circuit_breaker):
        """Circuit closes on success while in HALF_OPEN."""
        for _ in range(3):
            circuit_breaker.record_failure()

        time.sleep(0.15)
        circuit_breaker.allow_request()  # Trigger half-open
        circuit_breaker.record_success()

        assert circuit_breaker.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self, circuit_breaker):
        """Circuit reopens on failure while in HALF_OPEN."""
        for _ in range(3):
            circuit_breaker.record_failure()

        time.sleep(0.15)
        circuit_breaker.allow_request()  # Trigger half-open
        circuit_breaker.record_failure()

        assert circuit_breaker.state == CircuitState.OPEN

    def test_success_resets_failure_count(self, circuit_breaker):
        """Success in CLOSED state resets failure count."""
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_success()
        circuit_breaker.record_failure()

        # Should not be open (only 1 failure after reset)
        assert circuit_breaker.state == CircuitState.CLOSED


class TestCircuitBreakerStatus:
    """Tests for CircuitBreaker status reporting."""

    def test_get_status_closed(self, circuit_breaker):
        """get_status returns correct info when CLOSED."""
        status = circuit_breaker.get_status()

        assert status["name"] == "test-breaker"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 3

    def test_get_status_open(self, circuit_breaker):
        """get_status shows failure info when OPEN."""
        for _ in range(3):
            circuit_breaker.record_failure()

        status = circuit_breaker.get_status()

        assert status["state"] == "open"
        assert status["failure_count"] == 3
        assert status["last_failure"] is not None


class TestTaskSchedulerBasic:
    """Tests for basic TaskScheduler operations."""

    def test_add_task_no_dependencies(self, scheduler, create_task):
        """Adding task without dependencies works."""
        task = create_task(task_id="t1")
        scheduler.add_task(task)

        assert "t1" in scheduler._tasks

    def test_add_task_with_dependencies(self, scheduler, create_task):
        """Adding task with dependencies builds graph correctly."""
        task1 = create_task(task_id="t1")
        task2 = create_task(task_id="t2")

        scheduler.add_task(task1)
        scheduler.add_task(task2, depends_on=["t1"])

        assert "t1" in scheduler._dependencies["t2"]
        assert "t2" in scheduler._dependents["t1"]

    def test_remove_task_cleans_dependencies(self, scheduler, create_task):
        """Removing task cleans up both dependency directions."""
        task1 = create_task(task_id="t1")
        task2 = create_task(task_id="t2")
        task3 = create_task(task_id="t3")

        scheduler.add_task(task1)
        scheduler.add_task(task2, depends_on=["t1"])
        scheduler.add_task(task3, depends_on=["t1"])

        scheduler.remove_task("t1")

        assert "t1" not in scheduler._tasks
        assert "t1" not in scheduler._dependencies["t2"]
        assert "t1" not in scheduler._dependencies["t3"]


class TestTaskSchedulerReadyTasks:
    """Tests for ready task detection."""

    def test_get_ready_tasks_no_dependencies(self, scheduler, create_task):
        """All pending tasks are ready when no dependencies."""
        for i in range(3):
            scheduler.add_task(create_task(task_id=f"t{i}"))

        ready = scheduler.get_ready_tasks()
        assert len(ready) == 3

    def test_get_ready_tasks_with_dependencies(self, scheduler, create_task):
        """Only tasks with satisfied dependencies are ready."""
        t1 = create_task(task_id="t1")
        t2 = create_task(task_id="t2")
        t3 = create_task(task_id="t3")

        scheduler.add_task(t1)
        scheduler.add_task(t2, depends_on=["t1"])
        scheduler.add_task(t3, depends_on=["t2"])

        # Only t1 is ready initially
        ready = scheduler.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t1"

    def test_get_ready_tasks_after_completion(self, scheduler, create_task):
        """Completing task makes dependents ready."""
        t1 = create_task(task_id="t1")
        t2 = create_task(task_id="t2")

        scheduler.add_task(t1)
        scheduler.add_task(t2, depends_on=["t1"])

        scheduler.mark_completed("t1", success=True)

        ready = scheduler.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "t2"

    def test_get_ready_tasks_excludes_completed(self, scheduler, create_task):
        """Completed tasks are not included in ready list."""
        t1 = create_task(task_id="t1")
        scheduler.add_task(t1)
        scheduler.mark_completed("t1", success=True)

        ready = scheduler.get_ready_tasks()
        assert len(ready) == 0


class TestTaskSchedulerTopologicalSort:
    """Tests for topological sorting."""

    def test_topological_sort_valid(self, scheduler, create_task):
        """Topological sort returns correct order."""
        t1 = create_task(task_id="t1", description="First")
        t2 = create_task(task_id="t2", description="Second")
        t3 = create_task(task_id="t3", description="Third")

        scheduler.add_task(t1)
        scheduler.add_task(t2, depends_on=["t1"])
        scheduler.add_task(t3, depends_on=["t2"])

        order = scheduler.topological_sort()
        ids = [t.id for t in order]

        # t1 must come before t2, t2 before t3
        assert ids.index("t1") < ids.index("t2")
        assert ids.index("t2") < ids.index("t3")

    def test_topological_sort_circular_dependency_raises(self, scheduler, create_task):
        """Circular dependency raises ValueError."""
        t1 = create_task(task_id="t1")
        t2 = create_task(task_id="t2")
        t3 = create_task(task_id="t3")

        scheduler.add_task(t1, depends_on=["t3"])
        scheduler.add_task(t2, depends_on=["t1"])
        scheduler.add_task(t3, depends_on=["t2"])

        with pytest.raises(ValueError, match="Circular dependency"):
            scheduler.topological_sort()


class TestTaskSchedulerCompletion:
    """Tests for task completion."""

    def test_mark_completed_success(self, scheduler, create_task):
        """mark_completed with success updates status."""
        task = create_task(task_id="t1")
        scheduler.add_task(task)

        scheduler.mark_completed("t1", success=True)

        assert scheduler._tasks["t1"].status == TaskStatus.COMPLETED
        assert "t1" in scheduler._completed

    def test_mark_completed_failure(self, scheduler, create_task):
        """mark_completed with failure updates status."""
        task = create_task(task_id="t1")
        scheduler.add_task(task)

        scheduler.mark_completed("t1", success=False)

        assert scheduler._tasks["t1"].status == TaskStatus.FAILED
        assert "t1" in scheduler._failed

    def test_mark_completed_nonexistent_task(self, scheduler):
        """mark_completed on missing task is safe (no-op)."""
        scheduler.mark_completed("nonexistent", success=True)
        # Should not raise


class TestTaskSchedulerCircuitBreaker:
    """Tests for circuit breaker integration."""

    def test_can_execute_checks_dependencies(self, scheduler, create_task):
        """can_execute returns False if dependencies not satisfied."""
        t1 = create_task(task_id="t1")
        t2 = create_task(task_id="t2")

        scheduler.add_task(t1)
        scheduler.add_task(t2, depends_on=["t1"])

        assert scheduler.can_execute("t1") is True
        assert scheduler.can_execute("t2") is False

    def test_can_execute_checks_circuit_breaker(self, scheduler, create_task):
        """can_execute returns False if circuit breaker is OPEN."""
        task = create_task(task_id="t1", agent_name="test-agent")
        scheduler.add_task(task)

        # Get and trip the circuit breaker
        cb = scheduler.get_circuit_breaker("test-agent")
        for _ in range(3):
            cb.record_failure()

        assert scheduler.can_execute("t1") is False

    def test_get_circuit_breaker_creates_if_missing(self, scheduler):
        """get_circuit_breaker creates breaker if not exists."""
        cb = scheduler.get_circuit_breaker("new-agent")

        assert cb is not None
        assert cb.name == "agent-new-agent"

    def test_completion_updates_circuit_breaker(self, scheduler, create_task):
        """Completing task updates agent's circuit breaker."""
        task = create_task(task_id="t1", agent_name="agent1")
        scheduler.add_task(task)
        cb = scheduler.get_circuit_breaker("agent1")

        # Fail the task
        scheduler.mark_completed("t1", success=False)
        assert cb._failure_count == 1


class TestTaskSchedulerGraph:
    """Tests for task graph operations."""

    def test_get_task_graph(self, scheduler, create_task):
        """get_task_graph returns complete graph structure."""
        t1 = create_task(task_id="t1")
        t2 = create_task(task_id="t2")

        scheduler.add_task(t1)
        scheduler.add_task(t2, depends_on=["t1"])

        graph = scheduler.get_task_graph()

        assert graph["total_tasks"] == 2
        assert graph["pending"] == 2
        assert len(graph["tasks"]) == 2

    def test_clear_resets_all(self, scheduler, create_task):
        """clear() removes all tasks and resets state."""
        for i in range(5):
            scheduler.add_task(create_task(task_id=f"t{i}"))

        scheduler.mark_completed("t0", success=True)
        scheduler.clear()

        assert len(scheduler._tasks) == 0
        assert len(scheduler._completed) == 0
        assert len(scheduler._failed) == 0
        assert len(scheduler._dependencies) == 0
        assert len(scheduler._dependents) == 0
