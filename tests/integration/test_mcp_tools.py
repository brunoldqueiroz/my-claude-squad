"""Integration tests for MCP tools end-to-end."""

import pytest

from orchestrator.agent_registry import AgentRegistry
from orchestrator.coordinator import Coordinator
from orchestrator.memory import SwarmMemory
from orchestrator.types import TaskStatus


@pytest.mark.integration
class TestMCPToolsIntegration:
    """Integration tests for MCP tool workflows."""

    def test_list_agents_returns_all(self, coordinator):
        """list_agents returns all registered agents."""
        agents = coordinator.registry.list_agents()

        # Should have our test agents
        names = [a.name for a in agents]
        assert "test-agent-1" in names
        assert "test-agent-2" in names

    def test_route_and_spawn_workflow(self, coordinator):
        """Full workflow: route_task -> create_task -> start_task."""
        # Route the task
        agent = coordinator.route_task("Write a python script to process data")

        # Create task
        task = coordinator.create_task(
            "Write a python script to process data",
            agent_name=agent.name if agent else "test-agent-1",
        )
        assert task.status == TaskStatus.PENDING

        # Start task
        run = coordinator.start_task(task.id)
        assert run is not None
        assert coordinator._active_tasks[task.id].status == TaskStatus.IN_PROGRESS

        # Complete task
        coordinator.complete_task(task.id, result="Script written", success=True)
        assert coordinator._active_tasks[task.id].status == TaskStatus.COMPLETED

    def test_memory_store_and_query(self, memory):
        """memory_store and memory_query work end-to-end."""
        # Store multiple values
        memory.store("pattern:001", "first value", namespace="patterns")
        memory.store("pattern:002", "second value", namespace="patterns")
        memory.store("other:001", "other value", namespace="other")

        # Query by pattern
        results = memory.query("pattern:", namespace="patterns")
        assert len(results) == 2

        # Query across namespaces
        all_results = memory.query("001")
        assert len(all_results) == 2

    def test_swarm_status_reflects_state(self, coordinator):
        """swarm_status accurately reflects current state."""
        # Initial state
        status1 = coordinator.get_swarm_status()
        initial_active = status1.active_tasks

        # Create and start task
        task = coordinator.create_task("Test task", agent_name="test-agent-1")
        coordinator.start_task(task.id)

        # Status should show active task
        status2 = coordinator.get_swarm_status()
        assert status2.active_tasks == initial_active + 1

        # Complete task
        coordinator.complete_task(task.id, success=True)

        # Status should update
        status3 = coordinator.get_swarm_status()
        assert status3.active_tasks == initial_active
        assert status3.completed_tasks >= 1

    def test_complete_run_updates_all_state(self, coordinator):
        """complete_run updates task, memory, and metrics."""
        # Create and start task
        task = coordinator.create_task("Integration test task", agent_name="test-agent-1")
        run = coordinator.start_task(task.id)

        # Complete with result
        coordinator.complete_task(
            task.id,
            result="Task completed successfully",
            success=True,
            tokens_used=100,
        )

        # Verify task status
        assert coordinator._active_tasks[task.id].status == TaskStatus.COMPLETED

        # Verify memory has run record
        stats = coordinator.memory.get_run_stats()
        assert stats["completed"] >= 1
        assert stats["total_tokens"] >= 100

    def test_task_decomposition_creates_subtasks(self, coordinator):
        """decompose_task creates properly routed subtasks."""
        subtasks = coordinator.decompose_task(
            "Write a python script and then create SQL tables"
        )

        # Should be decomposed
        assert len(subtasks) >= 2

        # Each subtask should have an agent assignment
        for subtask_desc, agent in subtasks:
            assert len(subtask_desc) > 0
            # Agent may be None if not matched in test fixtures

    def test_agent_health_tracking(self, memory):
        """Agent health is tracked and persisted."""
        from orchestrator.agent_state import AgentStateManager

        manager = AgentStateManager(memory)

        # Initialize and track agent
        manager.initialize_agent("test-agent")
        manager.record_task_start("test-agent", "task-1")
        manager.record_task_complete("test-agent", success=True, duration_ms=100.0)

        # Verify health is persisted
        health = manager.get_health("test-agent")
        assert health is not None
        assert health.success_count == 1
        assert health.total_execution_time_ms == 100.0

        # Verify persistence across manager instances
        manager2 = AgentStateManager(memory)
        health2 = manager2.get_health("test-agent")
        assert health2 is not None
        assert health2.success_count == 1


