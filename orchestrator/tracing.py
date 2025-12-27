"""Langfuse tracing integration for my-claude-squad.

This module provides proper Langfuse client initialization and tracing utilities.
The key fix: we must instantiate Langfuse() before using get_client() or @observe.
"""

import atexit
import logging
import os
import signal
import sys
from typing import Any

from langfuse import Langfuse, get_client, observe

logger = logging.getLogger(__name__)

# Module-level client instance
_langfuse: Langfuse | None = None
_initialized: bool = False

# Re-export the observe decorator
__all__ = [
    "observe",
    "get_langfuse",
    "is_enabled",
    "init",
    "score_task",
    "update_trace",
    "update_span",
    "flush",
    "shutdown",
]


def is_enabled() -> bool:
    """Check if Langfuse is configured via environment variables."""
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY")) and bool(os.getenv("LANGFUSE_SECRET_KEY"))


def get_langfuse() -> Langfuse | None:
    """Get the initialized Langfuse client.

    Returns:
        The Langfuse client if initialized and enabled, None otherwise.
    """
    global _langfuse
    if _langfuse is None and _initialized:
        # Try get_client() as fallback (in case @observe created one)
        try:
            _langfuse = get_client()
        except Exception:
            pass
    return _langfuse


def init() -> bool:
    """Initialize Langfuse tracing.

    This MUST be called before using @observe or get_client().
    It creates the Langfuse client instance that enables all tracing.

    Returns:
        True if Langfuse is successfully initialized, False otherwise.
    """
    global _langfuse, _initialized

    if _initialized:
        return _langfuse is not None

    _initialized = True

    if not is_enabled():
        logger.warning(
            "Langfuse tracing disabled - missing LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY"
        )
        return False

    try:
        # Create the Langfuse client - this is the critical step!
        # Without this, get_client() and @observe won't work.
        _langfuse = Langfuse(
            debug=os.getenv("LANGFUSE_DEBUG", "").lower() == "true",
        )

        # Verify connectivity by checking auth
        # This will raise an exception if credentials are invalid
        _langfuse.auth_check()

        logger.info("Langfuse tracing enabled and connected successfully")

        # Register cleanup handlers
        _register_cleanup_handlers()

        return True

    except Exception as e:
        logger.error(f"Langfuse initialization failed: {e}")
        _langfuse = None
        return False


def _register_cleanup_handlers() -> None:
    """Register signal and atexit handlers for graceful shutdown."""

    def signal_handler(signum: int, frame: Any) -> None:
        """Handle termination signals by flushing Langfuse."""
        logger.debug(f"Received signal {signum}, flushing Langfuse...")
        flush()
        sys.exit(0)

    # Register atexit handler for normal shutdown
    atexit.register(flush)

    # Register signal handlers for SIGTERM and SIGINT
    # This ensures traces are flushed even on Ctrl+C or kill
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    except (ValueError, OSError) as e:
        # Signal handlers can fail in some environments (e.g., threads)
        logger.debug(f"Could not register signal handlers: {e}")


def score_task(name: str, value: float, comment: str | None = None) -> None:
    """Score the current trace/span.

    Args:
        name: Name of the score metric
        value: Numeric score value
        comment: Optional comment explaining the score
    """
    client = get_langfuse()
    if client is None:
        return

    try:
        client.score_current_trace(name=name, value=value, comment=comment)
    except Exception as e:
        logger.debug(f"Failed to score task: {e}")


def update_trace(
    user_id: str | None = None,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> None:
    """Update the current trace with additional context.

    Args:
        user_id: User identifier for the trace
        session_id: Session identifier for grouping traces
        metadata: Additional metadata dictionary
        tags: List of tags for filtering
    """
    client = get_langfuse()
    if client is None:
        return

    try:
        client.update_current_trace(
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            tags=tags,
        )
    except Exception as e:
        logger.debug(f"Failed to update trace: {e}")


def update_span(
    metadata: dict[str, Any] | None = None,
    output: Any | None = None,
    level: str | None = None,
    status_message: str | None = None,
) -> None:
    """Update the current span with additional context.

    Args:
        metadata: Additional metadata dictionary
        output: Output value for the span
        level: Log level (e.g., "ERROR", "WARNING")
        status_message: Status message for the span
    """
    client = get_langfuse()
    if client is None:
        return

    try:
        kwargs: dict[str, Any] = {}
        if metadata is not None:
            kwargs["metadata"] = metadata
        if output is not None:
            kwargs["output"] = output
        if level is not None:
            kwargs["level"] = level
        if status_message is not None:
            kwargs["status_message"] = status_message

        client.update_current_span(**kwargs)
    except Exception as e:
        logger.debug(f"Failed to update span: {e}")


def flush() -> None:
    """Flush any pending Langfuse events.

    Always call this on shutdown to ensure all traces are sent.
    This is a blocking call that waits for all events to be sent.
    """
    client = get_langfuse()
    if client is None:
        return

    try:
        client.flush()
        logger.debug("Langfuse events flushed successfully")
    except Exception as e:
        logger.warning(f"Failed to flush Langfuse events: {e}")


def shutdown() -> None:
    """Shutdown Langfuse tracing gracefully.

    Flushes all pending events and resets the client.
    """
    global _langfuse, _initialized

    flush()
    _langfuse = None
    _initialized = False
    logger.debug("Langfuse tracing shut down")
