"""Tests for the hooks system."""

import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

import pytest

from orchestrator.hooks import (
    HooksManager,
    HookType,
    HookContext,
    HookResult,
    HookAbortError,
    RegisteredHook,
    get_hooks_manager,
    hook,
)


class TestHooksManager:
    """Tests for HooksManager class."""

    def test_register_hook(self):
        """Test hook registration."""
        manager = HooksManager()

        def my_hook(ctx: HookContext) -> None:
            pass

        registered = manager.register(
            name="test-hook",
            hook_type=HookType.PRE_TASK,
            handler=my_hook,
            priority=50,
        )

        assert registered.name == "test-hook"
        assert registered.hook_type == HookType.PRE_TASK
        assert registered.priority == 50
        assert registered.enabled is True

    def test_register_duplicate_name_raises(self):
        """Test that registering with duplicate name raises error."""
        manager = HooksManager()

        def hook1(ctx: HookContext) -> None:
            pass

        def hook2(ctx: HookContext) -> None:
            pass

        manager.register("test-hook", HookType.PRE_TASK, hook1)

        with pytest.raises(ValueError, match="already exists"):
            manager.register("test-hook", HookType.POST_TASK, hook2)

    def test_unregister_hook(self):
        """Test hook unregistration."""
        manager = HooksManager()

        def my_hook(ctx: HookContext) -> None:
            pass

        manager.register("test-hook", HookType.PRE_TASK, my_hook)
        assert manager.get_hook("test-hook") is not None

        result = manager.unregister("test-hook")
        assert result is True
        assert manager.get_hook("test-hook") is None

    def test_unregister_nonexistent_returns_false(self):
        """Test unregistering nonexistent hook returns False."""
        manager = HooksManager()
        assert manager.unregister("nonexistent") is False

    def test_enable_disable_hook(self):
        """Test enabling and disabling hooks."""
        manager = HooksManager()

        def my_hook(ctx: HookContext) -> None:
            pass

        manager.register("test-hook", HookType.PRE_TASK, my_hook)

        # Disable
        assert manager.disable("test-hook") is True
        hook = manager.get_hook("test-hook")
        assert hook.enabled is False

        # Enable
        assert manager.enable("test-hook") is True
        hook = manager.get_hook("test-hook")
        assert hook.enabled is True

    def test_enable_disable_nonexistent_returns_false(self):
        """Test enable/disable on nonexistent hook returns False."""
        manager = HooksManager()
        assert manager.enable("nonexistent") is False
        assert manager.disable("nonexistent") is False

    def test_list_hooks(self):
        """Test listing hooks."""
        manager = HooksManager()

        def hook1(ctx: HookContext) -> None:
            pass

        def hook2(ctx: HookContext) -> None:
            pass

        manager.register("hook-1", HookType.PRE_TASK, hook1)
        manager.register("hook-2", HookType.POST_TASK, hook2)

        # List all
        all_hooks = manager.list_hooks()
        assert len(all_hooks) == 2

        # Filter by type
        pre_hooks = manager.list_hooks(hook_type=HookType.PRE_TASK)
        assert len(pre_hooks) == 1
        assert pre_hooks[0].name == "hook-1"

    def test_list_hooks_enabled_only(self):
        """Test listing only enabled hooks."""
        manager = HooksManager()

        def hook1(ctx: HookContext) -> None:
            pass

        def hook2(ctx: HookContext) -> None:
            pass

        manager.register("enabled-hook", HookType.PRE_TASK, hook1)
        manager.register("disabled-hook", HookType.PRE_TASK, hook2, enabled=False)

        enabled_hooks = manager.list_hooks(enabled_only=True)
        assert len(enabled_hooks) == 1
        assert enabled_hooks[0].name == "enabled-hook"

    def test_priority_ordering(self):
        """Test that hooks are executed in priority order."""
        manager = HooksManager()
        execution_order = []

        def high_priority(ctx: HookContext) -> None:
            execution_order.append("high")

        def low_priority(ctx: HookContext) -> None:
            execution_order.append("low")

        manager.register("low", HookType.PRE_TASK, low_priority, priority=100)
        manager.register("high", HookType.PRE_TASK, high_priority, priority=10)

        # Run hooks
        manager.run_sync(HookType.PRE_TASK, {"test": "data"})

        # High priority (10) should run before low priority (100)
        assert execution_order == ["high", "low"]


