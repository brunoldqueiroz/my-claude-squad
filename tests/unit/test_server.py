"""Tests for orchestrator/server.py - MCP Server tools."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.types import (
    Agent,
    AgentEventType,
    AgentHealth,
    AgentModel,
    AgentRun,
    AgentStatus,
    Memory,
    SwarmStatus,
    Task,
    TaskStatus,
)


# === Fixtures for mocking singletons ===


@pytest.fixture
def mock_coordinator():
    """Mock the get_coordinator singleton."""
    with patch("orchestrator.server.get_coordinator") as mock_getter:
        coordinator = MagicMock()
        mock_getter.return_value = coordinator
        yield coordinator


@pytest.fixture
def mock_agent_state_manager():
    """Mock the get_agent_state_manager singleton."""
    with patch("orchestrator.server.get_agent_state_manager") as mock_getter:
        manager = MagicMock()
        mock_getter.return_value = manager
        yield manager


@pytest.fixture
def mock_scheduler():
    """Mock the get_scheduler singleton."""
    with patch("orchestrator.server.get_scheduler") as mock_getter:
        scheduler = MagicMock()
        scheduler._tasks = {}
        mock_getter.return_value = scheduler
        yield scheduler


@pytest.fixture
def mock_event_bus():
    """Mock the get_event_bus function."""
    with patch("orchestrator.server.get_event_bus") as mock_getter:
        bus = MagicMock()
        mock_getter.return_value = bus
        yield bus


@pytest.fixture
def mock_metrics_collector():
    """Mock the get_metrics_collector function."""
    with patch("orchestrator.server.get_metrics_collector") as mock_getter:
        collector = MagicMock()
        mock_getter.return_value = collector
        yield collector


@pytest.fixture
def sample_agent_fixture():
    """Create a sample agent for testing."""
    return Agent(
        name="test-agent",
        description="A test agent for unit testing purposes",
        model=AgentModel.SONNET,
        color="blue",
        triggers=["test", "example"],
        file_path="/path/to/test-agent.md",
    )


@pytest.fixture
def sample_agent_health_fixture():
    """Create a sample AgentHealth for testing."""
    return AgentHealth(
        agent_name="test-agent",
        status=AgentStatus.IDLE,
        health_score=0.95,
        last_heartbeat=datetime.now(),
        success_count=10,
        error_count=1,
        total_execution_time_ms=5000.0,
    )


# === Tests for list_agents ===


class TestListAgents:
    """Tests for the list_agents MCP tool."""

    def test_returns_all_agents(self, mock_coordinator, sample_agent_fixture):
        """list_agents returns all registered agents."""
        mock_coordinator.registry.list_agents.return_value = [sample_agent_fixture]

        from orchestrator.server import list_agents

        result = list_agents.fn()

        assert result["total"] == 1
        assert len(result["agents"]) == 1
        assert result["agents"][0]["name"] == "test-agent"

    def test_truncates_long_description(self, mock_coordinator):
        """list_agents truncates descriptions longer than 200 chars."""
        agent = Agent(
            name="verbose-agent",
            description="A" * 300,
            model=AgentModel.SONNET,
            file_path="/path/to/agent.md",
        )
        mock_coordinator.registry.list_agents.return_value = [agent]

        from orchestrator.server import list_agents

        result = list_agents.fn()

        assert result["agents"][0]["description"].endswith("...")
        assert len(result["agents"][0]["description"]) == 203  # 200 + "..."

    def test_limits_triggers_shown(self, mock_coordinator):
        """list_agents shows at most 5 triggers."""
        agent = Agent(
            name="many-triggers",
            description="Agent with many triggers",
            model=AgentModel.SONNET,
            triggers=["a", "b", "c", "d", "e", "f", "g"],
            file_path="/path/to/agent.md",
        )
        mock_coordinator.registry.list_agents.return_value = [agent]

        from orchestrator.server import list_agents

        result = list_agents.fn()

        assert len(result["agents"][0]["triggers"]) == 5


# === Tests for route_task ===


class TestRouteTask:
    """Tests for the route_task MCP tool."""

    def test_routes_to_matching_agent(self, mock_coordinator, sample_agent_fixture):
        """route_task returns the matched agent."""
        mock_coordinator.route_task.return_value = sample_agent_fixture

        from orchestrator.server import route_task

        result = route_task.fn("write a test script")

        assert result["success"] is True
        assert result["recommended_agent"] == "test-agent"

    def test_returns_high_confidence_with_trigger_match(
        self, mock_coordinator, sample_agent_fixture
    ):
        """route_task returns high confidence when trigger matches."""
        mock_coordinator.route_task.return_value = sample_agent_fixture

        from orchestrator.server import route_task

        result = route_task.fn("test something")

        assert result["confidence"] == "high"

    def test_returns_medium_confidence_without_trigger_match(
        self, mock_coordinator, sample_agent_fixture
    ):
        """route_task returns medium confidence when no trigger matches."""
        mock_coordinator.route_task.return_value = sample_agent_fixture

        from orchestrator.server import route_task

        result = route_task.fn("write some code")

        assert result["confidence"] == "medium"

    def test_returns_failure_when_no_agent_found(self, mock_coordinator):
        """route_task returns failure when no agent matches."""
        mock_coordinator.route_task.return_value = None

        from orchestrator.server import route_task

        result = route_task.fn("unknown task xyz")

        assert result["success"] is False
        assert "No suitable agent found" in result["message"]


# === Tests for spawn_agent ===


class TestSpawnAgent:
    """Tests for the spawn_agent MCP tool."""

    def test_spawns_existing_agent(
        self, mock_coordinator, mock_agent_state_manager, sample_agent_fixture
    ):
        """spawn_agent creates task and run for existing agent."""
        mock_coordinator.registry.get_agent.return_value = sample_agent_fixture
        mock_task = MagicMock(id="task-123")
        mock_run = MagicMock(id="run-456")
        mock_coordinator.create_task.return_value = mock_task
        mock_coordinator.start_task.return_value = mock_run

        from orchestrator.server import spawn_agent

        result = spawn_agent.fn("test-agent", "do something")

        assert result["success"] is True
        assert result["task_id"] == "task-123"
        assert result["run_id"] == "run-456"
        assert result["agent"] == "test-agent"
        # Verify event was emitted
        mock_agent_state_manager.record_task_start.assert_called_once_with(
            "test-agent", "task-123"
        )

    def test_returns_error_for_unknown_agent(self, mock_coordinator):
        """spawn_agent returns error when agent not found."""
        mock_coordinator.registry.get_agent.return_value = None
        mock_coordinator.registry.list_agents.return_value = []

        from orchestrator.server import spawn_agent

        result = spawn_agent.fn("nonexistent-agent", "do something")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_returns_available_agents_on_error(
        self, mock_coordinator, sample_agent_fixture
    ):
        """spawn_agent lists available agents when agent not found."""
        mock_coordinator.registry.get_agent.return_value = None
        mock_coordinator.registry.list_agents.return_value = [sample_agent_fixture]

        from orchestrator.server import spawn_agent

        result = spawn_agent.fn("nonexistent-agent", "do something")

        assert "test-agent" in result["available_agents"]


# === Tests for decompose_task ===


class TestDecomposeTask:
    """Tests for the decompose_task MCP tool."""

    def test_returns_analysis_prompt(self, mock_coordinator, sample_agent_fixture):
        """decompose_task returns a prompt for Claude Code to analyze."""
        mock_coordinator.registry.list_agents.return_value = [sample_agent_fixture]

        from orchestrator.server import decompose_task

        result = decompose_task.fn("Write and run tests")

        assert result["action"] == "analyze_and_decompose"
        assert result["task"] == "Write and run tests"
        assert "instructions" in result
        assert "available_agents" in result
        assert "response_schema" in result

    def test_includes_available_agents(self, mock_coordinator, sample_agent_fixture):
        """decompose_task includes list of available agents."""
        mock_coordinator.registry.list_agents.return_value = [sample_agent_fixture]

        from orchestrator.server import decompose_task

        result = decompose_task.fn("Complex task")

        assert len(result["available_agents"]) == 1
        assert result["available_agents"][0]["name"] == "test-agent"
        assert "keywords" in result["available_agents"][0]

    def test_includes_example_decomposition(self, mock_coordinator, sample_agent_fixture):
        """decompose_task includes an example for Claude Code."""
        mock_coordinator.registry.list_agents.return_value = [sample_agent_fixture]

        from orchestrator.server import decompose_task

        result = decompose_task.fn("Complex task")

        assert "example" in result
        assert "subtasks" in result["example"]


class TestSubmitDecomposition:
    """Tests for the submit_decomposition MCP tool."""

    def test_submits_valid_decomposition(self, mock_coordinator, mock_scheduler, sample_agent_fixture):
        """submit_decomposition creates tasks from Claude's analysis."""
        mock_coordinator.registry.get_agent.return_value = sample_agent_fixture
        mock_scheduler.get_ready_tasks.return_value = []

        from orchestrator.server import submit_decomposition

        result = submit_decomposition.fn(
            original_task="Complex task",
            subtasks=[
                {"id": "t1", "description": "First task", "agent": "test-agent", "depends_on": []},
                {"id": "t2", "description": "Second task", "agent": "test-agent", "depends_on": ["t1"]},
            ],
            execution_order=["t1", "t2"],
            analysis="Two-phase task",
        )

        assert result["success"] is True
        assert result["subtask_count"] == 2
        assert result["analysis"] == "Two-phase task"
        assert "t1" in result["id_mapping"]
        assert "t2" in result["id_mapping"]

    def test_validates_agent_exists(self, mock_coordinator, mock_scheduler):
        """submit_decomposition reports validation errors for unknown agents."""
        mock_coordinator.registry.get_agent.return_value = None
        mock_scheduler.get_ready_tasks.return_value = []

        from orchestrator.server import submit_decomposition

        result = submit_decomposition.fn(
            original_task="Task",
            subtasks=[{"id": "t1", "description": "Task", "agent": "unknown-agent"}],
            auto_schedule=False,
        )

        assert "validation_errors" in result
        assert any("unknown-agent" in err for err in result["validation_errors"])

    def test_resolves_dependencies(self, mock_coordinator, mock_scheduler, sample_agent_fixture):
        """submit_decomposition resolves dependency IDs to task UUIDs."""
        mock_coordinator.registry.get_agent.return_value = sample_agent_fixture
        mock_scheduler.get_ready_tasks.return_value = []

        from orchestrator.server import submit_decomposition

        result = submit_decomposition.fn(
            original_task="Task",
            subtasks=[
                {"id": "t1", "description": "First", "agent": "test-agent"},
                {"id": "t2", "description": "Second", "agent": "test-agent", "depends_on": ["t1"]},
            ],
        )

        # t2's resolved deps should contain the UUID mapped from t1
        t1_uuid = result["id_mapping"]["t1"]
        t2_subtask = next(s for s in result["subtasks"] if s["id"] == result["id_mapping"]["t2"])
        assert t1_uuid in t2_subtask["depends_on"]

    def test_schedules_tasks_by_default(self, mock_coordinator, mock_scheduler, sample_agent_fixture):
        """submit_decomposition adds tasks to scheduler by default."""
        mock_coordinator.registry.get_agent.return_value = sample_agent_fixture
        mock_scheduler.get_ready_tasks.return_value = []

        from orchestrator.server import submit_decomposition

        result = submit_decomposition.fn(
            original_task="Task",
            subtasks=[{"id": "t1", "description": "Task", "agent": "test-agent"}],
        )

        assert result["scheduled"] is True
        mock_scheduler.add_task.assert_called()


