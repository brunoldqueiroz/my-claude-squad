"""Tests for orchestrator/events.py - EventBus."""

import asyncio

import pytest

from orchestrator.events import EventBus, create_event, get_event_bus
from orchestrator.types import AgentEvent, AgentEventType


class TestEventBusRegistration:
    """Tests for handler registration."""

    def test_on_registers_handler(self, event_bus):
        """on() adds handler to the handlers dict."""
        handler = lambda e: None
        event_bus.on(AgentEventType.HEARTBEAT, handler)

        assert handler in event_bus._handlers[AgentEventType.HEARTBEAT]

    def test_on_returns_unsubscribe(self, event_bus):
        """on() returns a function that unsubscribes."""
        handler = lambda e: None
        unsubscribe = event_bus.on(AgentEventType.HEARTBEAT, handler)

        assert handler in event_bus._handlers[AgentEventType.HEARTBEAT]

        unsubscribe()

        assert handler not in event_bus._handlers[AgentEventType.HEARTBEAT]

    def test_on_all_registers_global_handler(self, event_bus):
        """on_all() adds handler to global handlers."""
        handler = lambda e: None
        event_bus.on_all(handler)

        assert handler in event_bus._global_handlers

    def test_off_removes_handler(self, event_bus):
        """off() removes a specific handler."""
        handler = lambda e: None
        event_bus.on(AgentEventType.HEARTBEAT, handler)

        result = event_bus.off(AgentEventType.HEARTBEAT, handler)

        assert result is True
        assert handler not in event_bus._handlers[AgentEventType.HEARTBEAT]

    def test_off_nonexistent_returns_false(self, event_bus):
        """off() returns False for non-registered handler."""
        handler = lambda e: None
        result = event_bus.off(AgentEventType.HEARTBEAT, handler)
        assert result is False


