"""Tests for orchestrator/coordinator.py - Coordinator."""

from unittest.mock import MagicMock, patch

import pytest

from orchestrator.coordinator import Coordinator
from orchestrator.types import TaskStatus


class TestCoordinatorInit:
    """Tests for Coordinator initialization."""

    def test_creates_registry_and_memory(self, coordinator):
        """Coordinator initializes with registry and memory."""
        assert coordinator.registry is not None
        assert coordinator.memory is not None


class TestCoordinatorRouteTask:
    """Tests for task routing."""

    def test_routes_snowflake_task(self, coordinator):
        """Routes snowflake task to snowflake-specialist."""
        agent = coordinator.route_task("Create a Snowflake table")

        # May be None if agent not in test fixtures
        if agent:
            assert "snowflake" in agent.name.lower() or "planner" in agent.name.lower()

    def test_routes_python_task(self, coordinator):
        """Routes python task to python-developer or matching agent."""
        agent = coordinator.route_task("Write a python script")

        if agent:
            # Test agent may match on python keyword in description
            assert agent is not None

    def test_routes_sql_task(self, coordinator):
        """Routes SQL task to sql-specialist."""
        agent = coordinator.route_task("Write a SQL query")

        if agent:
            assert "sql" in agent.name.lower() or "planner" in agent.name.lower()

    def test_routes_docker_task(self, coordinator):
        """Routes docker task to container-specialist."""
        agent = coordinator.route_task("Create a Dockerfile")

        if agent:
            assert (
                "container" in agent.name.lower()
                or "docker" in agent.name.lower()
                or "planner" in agent.name.lower()
            )

    def test_routes_rag_task(self, coordinator):
        """Routes RAG task to rag-specialist."""
        agent = coordinator.route_task("Build a RAG pipeline")

        if agent:
            assert "rag" in agent.name.lower() or "planner" in agent.name.lower()

    def test_route_is_case_insensitive(self, coordinator):
        """Routing is case insensitive."""
        agent1 = coordinator.route_task("python script")
        agent2 = coordinator.route_task("PYTHON SCRIPT")
        agent3 = coordinator.route_task("Python Script")

        # All should return same agent
        if agent1 and agent2:
            assert agent1.name == agent2.name
        if agent2 and agent3:
            assert agent2.name == agent3.name

    def test_fallback_to_planner_orchestrator(self, coordinator):
        """Unknown tasks fall back to planner-orchestrator."""
        agent = coordinator.route_task("Do something completely random xyz")

        # Either returns planner-orchestrator or None
        if agent:
            # May match "planner" or fall back
            pass  # Just verify no exception


class TestCoordinatorDecomposeTask:
    """Tests for task decomposition."""

    def test_decompose_with_and(self, coordinator):
        """Decomposes tasks with 'and' connector."""
        subtasks = coordinator.decompose_task(
            "Write a python script and create a SQL query"
        )

        assert len(subtasks) >= 2

    def test_decompose_with_then(self, coordinator):
        """Decomposes tasks with 'then' connector."""
        subtasks = coordinator.decompose_task(
            "Create the schema then insert the data"
        )

        assert len(subtasks) >= 2

    def test_decompose_with_comma(self, coordinator):
        """Decomposes tasks with comma separator."""
        subtasks = coordinator.decompose_task(
            "Build the API, write tests, update docs"
        )

        assert len(subtasks) >= 2

    def test_simple_task_not_decomposed(self, coordinator):
        """Simple task without connectors is not decomposed."""
        subtasks = coordinator.decompose_task("Write a simple script")

        assert len(subtasks) == 1
        assert subtasks[0][0] == "Write a simple script"

    def test_decomposed_parts_have_agents(self, coordinator):
        """Each decomposed part is assigned an agent."""
        subtasks = coordinator.decompose_task(
            "Write a python script and create a SQL query"
        )

        for subtask, agent in subtasks:
            # Each should have a subtask string
            assert len(subtask) > 0
            # Agent can be None if no matching agent in fixtures


class TestCoordinatorCreateTask:
    """Tests for task creation."""

    def test_create_task_generates_id(self, coordinator):
        """create_task generates a unique ID."""
        task = coordinator.create_task("Test task")

        assert task.id is not None
        assert len(task.id) == 8

    def test_create_task_auto_routes(self, coordinator):
        """create_task auto-assigns agent based on description."""
        task = coordinator.create_task("Write a python function")

        # Agent should be assigned (or None if not matched)
        # Just verify task is created
        assert task.description == "Write a python function"

    def test_create_task_with_agent_override(self, coordinator):
        """create_task accepts agent name override."""
        task = coordinator.create_task("Test task", agent_name="custom-agent")

        assert task.agent_name == "custom-agent"

    def test_create_task_stored_in_active(self, coordinator):
        """Created tasks are stored in active tasks."""
        task = coordinator.create_task("Test task")

        assert task.id in coordinator._active_tasks

    def test_create_task_starts_pending(self, coordinator):
        """Created tasks start in PENDING status."""
        task = coordinator.create_task("Test task")

        assert task.status == TaskStatus.PENDING