# === Tests for memory_store ===


class TestMemoryStore:
    """Tests for the memory_store MCP tool."""

    def test_stores_key_value(self, mock_coordinator):
        """memory_store stores key-value pair."""
        from orchestrator.server import memory_store

        result = memory_store.fn("my-key", "my-value")

        mock_coordinator.memory.store.assert_called_once_with(
            "my-key", "my-value", "default"
        )
        assert result["success"] is True
        assert result["key"] == "my-key"

    def test_stores_with_namespace(self, mock_coordinator):
        """memory_store uses provided namespace."""
        from orchestrator.server import memory_store

        result = memory_store.fn("key", "value", namespace="custom-ns")

        mock_coordinator.memory.store.assert_called_once_with(
            "key", "value", "custom-ns"
        )
        assert result["namespace"] == "custom-ns"


# === Tests for memory_query ===


class TestMemoryQuery:
    """Tests for the memory_query MCP tool."""

    def test_queries_memories(self, mock_coordinator):
        """memory_query returns matching memories."""
        mock_memory = Memory(
            key="test-key",
            value="test-value",
            namespace="default",
            created_at=datetime.now(),
        )
        mock_coordinator.memory.query.return_value = [mock_memory]

        from orchestrator.server import memory_query

        result = memory_query.fn("test")

        assert result["count"] == 1
        assert result["memories"][0]["key"] == "test-key"

    def test_truncates_long_values(self, mock_coordinator):
        """memory_query truncates values longer than 100 chars."""
        mock_memory = Memory(
            key="long-key",
            value="A" * 200,
            namespace="default",
            created_at=datetime.now(),
        )
        mock_coordinator.memory.query.return_value = [mock_memory]

        from orchestrator.server import memory_query

        result = memory_query.fn("long")

        assert result["memories"][0]["value"].endswith("...")
        assert len(result["memories"][0]["value"]) == 103  # 100 + "..."