class TestEventBusEmit:
    """Tests for event emission."""

    def test_emit_calls_handlers(self, event_bus):
        """emit() calls registered handlers."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.on(AgentEventType.TASK_START, handler)

        event = create_event("test-agent", AgentEventType.TASK_START)
        asyncio.get_event_loop().run_until_complete(event_bus.emit(event))

        assert len(received) == 1
        assert received[0] is event

    def test_emit_calls_global_handlers(self, event_bus):
        """emit() also calls global handlers."""
        received = []

        def global_handler(event):
            received.append(event)

        event_bus.on_all(global_handler)

        event = create_event("test-agent", AgentEventType.TASK_START)
        asyncio.get_event_loop().run_until_complete(event_bus.emit(event))

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_emit_handles_async_handlers(self, event_bus):
        """emit() awaits async handlers."""
        received = []

        async def async_handler(event):
            await asyncio.sleep(0.01)
            received.append(event)

        event_bus.on(AgentEventType.TASK_COMPLETE, async_handler)

        event = create_event("test-agent", AgentEventType.TASK_COMPLETE)
        await event_bus.emit(event)

        assert len(received) == 1

    def test_emit_counts_handler_errors(self, event_bus):
        """emit() increments error count on handler failure."""

        def bad_handler(event):
            raise ValueError("Handler error")

        event_bus.on(AgentEventType.ERROR, bad_handler)

        event = create_event("test-agent", AgentEventType.ERROR)
        asyncio.get_event_loop().run_until_complete(event_bus.emit(event))

        assert event_bus._handler_errors == 1

    def test_emit_continues_after_handler_error(self, event_bus):
        """emit() continues calling other handlers after error."""
        received = []

        def bad_handler(event):
            raise ValueError("Handler error")

        def good_handler(event):
            received.append(event)

        event_bus.on(AgentEventType.ERROR, bad_handler)
        event_bus.on(AgentEventType.ERROR, good_handler)

        event = create_event("test-agent", AgentEventType.ERROR)
        asyncio.get_event_loop().run_until_complete(event_bus.emit(event))

        assert len(received) == 1


class TestEventBusEmitSync:
    """Tests for synchronous emission."""

    def test_emit_sync_calls_sync_handlers(self, event_bus):
        """emit_sync() calls sync handlers."""
        received = []

        def handler(event):
            received.append(event)

        event_bus.on(AgentEventType.HEARTBEAT, handler)

        event = create_event("test-agent", AgentEventType.HEARTBEAT)
        count = event_bus.emit_sync(event)

        assert len(received) == 1
        assert count == 1

    def test_emit_sync_skips_async_handlers(self, event_bus):
        """emit_sync() skips async handlers with warning."""
        received = []

        async def async_handler(event):
            received.append(event)

        event_bus.on(AgentEventType.HEARTBEAT, async_handler)

        event = create_event("test-agent", AgentEventType.HEARTBEAT)
        count = event_bus.emit_sync(event)

        assert len(received) == 0
        assert count == 0


class TestEventBusHistory:
    """Tests for event history."""

    def test_emit_adds_to_history(self, event_bus):
        """emit() adds events to history."""
        event = create_event("test-agent", AgentEventType.HEARTBEAT)
        asyncio.get_event_loop().run_until_complete(event_bus.emit(event))

        assert len(event_bus._history) == 1
        assert event_bus._history[0] is event

    def test_history_limited_to_max(self, event_bus):
        """History is trimmed when exceeding max_history."""
        event_bus._max_history = 5

        for i in range(10):
            event = create_event("agent", AgentEventType.HEARTBEAT, {"i": i})
            asyncio.get_event_loop().run_until_complete(event_bus.emit(event))

        assert len(event_bus._history) == 5
        # Should have most recent events
        assert event_bus._history[-1].event_data["i"] == 9

    def test_get_history_returns_newest_first(self, event_bus):
        """get_history() returns events newest first."""
        for i in range(5):
            event = create_event("agent", AgentEventType.HEARTBEAT, {"i": i})
            event_bus.emit_sync(event)

        history = event_bus.get_history()

        assert history[0].event_data["i"] == 4
        assert history[-1].event_data["i"] == 0

    def test_get_history_filters_by_type(self, event_bus):
        """get_history() filters by event_type."""
        event_bus.emit_sync(create_event("a", AgentEventType.HEARTBEAT))
        event_bus.emit_sync(create_event("a", AgentEventType.ERROR))
        event_bus.emit_sync(create_event("a", AgentEventType.HEARTBEAT))

        history = event_bus.get_history(event_type=AgentEventType.HEARTBEAT)

        assert len(history) == 2
        assert all(e.event_type == AgentEventType.HEARTBEAT for e in history)

    def test_get_history_filters_by_agent(self, event_bus):
        """get_history() filters by agent_name."""
        event_bus.emit_sync(create_event("agent1", AgentEventType.HEARTBEAT))
        event_bus.emit_sync(create_event("agent2", AgentEventType.HEARTBEAT))
        event_bus.emit_sync(create_event("agent1", AgentEventType.HEARTBEAT))

        history = event_bus.get_history(agent_name="agent1")

        assert len(history) == 2
        assert all(e.agent_name == "agent1" for e in history)

    def test_get_history_respects_limit(self, event_bus):
        """get_history() respects limit parameter."""
        for i in range(10):
            event_bus.emit_sync(create_event("agent", AgentEventType.HEARTBEAT))

        history = event_bus.get_history(limit=3)

        assert len(history) == 3

    def test_clear_history_returns_count(self, event_bus):
        """clear_history() returns number of cleared events."""
        for i in range(5):
            event_bus.emit_sync(create_event("agent", AgentEventType.HEARTBEAT))

        count = event_bus.clear_history()

        assert count == 5
        assert len(event_bus._history) == 0


class TestEventBusStats:
    """Tests for event statistics."""

    def test_get_stats(self, event_bus):
        """get_stats() returns complete statistics."""
        event_bus.on(AgentEventType.HEARTBEAT, lambda e: None)
        event_bus.on(AgentEventType.ERROR, lambda e: None)

        event_bus.emit_sync(create_event("a", AgentEventType.HEARTBEAT))
        event_bus.emit_sync(create_event("a", AgentEventType.HEARTBEAT))

        stats = event_bus.get_stats()

        assert stats["total_emits"] == 2
        assert stats["handler_errors"] == 0
        assert stats["history_size"] == 2
        assert "heartbeat" in stats["handlers_by_type"]
        assert "error" in stats["handlers_by_type"]


class TestEventBusClear:
    """Tests for clearing handlers."""

    def test_clear_handlers_removes_all(self, event_bus):
        """clear_handlers() removes all handlers."""
        event_bus.on(AgentEventType.HEARTBEAT, lambda e: None)
        event_bus.on(AgentEventType.ERROR, lambda e: None)
        event_bus.on_all(lambda e: None)

        event_bus.clear_handlers()

        assert len(event_bus._handlers) == 0
        assert len(event_bus._global_handlers) == 0


class TestCreateEventHelper:
    """Tests for create_event helper function."""

    def test_create_event_generates_id(self):
        """create_event() generates a UUID id."""
        event = create_event("agent", AgentEventType.HEARTBEAT)
        assert event.id is not None
        assert len(event.id) == 36  # UUID format

    def test_create_event_sets_timestamp(self):
        """create_event() sets timestamp to now."""
        event = create_event("agent", AgentEventType.HEARTBEAT)
        assert event.timestamp is not None

    def test_create_event_with_data(self):
        """create_event() includes event_data."""
        event = create_event("agent", AgentEventType.TASK_START, {"task_id": "t1"})
        assert event.event_data["task_id"] == "t1"


class TestEventBusSingleton:
    """Tests for singleton behavior."""

    def test_get_event_bus_returns_same_instance(self):
        """get_event_bus() returns the same instance."""
        # Reset singleton
        import orchestrator.events

        orchestrator.events._event_bus = None

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2