class TestHookExecution:
    """Tests for hook execution."""

    def test_run_sync_no_hooks(self):
        """Test running with no hooks returns original data."""
        manager = HooksManager()

        result = manager.run_sync(HookType.PRE_TASK, {"key": "value"})

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.abort is False

    def test_run_sync_modifies_data(self):
        """Test hook modifying data."""
        manager = HooksManager()

        def modify_hook(ctx: HookContext) -> dict:
            data = ctx.data.copy()
            data["modified"] = True
            return data

        manager.register("modify", HookType.PRE_TASK, modify_hook)

        result = manager.run_sync(HookType.PRE_TASK, {"key": "value"})

        assert result.success is True
        assert result.data["modified"] is True
        assert result.data["key"] == "value"

    def test_run_sync_hook_returns_none(self):
        """Test hook returning None keeps data unchanged."""
        manager = HooksManager()

        def no_change_hook(ctx: HookContext) -> None:
            return None

        manager.register("no-change", HookType.PRE_TASK, no_change_hook)

        result = manager.run_sync(HookType.PRE_TASK, {"key": "value"})

        assert result.data == {"key": "value"}

    def test_run_sync_hook_abort(self):
        """Test hook aborting operation."""
        manager = HooksManager()

        def abort_hook(ctx: HookContext) -> None:
            raise HookAbortError("Validation failed")

        manager.register("abort", HookType.PRE_TASK, abort_hook)

        result = manager.run_sync(HookType.PRE_TASK, {"key": "value"})

        assert result.abort is True
        assert result.abort_reason == "Validation failed"

    def test_run_sync_hook_abort_via_result(self):
        """Test hook aborting via HookResult."""
        manager = HooksManager()

        def abort_hook(ctx: HookContext) -> HookResult:
            return HookResult(
                success=True,
                abort=True,
                abort_reason="Rejected by policy",
            )

        manager.register("abort", HookType.PRE_TASK, abort_hook)

        result = manager.run_sync(HookType.PRE_TASK, {"key": "value"})

        assert result.abort is True
        assert result.abort_reason == "Rejected by policy"

    def test_run_sync_hook_error_continues(self):
        """Test that hook errors don't stop other hooks."""
        manager = HooksManager()
        executed = []

        def error_hook(ctx: HookContext) -> None:
            raise ValueError("Hook error")

        def success_hook(ctx: HookContext) -> None:
            executed.append("success")

        manager.register("error", HookType.PRE_TASK, error_hook, priority=10)
        manager.register("success", HookType.PRE_TASK, success_hook, priority=20)

        result = manager.run_sync(HookType.PRE_TASK, {})

        # Error hook should have incremented error count
        error_hook_obj = manager.get_hook("error")
        assert error_hook_obj.error_count == 1

        # Success hook should still have run
        assert "success" in executed

    def test_run_sync_skips_disabled_hooks(self):
        """Test that disabled hooks are skipped."""
        manager = HooksManager()
        executed = []

        def disabled_hook(ctx: HookContext) -> None:
            executed.append("disabled")

        manager.register("disabled", HookType.PRE_TASK, disabled_hook, enabled=False)

        manager.run_sync(HookType.PRE_TASK, {})

        assert "disabled" not in executed

    def test_run_sync_chained_modifications(self):
        """Test multiple hooks modifying data in sequence."""
        manager = HooksManager()

        def add_a(ctx: HookContext) -> dict:
            data = ctx.data.copy()
            data["a"] = 1
            return data

        def add_b(ctx: HookContext) -> dict:
            data = ctx.data.copy()
            data["b"] = 2
            return data

        manager.register("add-a", HookType.PRE_TASK, add_a, priority=10)
        manager.register("add-b", HookType.PRE_TASK, add_b, priority=20)

        result = manager.run_sync(HookType.PRE_TASK, {})

        assert result.data == {"a": 1, "b": 2}