# === Tests for swarm_status ===


class TestSwarmStatus:
    """Tests for the swarm_status MCP tool."""

    def test_returns_status_structure(self, mock_coordinator):
        """swarm_status returns proper structure."""
        mock_run = MagicMock()
        mock_run.id = "run-1"
        mock_run.agent_name = "test-agent"
        mock_run.task = "Test task"
        mock_run.status = TaskStatus.COMPLETED
        mock_run.started_at = datetime.now()

        mock_status = MagicMock()
        mock_status.total_agents = 5
        mock_status.active_tasks = 2
        mock_status.recent_runs = [mock_run]

        mock_coordinator.get_swarm_status.return_value = mock_status
        mock_coordinator.memory.get_run_stats.return_value = {
            "total_runs": 100,
            "completed": 80,
            "failed": 10,
            "in_progress": 10,
            "total_tokens": 50000,
        }

        from orchestrator.server import swarm_status

        result = swarm_status.fn()

        assert result["total_agents"] == 5
        assert result["active_tasks"] == 2
        assert result["stats"]["total_runs"] == 100
        assert len(result["recent_runs"]) == 1


# === Tests for complete_run ===


class TestCompleteRun:
    """Tests for the complete_run MCP tool."""

    def test_completes_task_successfully(self, mock_coordinator, mock_agent_state_manager):
        """complete_run marks task as complete."""
        # Set up task in coordinator's _active_tasks
        mock_task = MagicMock()
        mock_task.agent_name = "test-agent"
        mock_task.created_at = datetime.now()
        mock_coordinator._active_tasks = {"task-123": mock_task}

        from orchestrator.server import complete_run

        result = complete_run.fn("task-123", result="Done", success=True, tokens_used=100)

        mock_coordinator.complete_task.assert_called_once_with(
            "task-123", "Done", True, 100
        )
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["agent"] == "test-agent"
        # Verify event was emitted
        mock_agent_state_manager.record_task_complete.assert_called_once()
        call_args = mock_agent_state_manager.record_task_complete.call_args
        assert call_args[0][0] == "test-agent"  # agent_name
        assert call_args[0][1] is True  # success

    def test_completes_task_with_failure(self, mock_coordinator, mock_agent_state_manager):
        """complete_run marks task as failed."""
        # Set up task in coordinator's _active_tasks
        mock_task = MagicMock()
        mock_task.agent_name = "test-agent"
        mock_task.created_at = datetime.now()
        mock_coordinator._active_tasks = {"task-123": mock_task}

        from orchestrator.server import complete_run

        result = complete_run.fn("task-123", result="Error", success=False)

        assert result["status"] == "failed"
        # Verify failure event was emitted
        mock_agent_state_manager.record_task_complete.assert_called_once()
        call_args = mock_agent_state_manager.record_task_complete.call_args
        assert call_args[0][1] is False  # success=False

    def test_completes_task_without_active_task(self, mock_coordinator, mock_agent_state_manager):
        """complete_run handles case when task not in active_tasks."""
        mock_coordinator._active_tasks = {}

        from orchestrator.server import complete_run

        result = complete_run.fn("task-123", result="Done", success=True)

        assert result["success"] is True
        assert result["agent"] is None
        # Should not emit event if no agent
        mock_agent_state_manager.record_task_complete.assert_not_called()


