"""Shared pytest fixtures for orchestrator tests."""

import shutil
from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pytest

from orchestrator.agent_registry import AgentRegistry
from orchestrator.agent_state import AgentStateManager
from orchestrator.coordinator import Coordinator
from orchestrator.events import EventBus
from orchestrator.memory import SwarmMemory
from orchestrator.metrics import MetricsCollector
from orchestrator.scheduler import CircuitBreaker, TaskScheduler
from orchestrator.types import (
    Agent,
    AgentHealth,
    AgentModel,
    AgentStatus,
    Task,
    TaskStatus,
)


# === Path Fixtures ===


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create isolated temp DuckDB path for each test."""
    return tmp_path / "test_memory.duckdb"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_agents_dir(fixtures_dir: Path) -> Path:
    """Path to sample agent fixtures."""
    return fixtures_dir / "agents"


@pytest.fixture
def temp_agents_dir(tmp_path: Path, sample_agents_dir: Path) -> Path:
    """Create temp agents directory with sample .md files."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Copy sample agents if they exist
    if sample_agents_dir.exists():
        for agent_file in sample_agents_dir.glob("*.md"):
            shutil.copy(agent_file, agents_dir / agent_file.name)

    return agents_dir


# === Core Component Fixtures ===


@pytest.fixture
def memory(temp_db_path: Path) -> Generator[SwarmMemory, None, None]:
    """Isolated SwarmMemory instance with temp DuckDB."""
    mem = SwarmMemory(db_path=temp_db_path)
    yield mem
    mem.close()


@pytest.fixture
def registry(temp_agents_dir: Path) -> AgentRegistry:
    """AgentRegistry with test agents."""
    return AgentRegistry(agents_dir=temp_agents_dir)


@pytest.fixture
def coordinator(
    temp_agents_dir: Path, temp_db_path: Path
) -> Generator[Coordinator, None, None]:
    """Fully isolated Coordinator."""
    coord = Coordinator(agents_dir=temp_agents_dir, db_path=temp_db_path)
    yield coord
    coord.close()


@pytest.fixture
def scheduler() -> Generator[TaskScheduler, None, None]:
    """Fresh TaskScheduler instance."""
    sched = TaskScheduler()
    yield sched
    sched.clear()


@pytest.fixture
def circuit_breaker() -> CircuitBreaker:
    """Fresh CircuitBreaker for testing."""
    return CircuitBreaker(
        name="test-breaker",
        failure_threshold=3,
        reset_timeout_seconds=0.1,  # Fast timeout for tests
        half_open_max_requests=1,
    )


@pytest.fixture
def event_bus() -> EventBus:
    """Fresh EventBus (not singleton) for isolated tests."""
    return EventBus()


@pytest.fixture
def metrics() -> MetricsCollector:
    """Fresh MetricsCollector (not singleton) for isolated tests."""
    return MetricsCollector()


@pytest.fixture
def agent_state_manager(memory: SwarmMemory) -> AgentStateManager:
    """AgentStateManager with isolated memory."""
    return AgentStateManager(memory)


# === Sample Data Fixtures ===


@pytest.fixture
def sample_agent() -> Agent:
    """Sample Agent model for testing."""
    return Agent(
        name="test-agent",
        description="A test agent for unit tests",
        model=AgentModel.SONNET,
        color="blue",
        triggers=["test", "example"],
        file_path="/path/to/test-agent.md",
    )


@pytest.fixture
def sample_task() -> Task:
    """Sample Task model for testing."""
    return Task(
        id="test-123",
        description="Test task description",
        agent_name="test-agent",
        status=TaskStatus.PENDING,
    )


@pytest.fixture
def sample_agent_health() -> AgentHealth:
    """Sample AgentHealth model for testing."""
    return AgentHealth(
        agent_name="test-agent",
        status=AgentStatus.IDLE,
        health_score=1.0,
        last_heartbeat=datetime.now(),
        current_task_id=None,
        error_count=0,
        success_count=5,
        total_execution_time_ms=1500.0,
    )


# === Mock Fixtures ===


@pytest.fixture
def mock_langfuse(mocker):
    """Mock Langfuse client for tracing tests."""
    mock_class = mocker.patch("orchestrator.tracing.Langfuse")
    mock_instance = mock_class.return_value
    mock_instance.auth_check.return_value = True
    mock_instance.flush.return_value = None
    mock_instance.shutdown.return_value = None
    return mock_instance


@pytest.fixture
def langfuse_env(monkeypatch):
    """Set Langfuse env vars for testing."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test-123")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test-456")
    monkeypatch.setenv("LANGFUSE_HOST", "https://test.langfuse.com")


@pytest.fixture
def no_langfuse_env(monkeypatch):
    """Ensure Langfuse env vars are not set."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)


# === Helper Fixtures ===


@pytest.fixture
def create_task():
    """Factory fixture for creating Task instances."""

    def _create_task(
        task_id: str = "task-1",
        description: str = "Test task",
        agent_name: str | None = None,
        status: TaskStatus = TaskStatus.PENDING,
    ) -> Task:
        return Task(
            id=task_id,
            description=description,
            agent_name=agent_name,
            status=status,
        )

    return _create_task


@pytest.fixture
def create_agent():
    """Factory fixture for creating Agent instances."""

    def _create_agent(
        name: str = "test-agent",
        description: str = "Test agent",
        model: AgentModel = AgentModel.SONNET,
        triggers: list[str] | None = None,
    ) -> Agent:
        return Agent(
            name=name,
            description=description,
            model=model,
            triggers=triggers or [],
            file_path=f"/agents/{name}.md",
        )

    return _create_agent


@pytest.fixture
def reset_server_singletons():
    """Reset server module singletons between tests."""
    import orchestrator.server as server

    # Store original values
    orig_coord = server._coordinator
    orig_state = server._agent_state_manager
    orig_sched = server._scheduler

    # Reset to None
    server._coordinator = None
    server._agent_state_manager = None
    server._scheduler = None

    yield

    # Restore (cleanup)
    server._coordinator = orig_coord
    server._agent_state_manager = orig_state
    server._scheduler = orig_sched
