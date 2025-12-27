"""Tests for orchestrator/types.py - Pydantic models."""

from datetime import datetime

import pytest

from orchestrator.types import (
    Agent,
    AgentEvent,
    AgentEventType,
    AgentHealth,
    AgentModel,
    AgentRun,
    AgentStatus,
    DependencyType,
    Memory,
    ScheduledTask,
    SwarmStatus,
    Task,
    TaskDependency,
    TaskStatus,
)


class TestAgentModelEnum:
    """Tests for AgentModel enum."""

    def test_opus_value(self):
        assert AgentModel.OPUS.value == "opus"

    def test_sonnet_value(self):
        assert AgentModel.SONNET.value == "sonnet"

    def test_haiku_value(self):
        assert AgentModel.HAIKU.value == "haiku"


class TestAgentStatusEnum:
    """Tests for AgentStatus enum."""

    def test_all_status_values(self):
        expected = {"initializing", "idle", "busy", "paused", "error", "offline"}
        actual = {s.value for s in AgentStatus}
        assert actual == expected

    def test_status_is_string_enum(self):
        assert isinstance(AgentStatus.IDLE.value, str)


class TestTaskStatusEnum:
    """Tests for TaskStatus enum."""

    def test_all_status_values(self):
        expected = {"pending", "in_progress", "completed", "failed"}
        actual = {s.value for s in TaskStatus}
        assert actual == expected


class TestAgentEventTypeEnum:
    """Tests for AgentEventType enum."""

    def test_all_event_types(self):
        expected = {
            "heartbeat",
            "status_change",
            "task_start",
            "task_complete",
            "task_failed",
            "error",
        }
        actual = {e.value for e in AgentEventType}
        assert actual == expected


class TestDependencyTypeEnum:
    """Tests for DependencyType enum."""

    def test_all_dependency_types(self):
        expected = {"finish-start", "start-start", "data"}
        actual = {d.value for d in DependencyType}
        assert actual == expected


class TestAgentModel:
    """Tests for Agent Pydantic model."""

    def test_agent_creation_with_defaults(self):
        agent = Agent(name="test", description="Test agent")
        assert agent.name == "test"
        assert agent.description == "Test agent"
        assert agent.model == AgentModel.SONNET  # Default
        assert agent.color == "white"  # Default
        assert agent.triggers == []  # Default
        assert agent.file_path == ""  # Default

    def test_agent_creation_with_all_fields(self):
        agent = Agent(
            name="custom",
            description="Custom agent",
            model=AgentModel.OPUS,
            color="blue",
            triggers=["python", "code"],
            file_path="/agents/custom.md",
        )
        assert agent.name == "custom"
        assert agent.model == AgentModel.OPUS
        assert agent.color == "blue"
        assert "python" in agent.triggers


class TestTaskModel:
    """Tests for Task Pydantic model."""

    def test_task_creation_with_defaults(self):
        task = Task(id="t1", description="Test task")
        assert task.id == "t1"
        assert task.description == "Test task"
        assert task.agent_name is None
        assert task.status == TaskStatus.PENDING
        assert isinstance(task.created_at, datetime)
        assert task.completed_at is None
        assert task.result is None
        assert task.trace_id is None

    def test_task_creation_with_agent(self):
        task = Task(
            id="t2",
            description="Assigned task",
            agent_name="python-developer",
            status=TaskStatus.IN_PROGRESS,
        )
        assert task.agent_name == "python-developer"
        assert task.status == TaskStatus.IN_PROGRESS


class TestAgentHealthModel:
    """Tests for AgentHealth Pydantic model."""

    def test_agent_health_defaults(self):
        health = AgentHealth(agent_name="test")
        assert health.agent_name == "test"
        assert health.status == AgentStatus.IDLE
        assert health.health_score == 1.0
        assert health.current_task_id is None
        assert health.error_count == 0
        assert health.success_count == 0
        assert health.total_execution_time_ms == 0.0

    def test_success_rate_zero_tasks(self):
        """success_rate returns 1.0 when no tasks completed."""
        health = AgentHealth(agent_name="test", error_count=0, success_count=0)
        assert health.success_rate == 1.0

    def test_success_rate_all_success(self):
        health = AgentHealth(agent_name="test", error_count=0, success_count=10)
        assert health.success_rate == 1.0

    def test_success_rate_mixed(self):
        health = AgentHealth(agent_name="test", error_count=2, success_count=8)
        assert health.success_rate == 0.8

    def test_success_rate_all_failures(self):
        health = AgentHealth(agent_name="test", error_count=5, success_count=0)
        assert health.success_rate == 0.0

    def test_avg_execution_time_zero_tasks(self):
        """avg_execution_time_ms returns 0.0 when no tasks."""
        health = AgentHealth(
            agent_name="test", error_count=0, success_count=0, total_execution_time_ms=0
        )
        assert health.avg_execution_time_ms == 0.0

    def test_avg_execution_time_calculation(self):
        health = AgentHealth(
            agent_name="test",
            error_count=2,
            success_count=8,
            total_execution_time_ms=1000.0,
        )
        assert health.avg_execution_time_ms == 100.0  # 1000 / 10

    def test_health_score_bounds(self):
        """health_score must be between 0 and 1."""
        with pytest.raises(ValueError):
            AgentHealth(agent_name="test", health_score=1.5)
        with pytest.raises(ValueError):
            AgentHealth(agent_name="test", health_score=-0.1)