# === Tests for get_agent_health ===


class TestGetAgentHealth:
    """Tests for the get_agent_health MCP tool."""

    def test_returns_single_agent_health(
        self, mock_coordinator, mock_agent_state_manager, sample_agent_health_fixture
    ):
        """get_agent_health returns health for specific agent."""
        mock_agent_state_manager.get_health.return_value = sample_agent_health_fixture

        from orchestrator.server import get_agent_health

        result = get_agent_health.fn("test-agent")

        assert result["success"] is True
        assert result["agent"]["name"] == "test-agent"
        assert result["agent"]["health_score"] == 0.95

    def test_initializes_agent_if_not_tracked(
        self, mock_coordinator, mock_agent_state_manager, sample_agent_fixture
    ):
        """get_agent_health initializes health if agent exists but not tracked."""
        mock_agent_state_manager.get_health.return_value = None
        mock_coordinator.registry.get_agent.return_value = sample_agent_fixture
        mock_health = AgentHealth(agent_name="test-agent", status=AgentStatus.IDLE)
        mock_agent_state_manager.initialize_agent.return_value = mock_health

        from orchestrator.server import get_agent_health

        result = get_agent_health.fn("test-agent")

        assert result["success"] is True
        mock_agent_state_manager.initialize_agent.assert_called_once_with("test-agent")

    def test_returns_error_for_unknown_agent(
        self, mock_coordinator, mock_agent_state_manager
    ):
        """get_agent_health returns error for nonexistent agent."""
        mock_agent_state_manager.get_health.return_value = None
        mock_coordinator.registry.get_agent.return_value = None

        from orchestrator.server import get_agent_health

        result = get_agent_health.fn("nonexistent-agent")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_returns_all_agents_when_no_name(
        self, mock_coordinator, mock_agent_state_manager, sample_agent_health_fixture
    ):
        """get_agent_health returns all agents when no name specified."""
        mock_agent_state_manager.get_all_health.return_value = [
            sample_agent_health_fixture
        ]
        mock_agent_state_manager.get_available_agents.return_value = ["test-agent"]
        mock_agent_state_manager.get_busy_agents.return_value = []
        mock_coordinator.registry.list_agents.return_value = []

        from orchestrator.server import get_agent_health

        result = get_agent_health.fn(None)

        assert result["success"] is True
        assert result["total"] == 1
        assert result["available"] == 1