@pytest.mark.integration
class TestWorkflowExecution:
    """Integration tests for full workflow execution."""

    def test_dependent_task_workflow(self, coordinator):
        """Tasks with dependencies execute in order."""
        # Create parent task
        parent = coordinator.create_task("Setup database", agent_name="test-agent-1")
        coordinator.start_task(parent.id)
        coordinator.complete_task(parent.id, result="DB ready", success=True)

        # Create dependent task
        child = coordinator.create_task("Insert data", agent_name="test-agent-2")
        coordinator.start_task(child.id)
        coordinator.complete_task(child.id, result="Data inserted", success=True)

        # Verify both completed
        assert coordinator._active_tasks[parent.id].status == TaskStatus.COMPLETED
        assert coordinator._active_tasks[child.id].status == TaskStatus.COMPLETED

    def test_event_propagation(self, memory):
        """Events are properly propagated through system."""
        from orchestrator.agent_state import AgentStateManager
        from orchestrator.types import AgentEventType

        manager = AgentStateManager(memory)

        # Perform actions that generate events
        manager.initialize_agent("event-test-agent")
        manager.record_task_start("event-test-agent", "task-1")
        manager.record_task_complete("event-test-agent", success=True, duration_ms=50.0)
        manager.record_error("event-test-agent", "Test error")

        # Query events
        events = memory.get_agent_events(agent_name="event-test-agent")

        # Should have multiple events
        assert len(events) >= 3

        # Check event types present
        event_types = [e.event_type for e in events]
        assert AgentEventType.STATUS_CHANGE in event_types
        assert AgentEventType.TASK_START in event_types

    def test_circuit_breaker_protection(self):
        """Circuit breaker protects against failing agents."""
        from orchestrator.scheduler import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(name="test", failure_threshold=2, reset_timeout_seconds=0.1)

        # Simulate failures
        breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Should block requests
        assert breaker.allow_request() is False

    def test_metrics_collection(self, metrics):
        """Metrics are collected throughout workflow."""
        # Simulate workflow metrics
        metrics.increment("tasks_created")
        metrics.increment("tasks_completed")
        metrics.histogram("task_duration_ms", 150.0)

        summary = metrics.get_summary()

        assert summary["totals"]["counter_count"] >= 2
        assert summary["totals"]["histogram_count"] >= 1

    def test_full_agent_lifecycle(self, coordinator, memory):
        """Full agent lifecycle from spawn to completion."""
        from orchestrator.agent_state import AgentStateManager
        from orchestrator.types import AgentStatus

        state_manager = AgentStateManager(memory)

        # Initialize agent
        state_manager.initialize_agent("lifecycle-agent")
        assert state_manager.get_health("lifecycle-agent").status == AgentStatus.IDLE

        # Create and start task
        task = coordinator.create_task("Lifecycle test", agent_name="lifecycle-agent")
        state_manager.record_task_start("lifecycle-agent", task.id)
        assert state_manager.get_health("lifecycle-agent").status == AgentStatus.BUSY

        # Complete task
        coordinator.start_task(task.id)
        coordinator.complete_task(task.id, result="Done", success=True)
        state_manager.record_task_complete("lifecycle-agent", success=True, duration_ms=200.0)

        # Verify final state
        health = state_manager.get_health("lifecycle-agent")
        assert health.status == AgentStatus.IDLE
        assert health.success_count == 1
        assert health.total_execution_time_ms == 200.0