class TestMemoryModel:
    """Tests for Memory Pydantic model."""

    def test_memory_defaults(self):
        mem = Memory(key="k1", value="v1")
        assert mem.key == "k1"
        assert mem.value == "v1"
        assert mem.namespace == "default"
        assert mem.metadata == {}
        assert isinstance(mem.created_at, datetime)

    def test_memory_with_metadata(self):
        mem = Memory(key="k2", value="v2", metadata={"source": "test"})
        assert mem.metadata["source"] == "test"


class TestAgentRunModel:
    """Tests for AgentRun Pydantic model."""

    def test_agent_run_defaults(self):
        run = AgentRun(
            id="r1", agent_name="test", task="Test task", status=TaskStatus.IN_PROGRESS
        )
        assert run.id == "r1"
        assert run.agent_name == "test"
        assert run.task == "Test task"
        assert run.status == TaskStatus.IN_PROGRESS
        assert run.completed_at is None
        assert run.tokens_used == 0
        assert run.result is None


class TestAgentEventModel:
    """Tests for AgentEvent Pydantic model."""

    def test_agent_event_defaults(self):
        event = AgentEvent(
            id="e1", agent_name="test", event_type=AgentEventType.HEARTBEAT
        )
        assert event.id == "e1"
        assert event.agent_name == "test"
        assert event.event_type == AgentEventType.HEARTBEAT
        assert event.event_data == {}
        assert isinstance(event.timestamp, datetime)

    def test_agent_event_with_data(self):
        event = AgentEvent(
            id="e2",
            agent_name="test",
            event_type=AgentEventType.TASK_COMPLETE,
            event_data={"task_id": "t1", "result": "success"},
        )
        assert event.event_data["task_id"] == "t1"


class TestTaskDependencyModel:
    """Tests for TaskDependency Pydantic model."""

    def test_task_dependency_defaults(self):
        dep = TaskDependency(task_id="t2", depends_on="t1")
        assert dep.task_id == "t2"
        assert dep.depends_on == "t1"
        assert dep.dependency_type == DependencyType.FINISH_START


class TestScheduledTaskModel:
    """Tests for ScheduledTask Pydantic model."""

    def test_scheduled_task_inherits_task(self):
        stask = ScheduledTask(id="st1", description="Scheduled task")
        assert stask.id == "st1"
        assert stask.description == "Scheduled task"
        assert stask.status == TaskStatus.PENDING  # Inherited

    def test_scheduled_task_extra_fields(self):
        stask = ScheduledTask(
            id="st2",
            description="Task with deps",
            dependencies=[TaskDependency(task_id="st2", depends_on="st1")],
            retry_count=1,
            max_retries=5,
            priority=8,
        )
        assert len(stask.dependencies) == 1
        assert stask.retry_count == 1
        assert stask.max_retries == 5
        assert stask.priority == 8

    def test_scheduled_task_priority_bounds(self):
        """priority must be between 1 and 10."""
        with pytest.raises(ValueError):
            ScheduledTask(id="st", description="test", priority=0)
        with pytest.raises(ValueError):
            ScheduledTask(id="st", description="test", priority=11)


class TestSwarmStatusModel:
    """Tests for SwarmStatus Pydantic model."""

    def test_swarm_status_creation(self):
        status = SwarmStatus(
            total_agents=5, active_tasks=2, completed_tasks=10, agents=[]
        )
        assert status.total_agents == 5
        assert status.active_tasks == 2
        assert status.completed_tasks == 10
        assert status.agents == []
        assert status.recent_runs == []
