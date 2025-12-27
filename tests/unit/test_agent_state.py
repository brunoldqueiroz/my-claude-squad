"""Tests for orchestrator/agent_state.py - AgentStateManager."""

from datetime import datetime, timedelta

import pytest

from orchestrator.agent_state import AgentStateManager
from orchestrator.types import AgentStatus


class TestAgentStateManagerInit:
    """Tests for AgentStateManager initialization."""

    def test_initializes_with_memory(self, agent_state_manager):
        """Can initialize with memory instance."""
        assert agent_state_manager is not None

    def test_loads_existing_states(self, memory):
        """Loads previously persisted agent states."""
        from orchestrator.types import AgentHealth

        # Pre-persist some health data
        health = AgentHealth(agent_name="pre-existing", status=AgentStatus.IDLE, health_score=0.8)
        memory.upsert_agent_health(health)

        # Create new manager - should load the state
        manager = AgentStateManager(memory)

        loaded = manager.get_health("pre-existing")
        assert loaded is not None
        assert loaded.health_score == pytest.approx(0.8, rel=1e-5)


class TestAgentStateManagerInitializeAgent:
    """Tests for initialize_agent."""

    def test_initialize_creates_new_state(self, agent_state_manager):
        """Initialize creates new health state for agent."""
        health = agent_state_manager.initialize_agent("new-agent")

        assert health is not None
        assert health.agent_name == "new-agent"
        assert health.status == AgentStatus.IDLE

    def test_initialize_returns_existing(self, agent_state_manager):
        """Initialize returns existing state if already present."""
        health1 = agent_state_manager.initialize_agent("agent-a")
        health1.health_score = 0.5

        health2 = agent_state_manager.initialize_agent("agent-a")

        assert health1 is health2
        assert health2.health_score == 0.5


class TestAgentStateManagerStatus:
    """Tests for status management."""

    def test_set_status_updates(self, agent_state_manager):
        """set_status updates agent status."""
        agent_state_manager.initialize_agent("agent")

        health = agent_state_manager.set_status("agent", AgentStatus.BUSY, reason="task")

        assert health.status == AgentStatus.BUSY

    def test_set_status_to_error_decreases_score(self, agent_state_manager):
        """Setting status to ERROR decreases health score."""
        agent_state_manager.initialize_agent("agent")
        initial_score = agent_state_manager.get_health("agent").health_score

        agent_state_manager.set_status("agent", AgentStatus.ERROR)

        new_score = agent_state_manager.get_health("agent").health_score
        assert new_score < initial_score

    def test_set_status_to_idle_increases_score(self, agent_state_manager):
        """Setting status to IDLE slightly increases health score."""
        agent_state_manager.initialize_agent("agent")
        health = agent_state_manager.get_health("agent")
        health.health_score = 0.8  # Set below max

        agent_state_manager.set_status("agent", AgentStatus.IDLE)

        assert agent_state_manager.get_health("agent").health_score > 0.8

    def test_set_status_initializes_if_missing(self, agent_state_manager):
        """set_status initializes agent if not already present."""
        health = agent_state_manager.set_status("new-agent", AgentStatus.BUSY)

        assert health is not None
        assert health.status == AgentStatus.BUSY


class TestAgentStateManagerHeartbeat:
    """Tests for heartbeat recording."""

    def test_heartbeat_updates_timestamp(self, agent_state_manager):
        """record_heartbeat updates last_heartbeat timestamp."""
        agent_state_manager.initialize_agent("agent")
        old_heartbeat = agent_state_manager.get_health("agent").last_heartbeat

        health = agent_state_manager.record_heartbeat("agent")

        assert health.last_heartbeat > old_heartbeat

    def test_heartbeat_restores_offline_to_idle(self, agent_state_manager):
        """Heartbeat restores offline agent to idle."""
        agent_state_manager.initialize_agent("agent")
        agent_state_manager.set_status("agent", AgentStatus.OFFLINE)

        health = agent_state_manager.record_heartbeat("agent")

        assert health.status == AgentStatus.IDLE

    def test_heartbeat_restores_error_to_idle(self, agent_state_manager):
        """Heartbeat restores error agent to idle."""
        agent_state_manager.initialize_agent("agent")
        agent_state_manager.set_status("agent", AgentStatus.ERROR)

        health = agent_state_manager.record_heartbeat("agent")

        assert health.status == AgentStatus.IDLE

    def test_heartbeat_initializes_if_missing(self, agent_state_manager):
        """record_heartbeat initializes agent if not present."""
        health = agent_state_manager.record_heartbeat("new-agent")

        assert health is not None


class TestAgentStateManagerTaskLifecycle:
    """Tests for task start/complete."""

    def test_task_start_sets_busy(self, agent_state_manager):
        """record_task_start sets status to BUSY."""
        agent_state_manager.initialize_agent("agent")

        health = agent_state_manager.record_task_start("agent", "task-123")

        assert health.status == AgentStatus.BUSY
        assert health.current_task_id == "task-123"

    def test_task_complete_success_updates_stats(self, agent_state_manager):
        """record_task_complete with success updates stats."""
        agent_state_manager.initialize_agent("agent")
        agent_state_manager.record_task_start("agent", "task-123")

        health = agent_state_manager.record_task_complete("agent", success=True, duration_ms=100.0)

        assert health.status == AgentStatus.IDLE
        assert health.current_task_id is None
        assert health.success_count == 1
        assert health.total_execution_time_ms == 100.0

    def test_task_complete_failure_updates_stats(self, agent_state_manager):
        """record_task_complete with failure updates stats."""
        agent_state_manager.initialize_agent("agent")
        agent_state_manager.record_task_start("agent", "task-456")

        health = agent_state_manager.record_task_complete("agent", success=False, duration_ms=50.0)

        assert health.error_count == 1
        assert health.status == AgentStatus.IDLE

    def test_task_success_increases_health(self, agent_state_manager):
        """Successful task increases health score."""
        agent_state_manager.initialize_agent("agent")
        health = agent_state_manager.get_health("agent")
        health.health_score = 0.8
        agent_state_manager.record_task_start("agent", "task")

        health = agent_state_manager.record_task_complete("agent", success=True, duration_ms=100.0)

        assert health.health_score > 0.8

    def test_task_failure_decreases_health(self, agent_state_manager):
        """Failed task decreases health score."""
        agent_state_manager.initialize_agent("agent")
        initial_score = agent_state_manager.get_health("agent").health_score
        agent_state_manager.record_task_start("agent", "task")

        health = agent_state_manager.record_task_complete("agent", success=False, duration_ms=100.0)

        assert health.health_score < initial_score


