"""DuckDB connection management with locking resilience.

This module provides a connection manager that:
1. Uses short-lived connections (open, operate, close)
2. Implements retry logic with exponential backoff for lock conflicts
3. Supports read-only mode for concurrent reads
4. Provides a context manager for automatic cleanup
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import duckdb

logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 0.1  # 100ms
DEFAULT_MAX_DELAY = 2.0  # 2 seconds


class ConnectionManager:
    """Manages DuckDB connections with locking resilience.

    Instead of holding a persistent connection, this manager creates
    short-lived connections per operation and handles lock conflicts
    with retry logic.

    Example:
        manager = ConnectionManager(db_path)

        # Context manager for automatic cleanup
        with manager.connection() as conn:
            result = conn.execute("SELECT * FROM memories").fetchall()

        # Read-only mode for concurrent reads
        with manager.connection(read_only=True) as conn:
            result = conn.execute("SELECT * FROM memories").fetchall()
    """

    def __init__(
        self,
        db_path: Path,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
    ):
        """Initialize the connection manager.

        Args:
            db_path: Path to DuckDB database file
            max_retries: Maximum number of retry attempts for lock conflicts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
        """
        self.db_path = db_path
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(
        self,
        read_only: bool = False,
    ) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Get a database connection with automatic cleanup.

        Uses retry logic with exponential backoff for lock conflicts.

        Args:
            read_only: If True, open in read-only mode (allows concurrent reads)

        Yields:
            DuckDB connection object

        Raises:
            duckdb.IOException: If connection fails after all retries
        """
        conn = None
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                conn = duckdb.connect(
                    str(self.db_path),
                    read_only=read_only,
                )
                break  # Success

            except duckdb.IOException as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if this is a lock conflict
                if "lock" in error_msg or "conflicting" in error_msg:
                    if attempt < self.max_retries:
                        delay = min(
                            self.base_delay * (2 ** attempt),
                            self.max_delay,
                        )
                        logger.warning(
                            f"Lock conflict (attempt {attempt + 1}/{self.max_retries + 1}), "
                            f"retrying in {delay:.2f}s: {e}"
                        )
                        time.sleep(delay)
                        continue

                # Not a lock error or exhausted retries
                raise

        if conn is None:
            raise last_error or duckdb.IOException("Failed to connect to database")

        try:
            yield conn
        finally:
            conn.close()

    def execute(
        self,
        sql: str,
        params: list[Any] | None = None,
        read_only: bool = False,
    ) -> list[tuple]:
        """Execute a SQL query and return results.

        Convenience method that handles connection lifecycle.

        Args:
            sql: SQL query to execute
            params: Query parameters
            read_only: If True, use read-only mode

        Returns:
            List of result tuples
        """
        with self.connection(read_only=read_only) as conn:
            if params:
                return conn.execute(sql, params).fetchall()
            return conn.execute(sql).fetchall()

    def execute_one(
        self,
        sql: str,
        params: list[Any] | None = None,
        read_only: bool = False,
    ) -> tuple | None:
        """Execute a SQL query and return first result.

        Args:
            sql: SQL query to execute
            params: Query parameters
            read_only: If True, use read-only mode

        Returns:
            First result tuple or None
        """
        with self.connection(read_only=read_only) as conn:
            if params:
                return conn.execute(sql, params).fetchone()
            return conn.execute(sql).fetchone()

    def execute_write(
        self,
        sql: str,
        params: list[Any] | None = None,
    ) -> int:
        """Execute a write query and return affected row count.

        Args:
            sql: SQL query to execute
            params: Query parameters

        Returns:
            Number of affected rows (if RETURNING clause used)
        """
        with self.connection(read_only=False) as conn:
            if params:
                result = conn.execute(sql, params).fetchall()
            else:
                result = conn.execute(sql).fetchall()
            return len(result)


# Default database path
def get_default_db_path() -> Path:
    """Get the default database path."""
    swarm_dir = Path(__file__).parent.parent / ".swarm"
    swarm_dir.mkdir(exist_ok=True)
    return swarm_dir / "memory.duckdb"


# Singleton connection manager
_connection_manager: ConnectionManager | None = None


def get_connection_manager(db_path: Path | None = None) -> ConnectionManager:
    """Get or create the singleton ConnectionManager instance.

    Args:
        db_path: Path to database. Uses default if not specified.

    Returns:
        The ConnectionManager instance
    """
    global _connection_manager

    if _connection_manager is None:
        path = db_path or get_default_db_path()
        _connection_manager = ConnectionManager(path)

    return _connection_manager
