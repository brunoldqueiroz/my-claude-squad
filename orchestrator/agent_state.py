"""Agent state management for runtime health tracking.

Tracks agent status (idle/busy/error), health metrics, and events.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from orchestrator.types import AgentEvent, AgentEventType, AgentHealth, AgentStatus

if TYPE_CHECKING:
    from orchestrator.memory import SwarmMemory

logger = logging.getLogger(__name__)


class AgentStateManager:
    """Manages runtime state for all agents.

    Tracks:
    - Agent status (idle, busy, error, etc.)
    - Health metrics (success rate, execution time)
    - Heartbeats for liveness detection
    - Events for debugging/observability
    """

    def __init__(self, memory: "SwarmMemory"):
        """Initialize the state manager.

        Args:
            memory: SwarmMemory instance for persistence
        """
        self._memory = memory
        self._states: dict[str, AgentHealth] = {}
        self._load_states()

    def _load_states(self) -> None:
        """Load agent states from persistent storage."""
        try:
            states = self._memory.get_all_agent_health()
            for state in states:
                self._states[state.agent_name] = state
            logger.debug(f"Loaded {len(states)} agent states from database")
        except Exception as e:
            logger.warning(f"Failed to load agent states: {e}")

    def initialize_agent(self, agent_name: str) -> AgentHealth:
        """Initialize or get an agent's health state.

        Args:
            agent_name: Name of the agent

        Returns:
            The agent's health state
        """
        if agent_name in self._states:
            return self._states[agent_name]

        health = AgentHealth(
            agent_name=agent_name,
            status=AgentStatus.IDLE,
        )
        self._states[agent_name] = health
        self._persist_health(health)
        self._emit_event(agent_name, AgentEventType.STATUS_CHANGE, {
            "new_status": AgentStatus.IDLE.value,
            "reason": "initialized",
        })
        return health

    def get_health(self, agent_name: str) -> AgentHealth | None:
        """Get an agent's current health state.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentHealth or None if agent not found
        """
        return self._states.get(agent_name)

    def get_all_health(self) -> list[AgentHealth]:
        """Get health states for all agents.

        Returns:
            List of all agent health states
        """
        return list(self._states.values())

    def set_status(
        self,
        agent_name: str,
        status: AgentStatus,
        reason: str | None = None,
    ) -> AgentHealth:
        """Set an agent's status.

        Args:
            agent_name: Name of the agent
            status: New status to set
            reason: Optional reason for status change

        Returns:
            Updated health state
        """
        health = self._states.get(agent_name)
        if health is None:
            health = self.initialize_agent(agent_name)

        old_status = health.status
        health.status = status
        health.updated_at = datetime.now()

        # Update health score based on status
        if status == AgentStatus.ERROR:
            health.health_score = max(0.0, health.health_score - 0.1)
        elif status == AgentStatus.IDLE:
            health.health_score = min(1.0, health.health_score + 0.01)

        self._persist_health(health)

        if old_status != status:
            self._emit_event(agent_name, AgentEventType.STATUS_CHANGE, {
                "old_status": old_status.value,
                "new_status": status.value,
                "reason": reason,
            })

        return health

    def record_heartbeat(self, agent_name: str) -> AgentHealth:
        """Record a heartbeat for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Updated health state
        """
        health = self._states.get(agent_name)
        if health is None:
            health = self.initialize_agent(agent_name)

        health.last_heartbeat = datetime.now()
        health.updated_at = datetime.now()

        # If agent was offline/error, restore to idle on heartbeat
        if health.status in (AgentStatus.OFFLINE, AgentStatus.ERROR):
            health.status = AgentStatus.IDLE
            health.health_score = min(1.0, health.health_score + 0.05)

        self._persist_health(health)
        self._emit_event(agent_name, AgentEventType.HEARTBEAT, {})

        return health

    def record_task_start(self, agent_name: str, task_id: str) -> AgentHealth:
        """Record that an agent started a task.

        Args:
            agent_name: Name of the agent
            task_id: ID of the task being started

        Returns:
            Updated health state
        """
        health = self._states.get(agent_name)
        if health is None:
            health = self.initialize_agent(agent_name)

        health.status = AgentStatus.BUSY
        health.current_task_id = task_id
        health.last_heartbeat = datetime.now()
        health.updated_at = datetime.now()

        self._persist_health(health)
        self._emit_event(agent_name, AgentEventType.TASK_START, {
            "task_id": task_id,
        })

        return health

    def record_task_complete(
        self,
        agent_name: str,
        success: bool,
        duration_ms: float,
    ) -> AgentHealth:
        """Record that an agent completed a task.

        Args:
            agent_name: Name of the agent
            success: Whether the task succeeded
            duration_ms: How long the task took in milliseconds

        Returns:
            Updated health state
        """
        health = self._states.get(agent_name)
        if health is None:
            health = self.initialize_agent(agent_name)

        task_id = health.current_task_id
        health.status = AgentStatus.IDLE
        health.current_task_id = None
        health.total_execution_time_ms += duration_ms
        health.last_heartbeat = datetime.now()
        health.updated_at = datetime.now()

        if success:
            health.success_count += 1
            health.health_score = min(1.0, health.health_score + 0.02)
            event_type = AgentEventType.TASK_COMPLETE
        else:
            health.error_count += 1
            health.health_score = max(0.0, health.health_score - 0.05)
            event_type = AgentEventType.TASK_FAILED

        self._persist_health(health)
        self._emit_event(agent_name, event_type, {
            "task_id": task_id,
            "success": success,
            "duration_ms": duration_ms,
        })

        return health

    def record_error(
        self,
        agent_name: str,
        error_message: str,
        set_error_status: bool = False,
    ) -> AgentHealth:
        """Record an error for an agent.

        Args:
            agent_name: Name of the agent
            error_message: Description of the error
            set_error_status: Whether to set agent status to ERROR

        Returns:
            Updated health state
        """
        health = self._states.get(agent_name)
        if health is None:
            health = self.initialize_agent(agent_name)

        health.error_count += 1
        health.health_score = max(0.0, health.health_score - 0.1)
        health.updated_at = datetime.now()

        if set_error_status:
            health.status = AgentStatus.ERROR
            health.current_task_id = None

        self._persist_health(health)
        self._emit_event(agent_name, AgentEventType.ERROR, {
            "error_message": error_message,
            "status_set_to_error": set_error_status,
        })

        return health

    def get_available_agents(self) -> list[str]:
        """Get list of agents that are available for tasks.

        Returns:
            List of agent names that are idle
        """
        return [
            name for name, health in self._states.items()
            if health.status == AgentStatus.IDLE
        ]

    def get_busy_agents(self) -> list[str]:
        """Get list of agents currently working on tasks.

        Returns:
            List of agent names that are busy
        """
        return [
            name for name, health in self._states.items()
            if health.status == AgentStatus.BUSY
        ]

    def check_stale_agents(self, timeout_seconds: float = 300.0) -> list[str]:
        """Check for agents that haven't sent a heartbeat recently.

        Args:
            timeout_seconds: How long without heartbeat before considering stale

        Returns:
            List of agent names that are stale
        """
        now = datetime.now()
        stale_agents = []

        for name, health in self._states.items():
            if health.status == AgentStatus.OFFLINE:
                continue

            elapsed = (now - health.last_heartbeat).total_seconds()
            if elapsed > timeout_seconds:
                stale_agents.append(name)
                self.set_status(
                    name,
                    AgentStatus.OFFLINE,
                    reason=f"No heartbeat for {elapsed:.0f}s",
                )

        return stale_agents

    def _persist_health(self, health: AgentHealth) -> None:
        """Persist agent health to database.

        Args:
            health: Health state to persist
        """
        try:
            self._memory.upsert_agent_health(health)
        except Exception as e:
            logger.warning(f"Failed to persist agent health for {health.agent_name}: {e}")

    def _emit_event(
        self,
        agent_name: str,
        event_type: AgentEventType,
        event_data: dict,
    ) -> None:
        """Emit an agent event.

        Emits to both the EventBus (in-memory) and persists to database.

        Args:
            agent_name: Name of the agent
            event_type: Type of event
            event_data: Event data dictionary
        """
        from .events import get_event_bus

        event = AgentEvent(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            event_type=event_type,
            event_data=event_data,
        )

        # Emit to EventBus for real-time event handling
        try:
            event_bus = get_event_bus()
            event_bus.emit_sync(event)
        except Exception as e:
            logger.debug(f"Failed to emit event to bus: {e}")

        # Persist to database for history
        try:
            self._memory.insert_agent_event(event)
        except Exception as e:
            logger.debug(f"Failed to persist agent event: {e}")