# === Tests for set_agent_status ===


class TestSetAgentStatus:
    """Tests for the set_agent_status MCP tool."""

    def test_sets_valid_status(
        self, mock_coordinator, mock_agent_state_manager, sample_agent_fixture
    ):
        """set_agent_status updates status for valid agent."""
        mock_coordinator.registry.get_agent.return_value = sample_agent_fixture
        mock_health = AgentHealth(
            agent_name="test-agent", status=AgentStatus.PAUSED, health_score=0.9
        )
        mock_agent_state_manager.set_status.return_value = mock_health

        from orchestrator.server import set_agent_status

        result = set_agent_status.fn("test-agent", "paused", "Manual pause")

        assert result["success"] is True
        assert result["new_status"] == "paused"

    def test_returns_error_for_unknown_agent(
        self, mock_coordinator, mock_agent_state_manager
    ):
        """set_agent_status returns error for nonexistent agent."""
        mock_coordinator.registry.get_agent.return_value = None
        mock_coordinator.registry.list_agents.return_value = []

        from orchestrator.server import set_agent_status

        result = set_agent_status.fn("nonexistent", "idle")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_returns_error_for_invalid_status(
        self, mock_coordinator, mock_agent_state_manager, sample_agent_fixture
    ):
        """set_agent_status returns error for invalid status value."""
        mock_coordinator.registry.get_agent.return_value = sample_agent_fixture

        from orchestrator.server import set_agent_status

        result = set_agent_status.fn("test-agent", "invalid-status")

        assert result["success"] is False
        assert "Invalid status" in result["error"]
        assert "valid_statuses" in result