class TestAgentStateManagerError:
    """Tests for error recording."""

    def test_record_error_increments_count(self, agent_state_manager):
        """record_error increments error count."""
        agent_state_manager.initialize_agent("agent")

        health = agent_state_manager.record_error("agent", "Something went wrong")

        assert health.error_count == 1

    def test_record_error_decreases_health(self, agent_state_manager):
        """record_error decreases health score."""
        agent_state_manager.initialize_agent("agent")
        initial = agent_state_manager.get_health("agent").health_score

        agent_state_manager.record_error("agent", "Error!")

        assert agent_state_manager.get_health("agent").health_score < initial

    def test_record_error_can_set_status(self, agent_state_manager):
        """record_error can set status to ERROR."""
        agent_state_manager.initialize_agent("agent")

        health = agent_state_manager.record_error("agent", "Fatal error", set_error_status=True)

        assert health.status == AgentStatus.ERROR


class TestAgentStateManagerQueries:
    """Tests for agent queries."""

    def test_get_health_returns_state(self, agent_state_manager):
        """get_health returns agent's health state."""
        agent_state_manager.initialize_agent("agent")

        health = agent_state_manager.get_health("agent")

        assert health is not None
        assert health.agent_name == "agent"

    def test_get_health_nonexistent(self, agent_state_manager):
        """get_health returns None for unknown agent."""
        health = agent_state_manager.get_health("nonexistent")

        assert health is None

    def test_get_all_health(self, agent_state_manager):
        """get_all_health returns all agents."""
        agent_state_manager.initialize_agent("agent1")
        agent_state_manager.initialize_agent("agent2")

        all_health = agent_state_manager.get_all_health()

        names = [h.agent_name for h in all_health]
        assert "agent1" in names
        assert "agent2" in names

    def test_get_available_agents(self, agent_state_manager):
        """get_available_agents returns idle agents."""
        agent_state_manager.initialize_agent("idle1")
        agent_state_manager.initialize_agent("idle2")
        agent_state_manager.initialize_agent("busy")
        agent_state_manager.set_status("busy", AgentStatus.BUSY)

        available = agent_state_manager.get_available_agents()

        assert "idle1" in available
        assert "idle2" in available
        assert "busy" not in available

    def test_get_busy_agents(self, agent_state_manager):
        """get_busy_agents returns busy agents."""
        agent_state_manager.initialize_agent("idle")
        agent_state_manager.initialize_agent("busy1")
        agent_state_manager.initialize_agent("busy2")
        agent_state_manager.set_status("busy1", AgentStatus.BUSY)
        agent_state_manager.set_status("busy2", AgentStatus.BUSY)

        busy = agent_state_manager.get_busy_agents()

        assert "busy1" in busy
        assert "busy2" in busy
        assert "idle" not in busy


class TestAgentStateManagerStaleDetection:
    """Tests for stale agent detection."""

    def test_check_stale_agents(self, agent_state_manager):
        """check_stale_agents finds agents without recent heartbeat."""
        agent_state_manager.initialize_agent("stale")
        health = agent_state_manager.get_health("stale")
        # Set last heartbeat to long ago
        health.last_heartbeat = datetime.now() - timedelta(seconds=600)

        stale = agent_state_manager.check_stale_agents(timeout_seconds=300)

        assert "stale" in stale

    def test_check_stale_sets_offline(self, agent_state_manager):
        """check_stale_agents sets stale agents to OFFLINE."""
        agent_state_manager.initialize_agent("stale")
        health = agent_state_manager.get_health("stale")
        health.last_heartbeat = datetime.now() - timedelta(seconds=600)

        agent_state_manager.check_stale_agents(timeout_seconds=300)

        assert agent_state_manager.get_health("stale").status == AgentStatus.OFFLINE

    def test_check_stale_ignores_already_offline(self, agent_state_manager):
        """check_stale_agents ignores already offline agents."""
        agent_state_manager.initialize_agent("offline")
        agent_state_manager.set_status("offline", AgentStatus.OFFLINE)
        health = agent_state_manager.get_health("offline")
        health.last_heartbeat = datetime.now() - timedelta(seconds=600)

        stale = agent_state_manager.check_stale_agents(timeout_seconds=300)

        assert "offline" not in stale

    def test_check_stale_recent_heartbeat_ok(self, agent_state_manager):
        """check_stale_agents does not flag agents with recent heartbeat."""
        agent_state_manager.initialize_agent("fresh")
        agent_state_manager.record_heartbeat("fresh")

        stale = agent_state_manager.check_stale_agents(timeout_seconds=300)

        assert "fresh" not in stale