class TestAsyncHookExecution:
    """Tests for async hook execution."""

    @pytest.mark.asyncio
    async def test_run_async_hook(self):
        """Test running async hooks."""
        manager = HooksManager()

        async def async_hook(ctx: HookContext) -> dict:
            await asyncio.sleep(0.01)  # Simulate async work
            data = ctx.data.copy()
            data["async"] = True
            return data

        manager.register("async", HookType.PRE_TASK, async_hook)

        result = await manager.run(HookType.PRE_TASK, {"key": "value"})

        assert result.success is True
        assert result.data["async"] is True

    @pytest.mark.asyncio
    async def test_run_async_abort(self):
        """Test async hook aborting operation."""
        manager = HooksManager()

        async def async_abort(ctx: HookContext) -> None:
            raise HookAbortError("Async validation failed")

        manager.register("abort", HookType.PRE_TASK, async_abort)

        result = await manager.run(HookType.PRE_TASK, {})

        assert result.abort is True
        assert result.abort_reason == "Async validation failed"

    @pytest.mark.asyncio
    async def test_run_mixed_sync_async_hooks(self):
        """Test running both sync and async hooks."""
        manager = HooksManager()
        execution_order = []

        def sync_hook(ctx: HookContext) -> None:
            execution_order.append("sync")

        async def async_hook(ctx: HookContext) -> None:
            execution_order.append("async")

        manager.register("sync", HookType.PRE_TASK, sync_hook, priority=10)
        manager.register("async", HookType.PRE_TASK, async_hook, priority=20)

        await manager.run(HookType.PRE_TASK, {})

        assert execution_order == ["sync", "async"]


class TestHookContext:
    """Tests for HookContext."""

    def test_context_creation(self):
        """Test creating hook context."""
        ctx = HookContext(
            hook_type=HookType.PRE_TASK,
            operation_id="abc123",
            timestamp=datetime.now(),
            data={"task": "test"},
            metadata={"extra": "info"},
        )

        assert ctx.hook_type == HookType.PRE_TASK
        assert ctx.operation_id == "abc123"
        assert ctx.data["task"] == "test"
        assert ctx.metadata["extra"] == "info"
        assert ctx.modified is False


class TestHookResult:
    """Tests for HookResult."""

    def test_result_defaults(self):
        """Test HookResult default values."""
        result = HookResult(success=True)

        assert result.success is True
        assert result.data is None
        assert result.abort is False
        assert result.abort_reason is None
        assert result.duration_ms == 0.0

    def test_result_with_abort(self):
        """Test HookResult with abort."""
        result = HookResult(
            success=True,
            abort=True,
            abort_reason="Policy violation",
        )

        assert result.abort is True
        assert result.abort_reason == "Policy violation"


class TestHookStatistics:
    """Tests for hook statistics tracking."""

    def test_call_count_incremented(self):
        """Test that call count is incremented on each run."""
        manager = HooksManager()

        def my_hook(ctx: HookContext) -> None:
            pass

        manager.register("test", HookType.PRE_TASK, my_hook)

        manager.run_sync(HookType.PRE_TASK, {})
        manager.run_sync(HookType.PRE_TASK, {})
        manager.run_sync(HookType.PRE_TASK, {})

        hook = manager.get_hook("test")
        assert hook.call_count == 3

    def test_error_count_incremented(self):
        """Test that error count is incremented on errors."""
        manager = HooksManager()

        def error_hook(ctx: HookContext) -> None:
            raise ValueError("Test error")

        manager.register("error", HookType.PRE_TASK, error_hook)

        manager.run_sync(HookType.PRE_TASK, {})
        manager.run_sync(HookType.PRE_TASK, {})

        hook = manager.get_hook("error")
        assert hook.error_count == 2

    def test_get_stats(self):
        """Test getting hooks statistics."""
        manager = HooksManager()

        def hook1(ctx: HookContext) -> None:
            pass

        def hook2(ctx: HookContext) -> None:
            raise HookAbortError("Abort")

        manager.register("hook1", HookType.PRE_TASK, hook1)
        manager.register("hook2", HookType.POST_TASK, hook2)

        manager.run_sync(HookType.PRE_TASK, {})
        manager.run_sync(HookType.POST_TASK, {})

        stats = manager.get_stats()

        assert stats["total_hooks"] == 2
        assert stats["total_runs"] == 2
        assert stats["total_aborts"] == 1


