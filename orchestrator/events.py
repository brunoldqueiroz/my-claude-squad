"""Event-driven architecture for the orchestrator.

Provides an EventBus for pub/sub event handling across the system.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Awaitable

from orchestrator.types import AgentEvent, AgentEventType

logger = logging.getLogger(__name__)

# Type aliases for event handlers
SyncHandler = Callable[[AgentEvent], None]
AsyncHandler = Callable[[AgentEvent], Awaitable[None]]
EventHandler = SyncHandler | AsyncHandler


class EventBus:
    """Publish-subscribe event bus for orchestrator events.

    Supports both sync and async handlers. Events are emitted to all
    registered handlers for the event type.

    Example:
        bus = EventBus()

        # Register handler
        def on_task_complete(event: AgentEvent):
            print(f"Task completed: {event.event_data}")

        bus.on(AgentEventType.TASK_COMPLETE, on_task_complete)

        # Emit event
        event = AgentEvent(
            id=str(uuid.uuid4()),
            agent_name="python-developer",
            event_type=AgentEventType.TASK_COMPLETE,
            event_data={"task_id": "123", "result": "success"}
        )
        await bus.emit(event)
    """

    def __init__(self):
        """Initialize the event bus."""
        # Handlers per event type
        self._handlers: dict[AgentEventType, list[EventHandler]] = defaultdict(list)

        # All-events handlers (receive every event)
        self._global_handlers: list[EventHandler] = []

        # Event history for replay/debugging
        self._history: list[AgentEvent] = []
        self._max_history: int = 1000

        # Statistics
        self._emit_count: int = 0
        self._handler_errors: int = 0

    def on(self, event_type: AgentEventType, handler: EventHandler) -> Callable[[], None]:
        """Register a handler for an event type.

        Args:
            event_type: Type of event to handle
            handler: Sync or async function to call when event occurs

        Returns:
            Unsubscribe function that removes the handler
        """
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type.value}")

        def unsubscribe():
            self.off(event_type, handler)

        return unsubscribe

    def on_all(self, handler: EventHandler) -> Callable[[], None]:
        """Register a handler for all event types.

        Args:
            handler: Sync or async function to call for every event

        Returns:
            Unsubscribe function that removes the handler
        """
        self._global_handlers.append(handler)
        logger.debug("Registered global handler for all events")

        def unsubscribe():
            self._global_handlers.remove(handler)

        return unsubscribe

    def off(self, event_type: AgentEventType, handler: EventHandler) -> bool:
        """Remove a handler for an event type.

        Args:
            event_type: Type of event
            handler: Handler to remove

        Returns:
            True if handler was removed, False if not found
        """
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.debug(f"Removed handler for {event_type.value}")
            return True
        return False

    async def emit(self, event: AgentEvent) -> int:
        """Emit an event to all registered handlers.

        Handlers are called concurrently. Errors in handlers are logged
        but don't prevent other handlers from running.

        Args:
            event: Event to emit

        Returns:
            Number of handlers that were called
        """
        self._emit_count += 1

        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Collect all handlers
        handlers = list(self._handlers.get(event.event_type, []))
        handlers.extend(self._global_handlers)

        if not handlers:
            logger.debug(f"No handlers for event {event.event_type.value}")
            return 0

        # Execute handlers
        handler_count = 0
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
                handler_count += 1
            except Exception as e:
                self._handler_errors += 1
                logger.error(
                    f"Error in event handler for {event.event_type.value}: {e}",
                    exc_info=True,
                )

        logger.debug(
            f"Emitted {event.event_type.value} to {handler_count} handlers"
        )
        return handler_count

    def emit_sync(self, event: AgentEvent) -> int:
        """Emit an event synchronously (for sync-only handlers).

        Only calls synchronous handlers. Async handlers are skipped with a warning.

        Args:
            event: Event to emit

        Returns:
            Number of handlers that were called
        """
        self._emit_count += 1

        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Collect all handlers
        handlers = list(self._handlers.get(event.event_type, []))
        handlers.extend(self._global_handlers)

        if not handlers:
            return 0

        handler_count = 0
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    logger.warning(
                        f"Skipping async handler in sync emit for {event.event_type.value}"
                    )
                    # Close the coroutine to avoid warning
                    result.close()
                    continue
                handler_count += 1
            except Exception as e:
                self._handler_errors += 1
                logger.error(
                    f"Error in event handler for {event.event_type.value}: {e}",
                    exc_info=True,
                )

        return handler_count

    def get_history(
        self,
        event_type: AgentEventType | None = None,
        agent_name: str | None = None,
        limit: int = 50,
    ) -> list[AgentEvent]:
        """Get recent events from history.

        Args:
            event_type: Filter by event type
            agent_name: Filter by agent name
            limit: Maximum events to return

        Returns:
            List of matching events (newest first)
        """
        events = self._history[::-1]  # Reverse for newest first

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        if agent_name is not None:
            events = [e for e in events if e.agent_name == agent_name]

        return events[:limit]

    def clear_history(self) -> int:
        """Clear the event history.

        Returns:
            Number of events cleared
        """
        count = len(self._history)
        self._history.clear()
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics.

        Returns:
            Dictionary with emit counts, handler counts, errors
        """
        handler_counts = {
            event_type.value: len(handlers)
            for event_type, handlers in self._handlers.items()
            if handlers
        }

        return {
            "total_emits": self._emit_count,
            "handler_errors": self._handler_errors,
            "history_size": len(self._history),
            "max_history": self._max_history,
            "global_handlers": len(self._global_handlers),
            "handlers_by_type": handler_counts,
        }

    def clear_handlers(self) -> None:
        """Remove all registered handlers."""
        self._handlers.clear()
        self._global_handlers.clear()
        logger.info("Cleared all event handlers")


def create_event(
    agent_name: str,
    event_type: AgentEventType,
    event_data: dict[str, Any] | None = None,
) -> AgentEvent:
    """Helper to create an AgentEvent with auto-generated ID and timestamp.

    Args:
        agent_name: Name of the agent
        event_type: Type of event
        event_data: Optional event payload

    Returns:
        AgentEvent instance
    """
    return AgentEvent(
        id=str(uuid.uuid4()),
        agent_name=agent_name,
        event_type=event_type,
        event_data=event_data or {},
        timestamp=datetime.now(),
    )


# Singleton event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get or create the singleton EventBus instance.

    Returns:
        The global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