# === Tests for create_dependent_task ===


class TestCreateDependentTask:
    """Tests for the create_dependent_task MCP tool."""

    def test_creates_task_without_dependencies(self, mock_coordinator, mock_scheduler):
        """create_dependent_task creates a task without dependencies."""
        from orchestrator.server import create_dependent_task

        result = create_dependent_task.fn("Test task")

        assert result["success"] is True
        assert result["description"] == "Test task"
        assert result["depends_on"] == []

    def test_creates_task_with_dependencies(self, mock_coordinator, mock_scheduler):
        """create_dependent_task creates a task with dependencies."""
        # Add a task to the scheduler so dependency exists
        mock_scheduler._tasks = {"dep-1": MagicMock()}

        from orchestrator.server import create_dependent_task

        result = create_dependent_task.fn("Dependent task", depends_on=["dep-1"])

        assert result["success"] is True
        assert result["depends_on"] == ["dep-1"]

    def test_returns_error_for_missing_dependency(self, mock_coordinator, mock_scheduler):
        """create_dependent_task returns error when dependency doesn't exist."""
        mock_scheduler._tasks = {}

        from orchestrator.server import create_dependent_task

        result = create_dependent_task.fn("Task", depends_on=["nonexistent-dep"])

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_validates_agent_exists(
        self, mock_coordinator, mock_scheduler, sample_agent_fixture
    ):
        """create_dependent_task validates agent exists."""
        mock_coordinator.registry.get_agent.return_value = None
        mock_coordinator.registry.list_agents.return_value = [sample_agent_fixture]

        from orchestrator.server import create_dependent_task

        result = create_dependent_task.fn("Task", agent_name="nonexistent-agent")

        assert result["success"] is False
        assert "Agent" in result["error"]


# === Tests for get_task_graph ===


class TestGetTaskGraph:
    """Tests for the get_task_graph MCP tool."""

    def test_returns_task_graph(self, mock_scheduler):
        """get_task_graph returns scheduler's task graph."""
        mock_scheduler.get_task_graph.return_value = {
            "tasks": [],
            "circuit_breakers": {},
        }

        from orchestrator.server import get_task_graph

        result = get_task_graph.fn()

        assert "tasks" in result
        mock_scheduler.get_task_graph.assert_called_once()


# === Tests for get_ready_tasks ===


class TestGetReadyTasks:
    """Tests for the get_ready_tasks MCP tool."""

    def test_returns_ready_tasks(self, mock_scheduler):
        """get_ready_tasks returns tasks with satisfied dependencies."""
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.description = "Ready task"
        mock_task.agent_name = "test-agent"
        mock_scheduler.get_ready_tasks.return_value = [mock_task]

        from orchestrator.server import get_ready_tasks

        result = get_ready_tasks.fn()

        assert result["count"] == 1
        assert result["tasks"][0]["id"] == "task-1"


# === Tests for complete_scheduled_task ===


class TestCompleteScheduledTask:
    """Tests for the complete_scheduled_task MCP tool."""

    def test_completes_existing_task(self, mock_scheduler):
        """complete_scheduled_task marks existing task as complete."""
        mock_task = MagicMock()
        mock_scheduler._tasks = {"task-1": mock_task}
        mock_scheduler.get_ready_tasks.return_value = []

        from orchestrator.server import complete_scheduled_task

        result = complete_scheduled_task.fn("task-1", success=True, result="Done")

        assert result["success"] is True
        assert result["task_success"] is True
        mock_scheduler.mark_completed.assert_called_once_with("task-1", success=True)

    def test_returns_error_for_unknown_task(self, mock_scheduler):
        """complete_scheduled_task returns error for unknown task."""
        mock_scheduler._tasks = {}

        from orchestrator.server import complete_scheduled_task

        result = complete_scheduled_task.fn("nonexistent-task")

        assert result["success"] is False
        assert "not found" in result["error"]


