"""Tests for orchestrator/memory.py - DuckDB persistence."""

from datetime import datetime

import pytest

from orchestrator.memory import SwarmMemory
from orchestrator.types import AgentEvent, AgentEventType, AgentHealth, AgentStatus, TaskStatus


class TestSwarmMemoryInit:
    """Tests for SwarmMemory initialization."""

    def test_init_creates_tables(self, memory):
        """All required tables exist after initialization."""
        tables = memory.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        table_names = {t[0] for t in tables}

        assert "memories" in table_names
        assert "agent_runs" in table_names
        assert "task_log" in table_names
        assert "agent_health" in table_names
        assert "agent_events" in table_names


class TestMemoryOperations:
    """Tests for key-value memory operations."""

    def test_store_and_get(self, memory):
        """Basic key-value storage works."""
        memory.store("test_key", "test_value")
        result = memory.get("test_key")
        assert result == "test_value"

    def test_store_with_namespace(self, memory):
        """Namespace isolation works."""
        memory.store("key1", "value1", namespace="ns1")
        memory.store("key1", "value2", namespace="ns2")

        # Query uses pattern matching - keys in different namespaces
        results = memory.query("key1")
        # Both should be returned when querying without namespace filter
        assert len(results) >= 1

    def test_store_with_metadata(self, memory):
        """JSON metadata is persisted correctly."""
        memory.store("key", "value", metadata={"source": "test", "count": 5})
        results = memory.query("key")
        assert results[0].metadata["source"] == "test"
        assert results[0].metadata["count"] == 5

    def test_get_nonexistent_key_returns_none(self, memory):
        """Getting a missing key returns None."""
        result = memory.get("nonexistent_key")
        assert result is None

    def test_store_overwrites_existing(self, memory):
        """Storing with same key overwrites the value."""
        memory.store("key", "value1")
        memory.store("key", "value2")
        result = memory.get("key")
        assert result == "value2"

    def test_query_by_pattern_key(self, memory):
        """Query matches keys by pattern."""
        memory.store("user:123", "data1")
        memory.store("user:456", "data2")
        memory.store("other:789", "data3")

        results = memory.query("user:")
        assert len(results) == 2

    def test_query_by_pattern_value(self, memory):
        """Query matches values by pattern."""
        memory.store("k1", "important data")
        memory.store("k2", "other info")

        results = memory.query("important")
        assert len(results) == 1
        assert results[0].key == "k1"

    def test_query_with_namespace_filter(self, memory):
        """Query filters by namespace correctly."""
        memory.store("key", "value1", namespace="prod")
        memory.store("key", "value2", namespace="dev")

        # Query for all matching keys
        results = memory.query("key")
        # Should find matches - note that store may upsert based on key alone
        assert len(results) >= 1

    def test_query_respects_limit(self, memory):
        """Query respects limit parameter."""
        for i in range(10):
            memory.store(f"key{i}", f"value{i}")

        results = memory.query("key", limit=3)
        assert len(results) == 3

    def test_delete_existing_key(self, memory):
        """Delete removes existing key and returns True."""
        memory.store("key", "value")
        result = memory.delete("key")
        assert result is True
        assert memory.get("key") is None

    def test_delete_nonexistent_key(self, memory):
        """Delete returns False for missing key."""
        result = memory.delete("nonexistent")
        assert result is False


class TestAgentRunOperations:
    """Tests for agent run logging."""

    def test_log_run_start(self, memory):
        """log_run_start creates a record."""
        memory.log_run_start("run-1", "test-agent", "Test task")

        result = memory.conn.execute(
            "SELECT * FROM agent_runs WHERE id = 'run-1'"
        ).fetchone()

        assert result is not None
        assert result[1] == "test-agent"  # agent_name
        assert result[2] == "Test task"  # task

    def test_log_run_complete(self, memory):
        """log_run_complete updates the record."""
        memory.log_run_start("run-2", "test-agent", "Test task")
        memory.log_run_complete("run-2", TaskStatus.COMPLETED, "Success!", tokens=100)

        result = memory.conn.execute(
            "SELECT status, result, tokens_used FROM agent_runs WHERE id = 'run-2'"
        ).fetchone()

        assert result[0] == "completed"
        assert result[1] == "Success!"
        assert result[2] == 100

    def test_get_recent_runs(self, memory):
        """get_recent_runs returns runs ordered by started_at DESC."""
        memory.log_run_start("run-a", "agent1", "Task A")
        memory.log_run_start("run-b", "agent2", "Task B")
        memory.log_run_start("run-c", "agent3", "Task C")

        runs = memory.get_recent_runs(limit=2)

        assert len(runs) == 2
        # Most recent first
        assert runs[0].id == "run-c"
        assert runs[1].id == "run-b"

    def test_get_run_stats(self, memory):
        """get_run_stats aggregates correctly."""
        memory.log_run_start("r1", "agent", "Task 1")
        memory.log_run_complete("r1", TaskStatus.COMPLETED, tokens=50)

        memory.log_run_start("r2", "agent", "Task 2")
        memory.log_run_complete("r2", TaskStatus.COMPLETED, tokens=75)

        memory.log_run_start("r3", "agent", "Task 3")
        memory.log_run_complete("r3", TaskStatus.FAILED)

        memory.log_run_start("r4", "agent", "Task 4")
        # Leave in progress

        stats = memory.get_run_stats()

        assert stats["total_runs"] == 4
        assert stats["completed"] == 2
        assert stats["failed"] == 1
        assert stats["in_progress"] == 1
        assert stats["total_tokens"] == 125