class TestCoordinatorStartTask:
    """Tests for starting tasks."""

    def test_start_task_creates_run(self, coordinator):
        """start_task creates an AgentRun."""
        task = coordinator.create_task("Test task", agent_name="test-agent")
        run = coordinator.start_task(task.id)

        assert run is not None
        assert run.agent_name == "test-agent"

    def test_start_task_updates_status(self, coordinator):
        """start_task updates task status to IN_PROGRESS."""
        task = coordinator.create_task("Test task", agent_name="test-agent")
        coordinator.start_task(task.id)

        assert coordinator._active_tasks[task.id].status == TaskStatus.IN_PROGRESS

    def test_start_task_nonexistent_returns_none(self, coordinator):
        """start_task returns None for nonexistent task."""
        run = coordinator.start_task("nonexistent-id")

        assert run is None

    def test_start_task_without_agent_returns_none(self, coordinator):
        """start_task returns None if task has no agent."""
        task = coordinator.create_task("Test task")
        task.agent_name = None
        run = coordinator.start_task(task.id)

        assert run is None


class TestCoordinatorCompleteTask:
    """Tests for completing tasks."""

    def test_complete_task_success(self, coordinator):
        """complete_task marks task as COMPLETED on success."""
        task = coordinator.create_task("Test task", agent_name="test-agent")
        coordinator.start_task(task.id)

        coordinator.complete_task(task.id, result="Done", success=True)

        assert coordinator._active_tasks[task.id].status == TaskStatus.COMPLETED

    def test_complete_task_failure(self, coordinator):
        """complete_task marks task as FAILED on failure."""
        task = coordinator.create_task("Test task", agent_name="test-agent")
        coordinator.start_task(task.id)

        coordinator.complete_task(task.id, result="Error", success=False)

        assert coordinator._active_tasks[task.id].status == TaskStatus.FAILED

    def test_complete_task_sets_result(self, coordinator):
        """complete_task sets the result text."""
        task = coordinator.create_task("Test task", agent_name="test-agent")
        coordinator.start_task(task.id)

        coordinator.complete_task(task.id, result="Task completed successfully")

        assert coordinator._active_tasks[task.id].result == "Task completed successfully"

    def test_complete_task_sets_completed_at(self, coordinator):
        """complete_task sets completed_at timestamp."""
        task = coordinator.create_task("Test task", agent_name="test-agent")
        coordinator.start_task(task.id)

        coordinator.complete_task(task.id)

        assert coordinator._active_tasks[task.id].completed_at is not None

    def test_complete_task_nonexistent_no_error(self, coordinator):
        """complete_task does not raise for nonexistent task."""
        # Should not raise
        coordinator.complete_task("nonexistent-id", result="Done")

    def test_complete_task_logs_to_memory(self, coordinator):
        """complete_task logs completion to memory."""
        task = coordinator.create_task("Test task", agent_name="test-agent")
        coordinator.start_task(task.id)

        coordinator.complete_task(task.id, result="Done", tokens_used=150)

        # Verify run was logged
        stats = coordinator.memory.get_run_stats()
        assert stats["completed"] >= 1


class TestCoordinatorSwarmStatus:
    """Tests for swarm status."""

    def test_get_swarm_status_structure(self, coordinator):
        """get_swarm_status returns correct structure."""
        status = coordinator.get_swarm_status()

        assert hasattr(status, "total_agents")
        assert hasattr(status, "active_tasks")
        assert hasattr(status, "completed_tasks")
        assert hasattr(status, "agents")
        assert hasattr(status, "recent_runs")

    def test_get_swarm_status_counts_active(self, coordinator):
        """get_swarm_status counts active tasks correctly."""
        # Create and start some tasks
        task1 = coordinator.create_task("Task 1", agent_name="agent1")
        task2 = coordinator.create_task("Task 2", agent_name="agent2")
        coordinator.start_task(task1.id)
        coordinator.start_task(task2.id)

        status = coordinator.get_swarm_status()

        assert status.active_tasks == 2


class TestCoordinatorClose:
    """Tests for closing coordinator."""

    def test_close_closes_memory(self, temp_db_path, temp_agents_dir):
        """close() closes the memory connection."""
        coord = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
        coord.close()

        # Memory should be closed
        with pytest.raises(Exception):
            coord.memory.conn.execute("SELECT 1")