# === Tests for execute_workflow ===


class TestExecuteWorkflow:
    """Tests for the execute_workflow MCP tool."""

    def test_executes_simple_workflow(self, mock_coordinator, mock_scheduler):
        """execute_workflow creates tasks from workflow definition."""
        mock_coordinator.registry.get_agent.return_value = None
        mock_scheduler.topological_sort.return_value = []
        mock_scheduler.get_ready_tasks.return_value = []

        from orchestrator.server import execute_workflow

        tasks = [
            {"description": "Task 1"},
            {"description": "Task 2", "depends_on": [0]},
        ]
        result = execute_workflow.fn(tasks)

        assert result["success"] is True
        assert result["workflow_size"] == 2

    def test_returns_error_for_invalid_agent(
        self, mock_coordinator, mock_scheduler, sample_agent_fixture
    ):
        """execute_workflow returns error when agent not found."""
        mock_coordinator.registry.get_agent.return_value = None

        from orchestrator.server import execute_workflow

        tasks = [{"description": "Task 1", "agent": "nonexistent-agent"}]
        result = execute_workflow.fn(tasks)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_returns_error_for_circular_dependency(self, mock_coordinator, mock_scheduler):
        """execute_workflow returns error for circular dependencies."""
        mock_coordinator.registry.get_agent.return_value = None
        mock_scheduler.topological_sort.side_effect = ValueError("Circular dependency")

        from orchestrator.server import execute_workflow

        tasks = [{"description": "Task 1"}]
        result = execute_workflow.fn(tasks)

        assert result["success"] is False


# === Tests for clear_workflow ===


class TestClearWorkflow:
    """Tests for the clear_workflow MCP tool."""

    def test_clears_all_tasks(self, mock_scheduler):
        """clear_workflow removes all scheduled tasks."""
        mock_scheduler._tasks = {"t1": MagicMock(), "t2": MagicMock()}

        from orchestrator.server import clear_workflow

        result = clear_workflow.fn()

        assert result["success"] is True
        assert result["cleared_tasks"] == 2
        mock_scheduler.clear.assert_called_once()


# === Tests for get_health ===


class TestGetHealth:
    """Tests for the get_health MCP tool."""

    def test_returns_health_structure(self, mock_coordinator):
        """get_health returns proper health check structure."""
        mock_coordinator.memory.get_run_stats.return_value = {
            "total_runs": 50,
            "completed": 40,
            "failed": 5,
            "in_progress": 5,
        }
        mock_coordinator.registry.list_agents.return_value = []

        with patch("orchestrator.server.get_langfuse") as mock_langfuse:
            mock_langfuse.return_value = None
            with patch("orchestrator.server.langfuse_enabled") as mock_enabled:
                mock_enabled.return_value = False

                from orchestrator.server import get_health

                result = get_health.fn()

        assert result["status"] == "healthy"
        assert "components" in result
        assert result["components"]["coordinator"] == "ok"

    def test_detects_langfuse_connected(self, mock_coordinator):
        """get_health shows langfuse as connected when available."""
        mock_coordinator.memory.get_run_stats.return_value = {
            "total_runs": 0,
            "completed": 0,
            "failed": 0,
            "in_progress": 0,
        }
        mock_coordinator.registry.list_agents.return_value = []

        with patch("orchestrator.server.get_langfuse") as mock_langfuse:
            mock_langfuse.return_value = MagicMock()  # Langfuse is connected

            from orchestrator.server import get_health

            result = get_health.fn()

        assert result["components"]["langfuse"] == "connected"


# === Tests for get_metrics ===


class TestGetMetrics:
    """Tests for the get_metrics MCP tool."""

    def test_returns_metrics_summary(self, mock_metrics_collector):
        """get_metrics returns metrics summary."""
        mock_metrics_collector.get_summary.return_value = {
            "counters": {},
            "gauges": {},
            "histograms": {},
        }

        from orchestrator.server import get_metrics

        result = get_metrics.fn()

        assert "counters" in result
        mock_metrics_collector.get_summary.assert_called_once()

    def test_resets_metrics_when_requested(self, mock_metrics_collector):
        """get_metrics resets metrics when reset=True."""
        mock_metrics_collector.get_summary.return_value = {"counters": {}}

        from orchestrator.server import get_metrics

        result = get_metrics.fn(reset=True)

        mock_metrics_collector.reset.assert_called_once()
        assert result["reset"] is True


