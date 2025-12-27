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


class ExecutionMode(str, Enum):
    """How subtasks should be executed relative to siblings."""

    PARALLEL = "parallel"  # Can run simultaneously with other parallel tasks
    SEQUENTIAL = "sequential"  # Must wait for previous tasks


class TopologyType(str, Enum):
    """Swarm coordination topology patterns."""

    HIERARCHICAL = "hierarchical"  # Queen-Worker: coordinator delegates to workers
    MESH = "mesh"  # Peer-to-peer: all agents can collaborate directly
    RING = "ring"  # Pipeline: sequential processing A -> B -> C
    STAR = "star"  # Hub-spoke: central coordinator with specialized workers


class SwarmRole(str, Enum):
    """Role of an agent within a swarm topology."""

    COORDINATOR = "coordinator"  # Queen/Hub - manages other agents
    WORKER = "worker"  # Performs delegated tasks
    PEER = "peer"  # Equal participant in mesh topology


class SwarmMember(BaseModel):
    """An agent's membership in a swarm."""

    agent_name: str
    role: SwarmRole
    position: int = 0  # Position in ring topology (0-indexed)
    can_delegate_to: list[str] = Field(default_factory=list)  # Agents this member can delegate to
    reports_to: str | None = None  # Agent this member reports results to


class Swarm(BaseModel):
    """A coordinated group of agents working together.

    Swarms define how agents collaborate:
    - Hierarchical: Queen coordinates workers
    - Mesh: Peers collaborate freely
    - Ring: Sequential pipeline
    - Star: Hub delegates to spokes
    """

    id: str
    name: str
    topology: TopologyType
    members: list[SwarmMember] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_coordinator(self) -> SwarmMember | None:
        """Get the coordinator/queen/hub agent if any."""
        for member in self.members:
            if member.role == SwarmRole.COORDINATOR:
                return member
        return None

    def get_workers(self) -> list[SwarmMember]:
        """Get all worker agents."""
        return [m for m in self.members if m.role == SwarmRole.WORKER]

    def get_peers(self) -> list[SwarmMember]:
        """Get all peer agents (mesh topology)."""
        return [m for m in self.members if m.role == SwarmRole.PEER]

    def get_ring_order(self) -> list[SwarmMember]:
        """Get members in ring order by position."""
        return sorted(self.members, key=lambda m: m.position)


class SessionStatus(str, Enum):
    """Status of a session."""

    ACTIVE = "active"  # Session is currently running
    PAUSED = "paused"  # Session is paused, can be resumed
    COMPLETED = "completed"  # Session finished successfully
    FAILED = "failed"  # Session failed with errors
    CANCELLED = "cancelled"  # Session was cancelled by user


class SessionTask(BaseModel):
    """A task within a session with tracking info."""

    task_id: str
    description: str
    agent_name: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    order: int = 0  # Execution order within session
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: str | None = None
    error: str | None = None


class Session(BaseModel):
    """A persistent, resumable work session.

    Sessions track multi-task workflows that can be:
    - Paused and resumed later
    - Persisted across restarts
    - Associated with swarms for topology-aware execution
    """

    id: str
    name: str
    description: str | None = None
    status: SessionStatus = SessionStatus.ACTIVE
    swarm_id: str | None = None  # Optional associated swarm
    tasks: list[SessionTask] = Field(default_factory=list)
    current_task_index: int = 0  # Index of currently executing task
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    paused_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def progress(self) -> float:
        """Calculate session progress as percentage (0.0 to 1.0)."""
        if not self.tasks:
            return 0.0
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        return completed / len(self.tasks)

    @property
    def current_task(self) -> SessionTask | None:
        """Get the current task being executed."""
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None

    def get_pending_tasks(self) -> list[SessionTask]:
        """Get all pending tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def get_completed_tasks(self) -> list[SessionTask]:
        """Get all completed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED]

    def get_failed_tasks(self) -> list[SessionTask]:
        """Get all failed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]


class Subtask(BaseModel):
    """A decomposed subtask from Claude Code's analysis."""

    id: str
    description: str
    agent: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    priority: int = Field(default=5, ge=1, le=10)
    reasoning: str | None = None  # Why this agent was chosen


class DecompositionResult(BaseModel):
    """Result of task decomposition by Claude Code."""

    original_task: str
    subtasks: list[Subtask]
    parallel_groups: list[list[str]] = Field(default_factory=list)  # Groups of task IDs that can run together
    execution_order: list[str] = Field(default_factory=list)  # Suggested order respecting dependencies
    analysis: str | None = None  # Claude's analysis of the task
