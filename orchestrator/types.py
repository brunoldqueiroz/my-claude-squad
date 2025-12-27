"""Pydantic models for the orchestrator."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentModel(str, Enum):
    """Supported Claude models."""

    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


class AgentStatus(str, Enum):
    """Runtime status of an agent."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    OFFLINE = "offline"


class Agent(BaseModel):
    """Agent definition parsed from agents/*.md files."""

    name: str
    description: str
    model: AgentModel = AgentModel.SONNET
    color: str = "white"
    triggers: list[str] = Field(default_factory=list)
    file_path: str = ""


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """A task assigned to an agent."""

    id: str
    description: str
    agent_name: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    result: str | None = None
    trace_id: str | None = None  # Link to observability trace


class Memory(BaseModel):
    """A memory entry stored in DuckDB."""

    key: str
    value: str
    namespace: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class AgentRun(BaseModel):
    """Record of an agent execution."""

    id: str
    agent_name: str
    task: str
    status: TaskStatus
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    tokens_used: int = 0
    result: str | None = None


class SwarmStatus(BaseModel):
    """Current status of the swarm."""

    total_agents: int
    active_tasks: int
    completed_tasks: int
    agents: list[Agent]
    recent_runs: list[AgentRun] = Field(default_factory=list)


class AgentHealth(BaseModel):
    """Health status of an agent at runtime."""

    agent_name: str
    status: AgentStatus = AgentStatus.IDLE
    health_score: float = Field(default=1.0, ge=0.0, le=1.0)
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    current_task_id: str | None = None
    error_count: int = 0
    success_count: int = 0
    total_execution_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of the agent."""
        total = self.success_count + self.error_count
        if total == 0:
            return 1.0
        return self.success_count / total

    @property
    def avg_execution_time_ms(self) -> float:
        """Calculate average execution time per task."""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.total_execution_time_ms / total


class AgentEventType(str, Enum):
    """Types of agent events."""

    HEARTBEAT = "heartbeat"
    STATUS_CHANGE = "status_change"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    ERROR = "error"


class AgentEvent(BaseModel):
    """An event related to an agent's lifecycle."""

    id: str
    agent_name: str
    event_type: AgentEventType
    event_data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class DependencyType(str, Enum):
    """Types of task dependencies."""

    FINISH_START = "finish-start"  # Dependent starts after dependency finishes
    START_START = "start-start"  # Dependent can start when dependency starts
    DATA = "data"  # Dependent needs data output from dependency


class TaskDependency(BaseModel):
    """A dependency relationship between two tasks."""

    task_id: str
    depends_on: str
    dependency_type: DependencyType = DependencyType.FINISH_START


class ScheduledTask(Task):
    """A task with scheduling metadata.

    Extends Task with dependency tracking and retry configuration.
    """

    dependencies: list[TaskDependency] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    circuit_breaker: str | None = None  # Agent circuit breaker to use
    priority: int = Field(default=5, ge=1, le=10)  # 1=lowest, 10=highest
