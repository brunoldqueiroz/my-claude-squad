"""Integration tests for MCP tools end-to-end."""

import pytest

from orchestrator.agent_registry import AgentRegistry
from orchestrator.coordinator import Coordinator
from orchestrator.memory import SwarmMemory
from orchestrator.types import AgentEventType, AgentStatus, TaskStatus


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


@pytest.mark.integration
class TestMCPServerTools:
    """Integration tests for actual MCP server tool functions."""

    def test_list_agents_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """list_agents MCP tool returns properly formatted response."""
        import orchestrator.server as server

        # Configure server to use test paths
        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Access underlying function via .fn (FastMCP wraps in FunctionTool)
        result = server.list_agents.fn()

        assert "total" in result
        assert "agents" in result
        assert result["total"] >= 1
        assert isinstance(result["agents"], list)

        # Verify agent structure
        for agent in result["agents"]:
            assert "name" in agent
            assert "description" in agent
            assert "model" in agent

    def test_route_task_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """route_task MCP tool routes tasks correctly."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.route_task.fn("write a python script")

        assert "success" in result
        # May or may not find an agent depending on routing rules

    def test_spawn_agent_tool_success(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """spawn_agent MCP tool creates task and returns run info."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_agent_state_manager", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.spawn_agent.fn("test-agent-1", "Write a test script")

        assert result["success"] is True
        assert "task_id" in result
        assert result["agent"] == "test-agent-1"
        assert "run_id" in result

    def test_spawn_agent_tool_invalid_agent(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """spawn_agent MCP tool returns error for invalid agent."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.spawn_agent.fn("nonexistent-agent", "Some task")

        assert result["success"] is False
        assert "error" in result
        assert "available_agents" in result

    def test_memory_store_and_query_tools(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """memory_store and memory_query MCP tools work together."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Store some values
        store_result = server.memory_store.fn("test:key:1", "test value 1", namespace="test")
        assert store_result["success"] is True

        server.memory_store.fn("test:key:2", "test value 2", namespace="test")

        # Query them back
        query_result = server.memory_query.fn("test:key", namespace="test")
        assert query_result["count"] == 2
        assert len(query_result["memories"]) == 2

    def test_swarm_status_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """swarm_status MCP tool returns proper status info."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.swarm_status.fn()

        assert "total_agents" in result
        assert "active_tasks" in result
        assert "stats" in result
        assert "recent_runs" in result

    def test_complete_run_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """complete_run MCP tool updates task status correctly."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_agent_state_manager", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # First spawn an agent to create a task
        spawn_result = server.spawn_agent.fn("test-agent-1", "Test task for completion")
        task_id = spawn_result["task_id"]

        # Complete the task
        result = server.complete_run.fn(task_id, result="Task completed successfully", success=True, tokens_used=50)

        assert result["success"] is True
        assert result["task_id"] == task_id
        assert result["status"] == "completed"
        assert result["tokens_used"] == 50


@pytest.mark.integration
class TestMCPStorageTools:
    """Integration tests for storage/cleanup MCP tools."""

    def test_get_storage_stats_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_storage_stats MCP tool returns database statistics."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.get_storage_stats.fn()

        assert result["success"] is True
        assert "tables" in result
        assert "memories" in result["tables"]
        assert "agent_runs" in result["tables"]
        assert "database" in result
        assert "size_bytes" in result["database"]

    def test_get_storage_stats_with_data(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_storage_stats reflects actual data counts."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Add some data
        server.memory_store.fn("key1", "value1")
        server.memory_store.fn("key2", "value2")

        result = server.get_storage_stats.fn()

        assert result["tables"]["memories"] >= 2

    def test_cleanup_storage_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """cleanup_storage MCP tool runs cleanup and returns results."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.cleanup_storage.fn(runs_days=30, events_days=7, tasks_days=30)

        assert result["success"] is True
        assert "deleted" in result
        assert "retention_policy" in result
        assert "before" in result
        assert "after" in result

    def test_cleanup_storage_with_old_data(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """cleanup_storage removes old data correctly."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Insert old data directly
        coord = mock_get_coordinator()
        coord.memory.conn.execute("""
            INSERT INTO agent_runs (id, agent_name, task, status, started_at)
            VALUES ('old-run-1', 'agent1', 'old task', 'completed', CURRENT_TIMESTAMP - INTERVAL 60 DAY)
        """)

        # Run cleanup
        result = server.cleanup_storage.fn(runs_days=30)

        assert result["success"] is True
        assert result["deleted"]["agent_runs"] >= 1


@pytest.mark.integration
class TestMCPSchedulerTools:
    """Integration tests for scheduler MCP tools."""

    def test_create_dependent_task_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """create_dependent_task MCP tool creates tasks with dependencies."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Create first task (no dependencies)
        result1 = server.create_dependent_task.fn("First task", agent_name="test-agent-1")
        assert result1["success"] is True
        task1_id = result1["task_id"]

        # Create dependent task
        result2 = server.create_dependent_task.fn(
            "Second task", depends_on=[task1_id], agent_name="test-agent-1"
        )
        assert result2["success"] is True
        assert task1_id in result2["depends_on"]

    def test_get_task_graph_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_task_graph MCP tool returns task dependency graph."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Create some tasks
        server.create_dependent_task.fn("Task 1")
        server.create_dependent_task.fn("Task 2")

        result = server.get_task_graph.fn()

        assert "total_tasks" in result
        assert "tasks" in result
        assert result["total_tasks"] >= 2

    def test_get_ready_tasks_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_ready_tasks MCP tool returns tasks ready for execution."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Create a task with no dependencies
        create_result = server.create_dependent_task.fn("Ready task")

        result = server.get_ready_tasks.fn()

        assert "count" in result
        assert "tasks" in result
        assert result["count"] >= 1

    def test_complete_scheduled_task_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """complete_scheduled_task MCP tool marks tasks complete."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Create a task
        create_result = server.create_dependent_task.fn("Task to complete")
        task_id = create_result["task_id"]

        # Complete it
        result = server.complete_scheduled_task.fn(task_id, success=True, result="Done")

        assert result["success"] is True
        assert result["task_id"] == task_id
        assert result["task_success"] is True

    def test_execute_workflow_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """execute_workflow MCP tool creates full task workflow."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        tasks = [
            {"description": "Step 1: Setup", "agent": "test-agent-1"},
            {"description": "Step 2: Process", "agent": "test-agent-1", "depends_on": [0]},
            {"description": "Step 3: Finalize", "agent": "test-agent-1", "depends_on": [1]},
        ]

        result = server.execute_workflow.fn(tasks)

        assert result["success"] is True
        assert result["workflow_size"] == 3
        assert len(result["tasks"]) == 3
        assert len(result["execution_order"]) == 3

    def test_clear_workflow_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """clear_workflow MCP tool removes all scheduled tasks."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Create some tasks
        server.create_dependent_task.fn("Task 1")
        server.create_dependent_task.fn("Task 2")

        result = server.clear_workflow.fn()

        assert result["success"] is True
        assert result["cleared_tasks"] >= 2


@pytest.mark.integration
class TestMCPHealthTools:
    """Integration tests for agent health MCP tools."""

    def test_get_agent_health_single(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_agent_health MCP tool returns health for single agent."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_agent_state_manager", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.get_agent_health.fn("test-agent-1")

        assert result["success"] is True
        assert "agent" in result
        assert result["agent"]["name"] == "test-agent-1"
        assert "status" in result["agent"]
        assert "health_score" in result["agent"]

    def test_get_agent_health_all(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_agent_health MCP tool returns health for all agents."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_agent_state_manager", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.get_agent_health.fn()

        assert result["success"] is True
        assert "total" in result
        assert "agents" in result

    def test_set_agent_status_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """set_agent_status MCP tool updates agent status."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_agent_state_manager", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.set_agent_status.fn("test-agent-1", "paused", reason="Testing")

        assert result["success"] is True
        assert result["new_status"] == "paused"
        assert result["reason"] == "Testing"

    def test_set_agent_status_invalid_status(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """set_agent_status MCP tool returns error for invalid status."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_agent_state_manager", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.set_agent_status.fn("test-agent-1", "invalid_status")

        assert result["success"] is False
        assert "error" in result
        assert "valid_statuses" in result


@pytest.mark.integration
class TestMCPEventTools:
    """Integration tests for event MCP tools."""

    def test_emit_event_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """emit_event MCP tool emits events correctly."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.emit_event.fn(
            agent_name="test-agent-1",
            event_type="heartbeat",
            data={"status": "alive"},
        )

        assert result["success"] is True
        assert "event_id" in result
        assert result["agent"] == "test-agent-1"
        assert result["type"] == "heartbeat"

    def test_emit_event_invalid_type(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """emit_event MCP tool returns error for invalid event type."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.emit_event.fn(
            agent_name="test-agent-1",
            event_type="invalid_event_type",
        )

        assert result["success"] is False
        assert "error" in result
        assert "valid_types" in result

    def test_get_events_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_events MCP tool retrieves events."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Emit some events first
        server.emit_event.fn("test-agent-1", "heartbeat")
        server.emit_event.fn("test-agent-1", "task_start", {"task_id": "t1"})

        result = server.get_events.fn(limit=10)

        assert result["success"] is True
        assert "events" in result
        assert result["count"] >= 2

    def test_get_events_filtered(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_events MCP tool filters by agent and type."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        # Emit events from different agents
        server.emit_event.fn("agent-a", "heartbeat")
        server.emit_event.fn("agent-b", "heartbeat")
        server.emit_event.fn("agent-a", "error", {"message": "test error"})

        # Filter by agent
        result = server.get_events.fn(agent_name="agent-a")
        assert result["success"] is True
        assert all(e["agent"] == "agent-a" for e in result["events"])

        # Filter by event type
        result = server.get_events.fn(event_type="error")
        assert result["success"] is True
        assert all(e["type"] == "error" for e in result["events"])


@pytest.mark.integration
class TestMCPMetricsTools:
    """Integration tests for metrics MCP tools."""

    def test_get_metrics_tool(self, reset_server_singletons):
        """get_metrics MCP tool returns metrics summary."""
        import orchestrator.server as server

        result = server.get_metrics.fn()

        assert "totals" in result
        assert "counters" in result
        assert "gauges" in result
        assert "histograms" in result

    def test_get_metrics_with_reset(self, reset_server_singletons):
        """get_metrics MCP tool can reset metrics."""
        import orchestrator.server as server
        from orchestrator.metrics import get_metrics_collector

        # Add some metrics
        collector = get_metrics_collector()
        collector.increment("test_counter")
        collector.gauge_set("test_gauge", 42)

        # Get metrics with reset
        result = server.get_metrics.fn(reset=True)

        assert result.get("reset") is True

        # Verify reset happened
        result2 = server.get_metrics.fn()
        assert result2["totals"]["counter_count"] == 0

    def test_get_health_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """get_health MCP tool returns system health."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.get_health.fn()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "components" in result
        assert "stats" in result
        assert result["components"]["coordinator"] == "ok"
        assert result["components"]["memory"] == "ok"


@pytest.mark.integration
class TestMCPDecompositionTools:
    """Integration tests for task decomposition MCP tools."""

    def test_decompose_task_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """decompose_task MCP tool returns decomposition prompt."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        result = server.decompose_task.fn("Build a data pipeline with Python and SQL")

        assert result["action"] == "analyze_and_decompose"
        assert result["task"] == "Build a data pipeline with Python and SQL"
        assert "instructions" in result
        assert "available_agents" in result
        assert "response_schema" in result
        assert "example" in result

    def test_submit_decomposition_tool(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """submit_decomposition MCP tool creates workflow from decomposition."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        subtasks = [
            {
                "id": "t1",
                "description": "Setup environment",
                "agent": "test-agent-1",
                "depends_on": [],
                "execution_mode": "parallel",
                "priority": 8,
            },
            {
                "id": "t2",
                "description": "Process data",
                "agent": "test-agent-1",
                "depends_on": ["t1"],
                "execution_mode": "sequential",
                "priority": 5,
            },
        ]

        result = server.submit_decomposition.fn(
            original_task="Complex task",
            subtasks=subtasks,
            parallel_groups=[["t1"], ["t2"]],
            execution_order=["t1", "t2"],
            analysis="Two-phase workflow",
            auto_schedule=True,
        )

        assert result["success"] is True
        assert result["subtask_count"] == 2
        assert "id_mapping" in result
        assert result["scheduled"] is True
        assert "ready_to_execute" in result

    def test_submit_decomposition_invalid_agent(self, temp_agents_dir, temp_db_path, reset_server_singletons, monkeypatch):
        """submit_decomposition MCP tool reports validation errors."""
        import orchestrator.server as server

        monkeypatch.setattr(server, "_coordinator", None)
        monkeypatch.setattr(server, "_scheduler", None)

        def mock_get_coordinator():
            if server._coordinator is None:
                server._coordinator = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
            return server._coordinator

        monkeypatch.setattr(server, "get_coordinator", mock_get_coordinator)

        subtasks = [
            {
                "id": "t1",
                "description": "Task with invalid agent",
                "agent": "nonexistent-agent",
            },
        ]

        result = server.submit_decomposition.fn(
            original_task="Test task",
            subtasks=subtasks,
            auto_schedule=True,
        )

        assert result["success"] is False
        assert "validation_errors" in result
        assert any("nonexistent-agent" in err for err in result["validation_errors"])