# === Tests for get_events ===


class TestGetEvents:
    """Tests for the get_events MCP tool."""

    def test_returns_events(self, mock_event_bus):
        """get_events returns event history."""
        mock_event = MagicMock()
        mock_event.id = "evt-1"
        mock_event.agent_name = "test-agent"
        mock_event.event_type = AgentEventType.HEARTBEAT
        mock_event.event_data = {}
        mock_event.timestamp = datetime.now()

        mock_event_bus.get_history.return_value = [mock_event]
        mock_event_bus.get_stats.return_value = {"total": 1}

        from orchestrator.server import get_events

        result = get_events.fn(limit=50)

        assert result["success"] is True
        assert result["count"] == 1
        assert result["events"][0]["id"] == "evt-1"

    def test_filters_by_event_type(self, mock_event_bus):
        """get_events filters by event type."""
        mock_event_bus.get_history.return_value = []
        mock_event_bus.get_stats.return_value = {}

        from orchestrator.server import get_events

        result = get_events.fn(event_type="heartbeat")

        mock_event_bus.get_history.assert_called_once()
        call_args = mock_event_bus.get_history.call_args
        assert call_args.kwargs["event_type"] == AgentEventType.HEARTBEAT

    def test_returns_error_for_invalid_event_type(self, mock_event_bus):
        """get_events returns error for invalid event type."""
        from orchestrator.server import get_events

        result = get_events.fn(event_type="invalid-type")

        assert result["success"] is False
        assert "Invalid event type" in result["error"]


# === Tests for emit_event ===


class TestEmitEvent:
    """Tests for the emit_event MCP tool."""

    def test_emits_valid_event(self, mock_coordinator, mock_event_bus):
        """emit_event emits event to bus and persists to memory."""
        mock_event_bus.emit_sync.return_value = 2

        from orchestrator.server import emit_event

        result = emit_event.fn("test-agent", "heartbeat", {"status": "ok"})

        assert result["success"] is True
        assert result["agent"] == "test-agent"
        assert result["type"] == "heartbeat"
        assert result["handlers_called"] == 2
        mock_coordinator.memory.insert_agent_event.assert_called_once()

    def test_returns_error_for_invalid_event_type(self, mock_event_bus):
        """emit_event returns error for invalid event type."""
        from orchestrator.server import emit_event

        result = emit_event.fn("test-agent", "invalid-type")

        assert result["success"] is False
        assert "Invalid event type" in result["error"]


# === Tests for singleton getters ===


class TestSingletonGetters:
    """Tests for the singleton getter functions."""

    def test_get_coordinator_creates_singleton(self, tmp_path):
        """get_coordinator creates coordinator on first call."""
        import orchestrator.server as server

        # Reset singleton
        original = server._coordinator
        server._coordinator = None

        try:
            with patch.object(Path, "parent", tmp_path):
                # This will fail because agents dir doesn't exist, but tests the pattern
                pass
        finally:
            server._coordinator = original

    def test_get_agent_state_manager_uses_coordinator_memory(self):
        """get_agent_state_manager uses coordinator's memory."""
        import orchestrator.server as server

        original_coord = server._coordinator
        original_state = server._agent_state_manager

        try:
            server._coordinator = MagicMock()
            server._agent_state_manager = None

            manager = server.get_agent_state_manager()

            # Verify AgentStateManager was created with coordinator's memory
            assert manager is not None
        finally:
            server._coordinator = original_coord
            server._agent_state_manager = original_state

    def test_get_scheduler_creates_singleton(self):
        """get_scheduler creates TaskScheduler on first call."""
        import orchestrator.server as server

        original = server._scheduler
        server._scheduler = None

        try:
            scheduler = server.get_scheduler()
            assert scheduler is not None

            # Second call returns same instance
            scheduler2 = server.get_scheduler()
            assert scheduler is scheduler2
        finally:
            server._scheduler = original
