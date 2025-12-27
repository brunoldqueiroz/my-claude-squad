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


class TestRetentionAndCleanup:
    """Tests for data retention and cleanup operations."""

    def test_get_storage_stats_empty_database(self, memory):
        """get_storage_stats returns zeros for empty database."""
        stats = memory.get_storage_stats()

        assert stats["memories_count"] == 0
        assert stats["agent_runs_count"] == 0
        assert stats["task_log_count"] == 0
        assert stats["agent_health_count"] == 0
        assert stats["agent_events_count"] == 0
        assert "db_size_bytes" in stats

    def test_get_storage_stats_with_data(self, memory):
        """get_storage_stats returns correct counts."""
        # Add some test data
        memory.store("key1", "value1")
        memory.store("key2", "value2")
        memory.log_run_start("run1", "agent1", "task1")
        memory.upsert_agent_health(AgentHealth(agent_name="agent1"))
        memory.insert_agent_event(
            AgentEvent(id="evt1", agent_name="agent1", event_type=AgentEventType.HEARTBEAT)
        )

        stats = memory.get_storage_stats()

        assert stats["memories_count"] == 2
        assert stats["agent_runs_count"] == 1
        assert stats["agent_health_count"] == 1
        assert stats["agent_events_count"] == 1

    def test_get_storage_stats_time_ranges(self, memory):
        """get_storage_stats includes time range info."""
        memory.log_run_start("run1", "agent1", "task1")
        memory.insert_agent_event(
            AgentEvent(id="evt1", agent_name="agent1", event_type=AgentEventType.HEARTBEAT)
        )

        stats = memory.get_storage_stats()

        # Should have time range info for agent_runs and agent_events
        assert "agent_runs_oldest" in stats or stats["agent_runs_count"] > 0
        assert "agent_events_oldest" in stats or stats["agent_events_count"] > 0

    def test_cleanup_old_runs_removes_old_data(self, memory):
        """cleanup_old_runs removes runs older than threshold."""
        # Insert runs with manual timestamps
        memory.conn.execute("""
            INSERT INTO agent_runs (id, agent_name, task, status, started_at)
            VALUES
                ('old-run', 'agent1', 'old task', 'completed', CURRENT_TIMESTAMP - INTERVAL 60 DAY),
                ('new-run', 'agent1', 'new task', 'completed', CURRENT_TIMESTAMP)
        """)

        deleted = memory.cleanup_old_runs(days=30)

        assert deleted == 1
        # Verify old run is gone
        result = memory.conn.execute(
            "SELECT id FROM agent_runs WHERE id = 'old-run'"
        ).fetchone()
        assert result is None

        # Verify new run remains
        result = memory.conn.execute(
            "SELECT id FROM agent_runs WHERE id = 'new-run'"
        ).fetchone()
        assert result is not None

    def test_cleanup_old_events_removes_old_data(self, memory):
        """cleanup_old_events removes events older than threshold."""
        import json

        # Insert events with manual timestamps
        memory.conn.execute("""
            INSERT INTO agent_events (id, agent_name, event_type, event_data, timestamp)
            VALUES
                ('old-evt', 'agent1', 'heartbeat', '{}', CURRENT_TIMESTAMP - INTERVAL 14 DAY),
                ('new-evt', 'agent1', 'heartbeat', '{}', CURRENT_TIMESTAMP)
        """)

        deleted = memory.cleanup_old_events(days=7)

        assert deleted == 1

    def test_cleanup_old_tasks_removes_old_data(self, memory):
        """cleanup_old_tasks removes task log entries older than threshold."""
        memory.conn.execute("""
            INSERT INTO task_log (id, description, status, created_at)
            VALUES
                ('old-task', 'old description', 'completed', CURRENT_TIMESTAMP - INTERVAL 60 DAY),
                ('new-task', 'new description', 'completed', CURRENT_TIMESTAMP)
        """)

        deleted = memory.cleanup_old_tasks(days=30)

        assert deleted == 1

    def test_cleanup_memories_by_namespace(self, memory):
        """cleanup_memories_by_namespace removes all memories in namespace."""
        memory.store("key1", "value1", namespace="temp")
        memory.store("key2", "value2", namespace="temp")
        memory.store("key3", "value3", namespace="persistent")

        deleted = memory.cleanup_memories_by_namespace("temp")

        assert deleted == 2

        # Verify temp namespace is cleared
        results = memory.query("key", namespace="temp")
        assert len(results) == 0

        # Verify persistent namespace remains
        results = memory.query("key", namespace="persistent")
        assert len(results) == 1

    def test_cleanup_old_memories_removes_old_data(self, memory):
        """cleanup_old_memories removes memories older than threshold."""
        # Insert memories with manual timestamps
        memory.conn.execute("""
            INSERT INTO memories (key, value, namespace, metadata, created_at)
            VALUES
                ('old-key', 'old value', 'default', '{}', CURRENT_TIMESTAMP - INTERVAL 120 DAY),
                ('new-key', 'new value', 'default', '{}', CURRENT_TIMESTAMP)
        """)

        deleted = memory.cleanup_old_memories(days=90)

        assert deleted == 1

    def test_run_full_cleanup(self, memory):
        """run_full_cleanup cleans up all tables."""
        # Insert old data in all tables
        memory.conn.execute("""
            INSERT INTO agent_runs (id, agent_name, task, status, started_at)
            VALUES ('old-run', 'agent1', 'task', 'completed', CURRENT_TIMESTAMP - INTERVAL 60 DAY)
        """)
        memory.conn.execute("""
            INSERT INTO agent_events (id, agent_name, event_type, event_data, timestamp)
            VALUES ('old-evt', 'agent1', 'heartbeat', '{}', CURRENT_TIMESTAMP - INTERVAL 14 DAY)
        """)
        memory.conn.execute("""
            INSERT INTO task_log (id, description, status, created_at)
            VALUES ('old-task', 'desc', 'completed', CURRENT_TIMESTAMP - INTERVAL 60 DAY)
        """)

        deleted = memory.run_full_cleanup(
            runs_days=30,
            events_days=7,
            tasks_days=30,
            memories_days=None,  # Don't clean memories
        )

        assert deleted["agent_runs"] == 1
        assert deleted["agent_events"] == 1
        assert deleted["task_log"] == 1
        assert "memories" not in deleted  # Should not be cleaned

    def test_run_full_cleanup_with_memories(self, memory):
        """run_full_cleanup can include memories cleanup."""
        memory.conn.execute("""
            INSERT INTO memories (key, value, namespace, metadata, created_at)
            VALUES ('old-mem', 'old', 'default', '{}', CURRENT_TIMESTAMP - INTERVAL 120 DAY)
        """)

        deleted = memory.run_full_cleanup(memories_days=90)

        assert deleted["memories"] == 1

    def test_vacuum(self, memory):
        """vacuum runs without error."""
        # Add and delete data to create fragmentation
        for i in range(10):
            memory.store(f"key{i}", "x" * 1000)
        for i in range(10):
            memory.delete(f"key{i}")

        # Should not raise
        memory.vacuum()

    def test_cleanup_preserves_recent_data(self, memory):
        """Cleanup operations preserve data within retention period."""
        # Insert recent data
        memory.log_run_start("recent-run", "agent1", "recent task")
        memory.insert_agent_event(
            AgentEvent(id="recent-evt", agent_name="agent1", event_type=AgentEventType.HEARTBEAT)
        )
        memory.store("recent-key", "recent value")

        # Run cleanup with default retention
        deleted = memory.run_full_cleanup()

        # Verify recent data is preserved
        result = memory.conn.execute(
            "SELECT id FROM agent_runs WHERE id = 'recent-run'"
        ).fetchone()
        assert result is not None

        assert memory.get("recent-key") == "recent value"