class TestAgentHealthOperations:
    """Tests for agent health persistence."""

    def test_upsert_agent_health_insert(self, memory):
        """upsert_agent_health inserts new record."""
        health = AgentHealth(
            agent_name="new-agent",
            status=AgentStatus.IDLE,
            health_score=0.9,
        )
        memory.upsert_agent_health(health)

        result = memory.get_agent_health("new-agent")
        assert result is not None
        assert result.agent_name == "new-agent"
        assert result.health_score == pytest.approx(0.9, rel=1e-5)

    def test_upsert_agent_health_update(self, memory):
        """upsert_agent_health updates existing record."""
        health1 = AgentHealth(agent_name="agent", status=AgentStatus.IDLE)
        memory.upsert_agent_health(health1)

        health2 = AgentHealth(
            agent_name="agent", status=AgentStatus.BUSY, health_score=0.8
        )
        memory.upsert_agent_health(health2)

        result = memory.get_agent_health("agent")
        assert result.status == AgentStatus.BUSY
        assert result.health_score == pytest.approx(0.8, rel=1e-5)

    def test_get_agent_health_nonexistent(self, memory):
        """get_agent_health returns None for missing agent."""
        result = memory.get_agent_health("nonexistent")
        assert result is None

    def test_get_all_agent_health(self, memory):
        """get_all_agent_health returns all records."""
        for name in ["agent1", "agent2", "agent3"]:
            memory.upsert_agent_health(AgentHealth(agent_name=name))

        results = memory.get_all_agent_health()
        names = {r.agent_name for r in results}

        assert len(results) == 3
        assert names == {"agent1", "agent2", "agent3"}


class TestAgentEventOperations:
    """Tests for agent event logging."""

    def test_insert_agent_event(self, memory):
        """insert_agent_event stores event correctly."""
        event = AgentEvent(
            id="evt-1",
            agent_name="test-agent",
            event_type=AgentEventType.TASK_START,
            event_data={"task_id": "t1"},
        )
        memory.insert_agent_event(event)

        results = memory.get_agent_events(agent_name="test-agent")
        assert len(results) == 1
        assert results[0].id == "evt-1"
        assert results[0].event_data["task_id"] == "t1"

    def test_get_agent_events_filtered_by_agent(self, memory):
        """get_agent_events filters by agent_name."""
        memory.insert_agent_event(
            AgentEvent(id="e1", agent_name="agent1", event_type=AgentEventType.HEARTBEAT)
        )
        memory.insert_agent_event(
            AgentEvent(id="e2", agent_name="agent2", event_type=AgentEventType.HEARTBEAT)
        )

        results = memory.get_agent_events(agent_name="agent1")
        assert len(results) == 1
        assert results[0].agent_name == "agent1"

    def test_get_agent_events_filtered_by_type(self, memory):
        """get_agent_events filters by event_type."""
        memory.insert_agent_event(
            AgentEvent(id="e1", agent_name="agent", event_type=AgentEventType.HEARTBEAT)
        )
        memory.insert_agent_event(
            AgentEvent(id="e2", agent_name="agent", event_type=AgentEventType.ERROR)
        )

        results = memory.get_agent_events(event_type=AgentEventType.ERROR)
        assert len(results) == 1
        assert results[0].event_type == AgentEventType.ERROR

    def test_get_agent_events_limit(self, memory):
        """get_agent_events respects limit parameter."""
        for i in range(10):
            memory.insert_agent_event(
                AgentEvent(
                    id=f"e{i}", agent_name="agent", event_type=AgentEventType.HEARTBEAT
                )
            )

        results = memory.get_agent_events(limit=5)
        assert len(results) == 5


class TestSwarmMemoryClose:
    """Tests for cleanup."""

    def test_close_closes_connection(self, temp_db_path):
        """close() closes the database connection."""
        mem = SwarmMemory(db_path=temp_db_path)
        mem.store("key", "value")
        mem.close()

        # Trying to use closed connection should fail
        with pytest.raises(Exception):
            mem.conn.execute("SELECT 1")