class TestClearHooks:
    """Tests for clearing hooks."""

    def test_clear_all_hooks(self):
        """Test clearing all hooks."""
        manager = HooksManager()

        def hook1(ctx: HookContext) -> None:
            pass

        def hook2(ctx: HookContext) -> None:
            pass

        manager.register("hook1", HookType.PRE_TASK, hook1)
        manager.register("hook2", HookType.POST_TASK, hook2)

        count = manager.clear()

        assert count == 2
        assert len(manager.list_hooks()) == 0

    def test_clear_by_type(self):
        """Test clearing hooks by type."""
        manager = HooksManager()

        def hook1(ctx: HookContext) -> None:
            pass

        def hook2(ctx: HookContext) -> None:
            pass

        manager.register("hook1", HookType.PRE_TASK, hook1)
        manager.register("hook2", HookType.POST_TASK, hook2)

        count = manager.clear(HookType.PRE_TASK)

        assert count == 1
        assert len(manager.list_hooks()) == 1
        assert manager.get_hook("hook2") is not None


class TestHookInfo:
    """Tests for get_hook_info."""

    def test_get_hook_info(self):
        """Test getting hook info."""
        manager = HooksManager()

        def my_hook(ctx: HookContext) -> None:
            pass

        manager.register("test", HookType.PRE_TASK, my_hook, priority=42)
        manager.run_sync(HookType.PRE_TASK, {})

        info = manager.get_hook_info("test")

        assert info is not None
        assert info["name"] == "test"
        assert info["hook_type"] == "pre_task"
        assert info["priority"] == 42
        assert info["enabled"] is True
        assert info["call_count"] == 1
        assert "created_at" in info

    def test_get_hook_info_not_found(self):
        """Test getting info for nonexistent hook."""
        manager = HooksManager()
        assert manager.get_hook_info("nonexistent") is None


class TestHookDecorator:
    """Tests for the @hook decorator."""

    def test_hook_decorator(self):
        """Test registering hooks via decorator."""
        # Reset singleton for test
        import orchestrator.hooks as hooks_module
        hooks_module._hooks_manager = None

        @hook("decorated-hook", HookType.PRE_TASK, priority=25)
        def my_decorated_hook(ctx: HookContext) -> None:
            pass

        manager = get_hooks_manager()
        registered = manager.get_hook("decorated-hook")

        assert registered is not None
        assert registered.name == "decorated-hook"
        assert registered.priority == 25

        # Clean up
        manager.clear()


class TestHookTypes:
    """Tests for all hook types."""

    def test_all_hook_types_exist(self):
        """Test that all expected hook types exist."""
        expected_types = [
            "pre_task",
            "post_task",
            "pre_spawn",
            "post_spawn",
            "on_agent_error",
            "pre_session",
            "post_session",
            "on_session_pause",
            "on_session_resume",
            "pre_route",
            "post_route",
            "pre_memory_store",
            "post_memory_query",
        ]

        for type_name in expected_types:
            assert HookType(type_name) is not None

    def test_each_hook_type_can_have_hooks(self):
        """Test that hooks can be registered for each type."""
        manager = HooksManager()

        def my_hook(ctx: HookContext) -> None:
            pass

        for hook_type in HookType:
            name = f"hook-{hook_type.value}"
            manager.register(name, hook_type, my_hook)
            assert manager.get_hook(name) is not None

        assert len(manager.list_hooks()) == len(HookType)


class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_hooks_manager_returns_same_instance(self):
        """Test that get_hooks_manager returns the same instance."""
        # Reset singleton
        import orchestrator.hooks as hooks_module
        hooks_module._hooks_manager = None

        manager1 = get_hooks_manager()
        manager2 = get_hooks_manager()

        assert manager1 is manager2

        # Clean up
        manager1.clear()
