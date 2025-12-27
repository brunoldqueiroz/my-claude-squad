"""DuckDB-based persistent memory for the orchestrator.

Uses short-lived connections with retry logic to avoid lock conflicts
when multiple processes access the same database file.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator.connection import ConnectionManager
from orchestrator.types import (
    AgentEvent,
    AgentEventType,
    AgentHealth,
    AgentRun,
    AgentStatus,
    Memory,
    Session,
    SessionStatus,
    SessionTask,
    TaskStatus,
)


class SwarmMemory:
    """DuckDB-backed persistent memory for swarm state.

    Uses short-lived connections to avoid lock conflicts. Each operation
    opens a connection, performs the query, and closes it immediately.
    Retry logic handles transient lock errors.
    """

    def __init__(self, db_path: Path | None = None):
        """Initialize the memory store.

        Args:
            db_path: Path to DuckDB database. Defaults to .swarm/memory.duckdb
        """
        if db_path is None:
            swarm_dir = Path(__file__).parent.parent / ".swarm"
            swarm_dir.mkdir(exist_ok=True)
            db_path = swarm_dir / "memory.duckdb"

        self.db_path = db_path
        self._manager = ConnectionManager(db_path)
        self._init_tables()

    def _init_tables(self) -> None:
        """Initialize database tables."""
        with self._manager.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    key VARCHAR PRIMARY KEY,
                    value VARCHAR,
                    namespace VARCHAR DEFAULT 'default',
                    metadata JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id VARCHAR PRIMARY KEY,
                    agent_name VARCHAR NOT NULL,
                    task VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    tokens_used INTEGER DEFAULT 0,
                    result VARCHAR
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_log (
                    id VARCHAR PRIMARY KEY,
                    description VARCHAR NOT NULL,
                    agent_name VARCHAR,
                    status VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    result VARCHAR
                )
            """)

            # Agent health tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_health (
                    agent_name VARCHAR PRIMARY KEY,
                    status VARCHAR NOT NULL,
                    health_score REAL DEFAULT 1.0,
                    last_heartbeat TIMESTAMP,
                    current_task_id VARCHAR,
                    error_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    total_execution_time_ms REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Agent events for debugging and observability
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_events (
                    id VARCHAR PRIMARY KEY,
                    agent_name VARCHAR NOT NULL,
                    event_type VARCHAR NOT NULL,
                    event_data JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sessions for persistent, resumable workflows
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description VARCHAR,
                    status VARCHAR NOT NULL,
                    swarm_id VARCHAR,
                    tasks JSON,
                    current_task_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paused_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata JSON
                )
            """)

        # Create indexes for frequently queried columns
        self._create_indexes()

    def _create_indexes(self) -> None:
        """Create indexes for frequently queried columns.

        Uses CREATE INDEX IF NOT EXISTS to be idempotent.
        Indexes are created for columns used in WHERE, ORDER BY, and JOIN clauses.
        """
        indexes = [
            # memories: namespace is used in WHERE and ORDER BY
            ("idx_memories_namespace", "memories", "namespace"),
            ("idx_memories_created_at", "memories", "created_at"),

            # agent_runs: frequently filtered and sorted by these columns
            ("idx_agent_runs_agent_name", "agent_runs", "agent_name"),
            ("idx_agent_runs_status", "agent_runs", "status"),
            ("idx_agent_runs_started_at", "agent_runs", "started_at DESC"),

            # task_log: filtered and cleaned up by created_at
            ("idx_task_log_agent_name", "task_log", "agent_name"),
            ("idx_task_log_status", "task_log", "status"),
            ("idx_task_log_created_at", "task_log", "created_at"),

            # agent_events: frequently filtered and sorted
            ("idx_agent_events_agent_name", "agent_events", "agent_name"),
            ("idx_agent_events_event_type", "agent_events", "event_type"),
            ("idx_agent_events_timestamp", "agent_events", "timestamp DESC"),

            # sessions: filtered by status, sorted by updated_at
            ("idx_sessions_status", "sessions", "status"),
            ("idx_sessions_updated_at", "sessions", "updated_at DESC"),
            ("idx_sessions_swarm_id", "sessions", "swarm_id"),
        ]

        with self._manager.connection() as conn:
            for index_name, table, column in indexes:
                try:
                    conn.execute(
                        f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})"
                    )
                except Exception:
                    # Index might already exist with different definition
                    pass

    # === Memory Operations ===

    def store(self, key: str, value: str, namespace: str = "default", metadata: dict[str, Any] | None = None) -> None:
        """Store a key-value pair in memory.

        Args:
            key: Unique key
            value: Value to store
            namespace: Optional namespace for organization
            metadata: Optional metadata dict
        """
        import json

        metadata_json = json.dumps(metadata or {})

        with self._manager.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memories (key, value, namespace, metadata, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                [key, value, namespace, metadata_json],
            )

    def get(self, key: str) -> str | None:
        """Get a value by key.

        Args:
            key: Key to look up

        Returns:
            Value if found, None otherwise
        """
        result = self._manager.execute_one(
            "SELECT value FROM memories WHERE key = ?", [key], read_only=True
        )
        return result[0] if result else None

    def query(self, pattern: str, namespace: str | None = None, limit: int = 10) -> list[Memory]:
        """Query memories by pattern.

        Args:
            pattern: SQL LIKE pattern to match keys or values
            namespace: Optional namespace filter
            limit: Maximum results to return

        Returns:
            List of matching Memory objects
        """
        import json

        sql = """
            SELECT key, value, namespace, metadata, created_at
            FROM memories
            WHERE (key LIKE ? OR value LIKE ?)
        """
        params: list[Any] = [f"%{pattern}%", f"%{pattern}%"]

        if namespace:
            sql += " AND namespace = ?"
            params.append(namespace)

        sql += f" ORDER BY created_at DESC LIMIT {limit}"

        results = self._manager.execute(sql, params, read_only=True)

        return [
            Memory(
                key=row[0],
                value=row[1],
                namespace=row[2],
                metadata=json.loads(row[3]) if row[3] else {},
                created_at=row[4],
            )
            for row in results
        ]

    def delete(self, key: str) -> bool:
        """Delete a memory by key.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found
        """
        with self._manager.connection() as conn:
            result = conn.execute(
                "DELETE FROM memories WHERE key = ? RETURNING key", [key]
            ).fetchone()
            return result is not None

    # === Agent Run Operations ===

    def log_run_start(self, run_id: str, agent_name: str, task: str) -> None:
        """Log the start of an agent run.

        Args:
            run_id: Unique run ID
            agent_name: Name of the agent
            task: Task description
        """
        with self._manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO agent_runs (id, agent_name, task, status, started_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                [run_id, agent_name, task, TaskStatus.IN_PROGRESS.value],
            )

    def log_run_complete(self, run_id: str, status: TaskStatus, result: str | None = None, tokens: int = 0) -> None:
        """Log the completion of an agent run.

        Args:
            run_id: Run ID to update
            status: Final status
            result: Optional result text
            tokens: Tokens used
        """
        with self._manager.connection() as conn:
            conn.execute(
                """
                UPDATE agent_runs
                SET status = ?, completed_at = CURRENT_TIMESTAMP, result = ?, tokens_used = ?
                WHERE id = ?
            """,
                [status.value, result, tokens, run_id],
            )

    def get_recent_runs(self, limit: int = 10) -> list[AgentRun]:
        """Get recent agent runs.

        Args:
            limit: Maximum results

        Returns:
            List of recent AgentRun objects
        """
        results = self._manager.execute(
            f"""
            SELECT id, agent_name, task, status, started_at, completed_at, tokens_used, result
            FROM agent_runs
            ORDER BY started_at DESC
            LIMIT {limit}
        """,
            read_only=True,
        )

        return [
            AgentRun(
                id=row[0],
                agent_name=row[1],
                task=row[2],
                status=TaskStatus(row[3]),
                started_at=row[4],
                completed_at=row[5],
                tokens_used=row[6] or 0,
                result=row[7],
            )
            for row in results
        ]

    def get_run_stats(self) -> dict[str, Any]:
        """Get statistics about agent runs.

        Returns:
            Dict with run statistics
        """
        result = self._manager.execute_one(
            """
            SELECT
                COUNT(*) as total_runs,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
                SUM(tokens_used) as total_tokens
            FROM agent_runs
        """,
            read_only=True,
        )

        return {
            "total_runs": result[0] if result else 0,
            "completed": result[1] if result else 0,
            "failed": result[2] if result else 0,
            "in_progress": result[3] if result else 0,
            "total_tokens": (result[4] or 0) if result else 0,
        }

    def close(self) -> None:
        """Close the database connection.

        Note: With short-lived connections, this is now a no-op.
        Kept for backwards compatibility.
        """
        pass  # Connections are now short-lived, no persistent connection to close

    # === Agent Health Operations ===

    def upsert_agent_health(self, health: AgentHealth) -> None:
        """Insert or update agent health record.

        Args:
            health: AgentHealth object to persist
        """
        with self._manager.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_health (
                    agent_name, status, health_score, last_heartbeat,
                    current_task_id, error_count, success_count,
                    total_execution_time_ms, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    health.agent_name,
                    health.status.value,
                    health.health_score,
                    health.last_heartbeat,
                    health.current_task_id,
                    health.error_count,
                    health.success_count,
                    health.total_execution_time_ms,
                    health.created_at,
                    health.updated_at,
                ],
            )

    def get_agent_health(self, agent_name: str) -> AgentHealth | None:
        """Get health record for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            AgentHealth object or None if not found
        """
        result = self._manager.execute_one(
            """
            SELECT agent_name, status, health_score, last_heartbeat,
                   current_task_id, error_count, success_count,
                   total_execution_time_ms, created_at, updated_at
            FROM agent_health
            WHERE agent_name = ?
        """,
            [agent_name],
            read_only=True,
        )

        if result is None:
            return None

        return AgentHealth(
            agent_name=result[0],
            status=AgentStatus(result[1]),
            health_score=result[2],
            last_heartbeat=result[3],
            current_task_id=result[4],
            error_count=result[5],
            success_count=result[6],
            total_execution_time_ms=result[7],
            created_at=result[8],
            updated_at=result[9],
        )

    def get_all_agent_health(self) -> list[AgentHealth]:
        """Get health records for all agents.

        Returns:
            List of AgentHealth objects
        """
        results = self._manager.execute(
            """
            SELECT agent_name, status, health_score, last_heartbeat,
                   current_task_id, error_count, success_count,
                   total_execution_time_ms, created_at, updated_at
            FROM agent_health
            ORDER BY agent_name
        """,
            read_only=True,
        )

        return [
            AgentHealth(
                agent_name=row[0],
                status=AgentStatus(row[1]),
                health_score=row[2],
                last_heartbeat=row[3],
                current_task_id=row[4],
                error_count=row[5],
                success_count=row[6],
                total_execution_time_ms=row[7],
                created_at=row[8],
                updated_at=row[9],
            )
            for row in results
        ]

    def insert_agent_event(self, event: AgentEvent) -> None:
        """Insert an agent event.

        Args:
            event: AgentEvent object to persist
        """
        import json

        with self._manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO agent_events (id, agent_name, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                [
                    event.id,
                    event.agent_name,
                    event.event_type.value,
                    json.dumps(event.event_data),
                    event.timestamp,
                ],
            )

    def get_agent_events(
        self,
        agent_name: str | None = None,
        event_type: AgentEventType | None = None,
        limit: int = 50,
    ) -> list[AgentEvent]:
        """Get agent events with optional filters.

        Args:
            agent_name: Filter by agent name
            event_type: Filter by event type
            limit: Maximum results to return

        Returns:
            List of AgentEvent objects
        """
        import json

        sql = "SELECT id, agent_name, event_type, event_data, timestamp FROM agent_events WHERE 1=1"
        params: list[Any] = []

        if agent_name is not None:
            sql += " AND agent_name = ?"
            params.append(agent_name)

        if event_type is not None:
            sql += " AND event_type = ?"
            params.append(event_type.value)

        sql += f" ORDER BY timestamp DESC LIMIT {limit}"

        results = self._manager.execute(sql, params, read_only=True)

        return [
            AgentEvent(
                id=row[0],
                agent_name=row[1],
                event_type=AgentEventType(row[2]),
                event_data=json.loads(row[3]) if row[3] else {},
                timestamp=row[4],
            )
            for row in results
        ]

    # === Session Operations ===

    def save_session(self, session: Session) -> None:
        """Save or update a session.

        Args:
            session: Session object to persist
        """
        import json

        tasks_json = json.dumps([t.model_dump() for t in session.tasks], default=str)
        metadata_json = json.dumps(session.metadata)

        # Use INSERT ON CONFLICT instead of INSERT OR REPLACE to avoid
        # DuckDB bug where indexes on updated columns prevent updates
        with self._manager.connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, name, description, status, swarm_id, tasks,
                    current_task_index, created_at, updated_at, paused_at,
                    completed_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    swarm_id = EXCLUDED.swarm_id,
                    tasks = EXCLUDED.tasks,
                    current_task_index = EXCLUDED.current_task_index,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at,
                    paused_at = EXCLUDED.paused_at,
                    completed_at = EXCLUDED.completed_at,
                    metadata = EXCLUDED.metadata
            """,
                [
                    session.id,
                    session.name,
                    session.description,
                    session.status.value,
                    session.swarm_id,
                    tasks_json,
                    session.current_task_index,
                    session.created_at,
                    session.updated_at,
                    session.paused_at,
                    session.completed_at,
                    metadata_json,
                ],
            )

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session object or None if not found
        """
        import json

        result = self._manager.execute_one(
            """
            SELECT id, name, description, status, swarm_id, tasks,
                   current_task_index, created_at, updated_at, paused_at,
                   completed_at, metadata
            FROM sessions
            WHERE id = ?
        """,
            [session_id],
            read_only=True,
        )

        if result is None:
            return None

        tasks_data = json.loads(result[5]) if result[5] else []
        tasks = [SessionTask(**t) for t in tasks_data]
        metadata = json.loads(result[11]) if result[11] else {}

        return Session(
            id=result[0],
            name=result[1],
            description=result[2],
            status=SessionStatus(result[3]),
            swarm_id=result[4],
            tasks=tasks,
            current_task_index=result[6],
            created_at=result[7],
            updated_at=result[8],
            paused_at=result[9],
            completed_at=result[10],
            metadata=metadata,
        )

    def list_sessions(
        self,
        status: SessionStatus | None = None,
        limit: int = 50,
    ) -> list[Session]:
        """List sessions with optional status filter.

        Args:
            status: Optional status to filter by
            limit: Maximum results to return

        Returns:
            List of Session objects
        """
        import json

        sql = """
            SELECT id, name, description, status, swarm_id, tasks,
                   current_task_index, created_at, updated_at, paused_at,
                   completed_at, metadata
            FROM sessions
        """
        params: list[Any] = []

        if status is not None:
            sql += " WHERE status = ?"
            params.append(status.value)

        sql += f" ORDER BY updated_at DESC LIMIT {limit}"

        results = self._manager.execute(sql, params, read_only=True)

        sessions = []
        for row in results:
            tasks_data = json.loads(row[5]) if row[5] else []
            tasks = [SessionTask(**t) for t in tasks_data]
            metadata = json.loads(row[11]) if row[11] else {}

            sessions.append(
                Session(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    status=SessionStatus(row[3]),
                    swarm_id=row[4],
                    tasks=tasks,
                    current_task_index=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                    paused_at=row[9],
                    completed_at=row[10],
                    metadata=metadata,
                )
            )

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        with self._manager.connection() as conn:
            result = conn.execute(
                "DELETE FROM sessions WHERE id = ? RETURNING id",
                [session_id],
            ).fetchone()
            return result is not None

    def get_active_sessions(self) -> list[Session]:
        """Get all active or paused sessions (resumable).

        Returns:
            List of active/paused Session objects
        """
        import json

        results = self._manager.execute(
            """
            SELECT id, name, description, status, swarm_id, tasks,
                   current_task_index, created_at, updated_at, paused_at,
                   completed_at, metadata
            FROM sessions
            WHERE status IN ('active', 'paused')
            ORDER BY updated_at DESC
        """,
            read_only=True,
        )

        sessions = []
        for row in results:
            tasks_data = json.loads(row[5]) if row[5] else []
            tasks = [SessionTask(**t) for t in tasks_data]
            metadata = json.loads(row[11]) if row[11] else {}

            sessions.append(
                Session(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    status=SessionStatus(row[3]),
                    swarm_id=row[4],
                    tasks=tasks,
                    current_task_index=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                    paused_at=row[9],
                    completed_at=row[10],
                    metadata=metadata,
                )
            )

        return sessions

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Delete completed/failed/cancelled sessions older than specified days.

        Args:
            days: Delete sessions older than this many days

        Returns:
            Number of rows deleted
        """
        with self._manager.connection() as conn:
            result = conn.execute(
                f"""
                DELETE FROM sessions
                WHERE status IN ('completed', 'failed', 'cancelled')
                AND updated_at < CURRENT_TIMESTAMP - INTERVAL {int(days)} DAY
                RETURNING id
                """
            ).fetchall()
            return len(result)

    # === Retention and Cleanup Operations ===

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics for all tables.

        Returns:
            Dict with row counts and estimated sizes
        """
        stats = {}

        with self._manager.connection(read_only=True) as conn:
            # Get row counts for each table
            tables = ["memories", "agent_runs", "task_log", "agent_health", "agent_events"]
            for table in tables:
                result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                stats[f"{table}_count"] = result[0] if result else 0

            # Get oldest and newest timestamps for time-series tables
            for table in ["agent_runs", "agent_events"]:
                time_col = "started_at" if table == "agent_runs" else "timestamp"
                result = conn.execute(
                    f"SELECT MIN({time_col}), MAX({time_col}) FROM {table}"
                ).fetchone()
                if result and result[0]:
                    stats[f"{table}_oldest"] = result[0].isoformat() if hasattr(result[0], "isoformat") else str(result[0])
                    stats[f"{table}_newest"] = result[1].isoformat() if hasattr(result[1], "isoformat") else str(result[1])

        # Get database file size
        if self.db_path.exists():
            stats["db_size_bytes"] = self.db_path.stat().st_size
            stats["db_size_mb"] = round(self.db_path.stat().st_size / (1024 * 1024), 2)

        return stats

    def cleanup_old_runs(self, days: int = 30) -> int:
        """Delete agent runs older than specified days.

        Args:
            days: Delete runs older than this many days

        Returns:
            Number of rows deleted
        """
        # DuckDB doesn't support parameter binding in INTERVAL, so use string formatting
        # This is safe since days is validated as int
        with self._manager.connection() as conn:
            result = conn.execute(
                f"""
                DELETE FROM agent_runs
                WHERE started_at < CURRENT_TIMESTAMP - INTERVAL {int(days)} DAY
                RETURNING id
                """
            ).fetchall()
            return len(result)

    def cleanup_old_events(self, days: int = 7) -> int:
        """Delete agent events older than specified days.

        Args:
            days: Delete events older than this many days

        Returns:
            Number of rows deleted
        """
        # DuckDB doesn't support parameter binding in INTERVAL, so use string formatting
        with self._manager.connection() as conn:
            result = conn.execute(
                f"""
                DELETE FROM agent_events
                WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL {int(days)} DAY
                RETURNING id
                """
            ).fetchall()
            return len(result)

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """Delete task log entries older than specified days.

        Args:
            days: Delete tasks older than this many days

        Returns:
            Number of rows deleted
        """
        # DuckDB doesn't support parameter binding in INTERVAL, so use string formatting
        with self._manager.connection() as conn:
            result = conn.execute(
                f"""
                DELETE FROM task_log
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL {int(days)} DAY
                RETURNING id
                """
            ).fetchall()
            return len(result)

    def cleanup_memories_by_namespace(self, namespace: str) -> int:
        """Delete all memories in a specific namespace.

        Args:
            namespace: Namespace to clear

        Returns:
            Number of rows deleted
        """
        with self._manager.connection() as conn:
            result = conn.execute(
                "DELETE FROM memories WHERE namespace = ? RETURNING key",
                [namespace],
            ).fetchall()
            return len(result)

    def cleanup_old_memories(self, days: int = 90) -> int:
        """Delete memories older than specified days.

        Args:
            days: Delete memories older than this many days

        Returns:
            Number of rows deleted
        """
        # DuckDB doesn't support parameter binding in INTERVAL, so use string formatting
        with self._manager.connection() as conn:
            result = conn.execute(
                f"""
                DELETE FROM memories
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL {int(days)} DAY
                RETURNING key
                """
            ).fetchall()
            return len(result)

    def run_full_cleanup(
        self,
        runs_days: int = 30,
        events_days: int = 7,
        tasks_days: int = 30,
        memories_days: int | None = None,
    ) -> dict[str, int]:
        """Run full cleanup with configurable retention periods.

        Args:
            runs_days: Delete runs older than this (default 30)
            events_days: Delete events older than this (default 7)
            tasks_days: Delete tasks older than this (default 30)
            memories_days: Delete memories older than this (None = keep all)

        Returns:
            Dict with counts of deleted rows per table
        """
        deleted = {
            "agent_runs": self.cleanup_old_runs(runs_days),
            "agent_events": self.cleanup_old_events(events_days),
            "task_log": self.cleanup_old_tasks(tasks_days),
        }

        if memories_days is not None:
            deleted["memories"] = self.cleanup_old_memories(memories_days)

        # Vacuum to reclaim space
        self.vacuum()

        return deleted

    def vacuum(self) -> None:
        """Reclaim disk space by vacuuming the database."""
        with self._manager.connection() as conn:
            conn.execute("VACUUM")
