"""Hooks system for pre/post operation interception.

Hooks differ from events in that they:
- Can modify input data before operations
- Can process and transform output after operations
- Can abort operations by raising HookAbortError
- Run in priority order (lower = earlier)

Use events for notifications, hooks for interception/modification.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar("T")


class HookType(str, Enum):
    """Types of hooks that can be registered."""

    # Task lifecycle
    PRE_TASK = "pre_task"  # Before task execution
    POST_TASK = "post_task"  # After task completion

    # Agent lifecycle
    PRE_SPAWN = "pre_spawn"  # Before spawning an agent
    POST_SPAWN = "post_spawn"  # After spawning an agent
    ON_AGENT_ERROR = "on_agent_error"  # When agent encounters error

    # Session lifecycle
    PRE_SESSION = "pre_session"  # Before session starts
    POST_SESSION = "post_session"  # After session ends
    ON_SESSION_PAUSE = "on_session_pause"  # When session is paused
    ON_SESSION_RESUME = "on_session_resume"  # When session is resumed

    # Routing
    PRE_ROUTE = "pre_route"  # Before routing decision
    POST_ROUTE = "post_route"  # After routing (can modify agent)

    # Memory
    PRE_MEMORY_STORE = "pre_memory_store"  # Before storing memory
    POST_MEMORY_QUERY = "post_memory_query"  # After querying memory


class HookAbortError(Exception):
    """Raised by a hook to abort the current operation.

    The message will be returned as the abort reason.
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass
class HookContext:
    """Context passed to hooks with operation details.

    Attributes:
        hook_type: Type of hook being executed
        operation_id: Unique ID for this operation
        timestamp: When the operation started
        data: The data being processed (task, session, etc.)
        metadata: Additional context metadata
        modified: Whether data has been modified by a previous hook
    """

    hook_type: HookType
    operation_id: str
    timestamp: datetime
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    modified: bool = False


@dataclass
class HookResult:
    """Result from a hook execution.

    Attributes:
        success: Whether the hook succeeded
        data: Modified data (or None to keep original)
        abort: Whether to abort the operation
        abort_reason: Reason for aborting (if abort=True)
        duration_ms: Hook execution time in milliseconds
    """

    success: bool
    data: dict[str, Any] | None = None
    abort: bool = False
    abort_reason: str | None = None
    duration_ms: float = 0.0


# Type aliases for hook handlers
SyncHook = Callable[[HookContext], HookResult | dict[str, Any] | None]
AsyncHook = Callable[[HookContext], Awaitable[HookResult | dict[str, Any] | None]]
HookHandler = SyncHook | AsyncHook


@dataclass
class RegisteredHook:
    """A registered hook with metadata.

    Attributes:
        name: Unique name for this hook registration
        hook_type: Type of hook
        handler: The hook function
        priority: Execution order (lower = earlier, default 100)
        enabled: Whether the hook is currently enabled
        created_at: When the hook was registered
        call_count: Number of times the hook has been called
        error_count: Number of times the hook has errored
    """

    name: str
    hook_type: HookType
    handler: HookHandler
    priority: int = 100
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    call_count: int = 0
    error_count: int = 0


class HooksManager:
    """Manages hook registration and execution.

    Hooks are executed in priority order (lower priority value = earlier).
    Each hook can:
    - Return modified data to pass to next hook
    - Return None to keep current data unchanged
    - Raise HookAbortError to stop the operation
    - Return HookResult for fine-grained control

    Example:
        hooks = HooksManager()

        # Register a pre-task hook
        def validate_task(ctx: HookContext) -> dict | None:
            task = ctx.data
            if not task.get("description"):
                raise HookAbortError("Task must have a description")
            return None  # No modifications

        hooks.register("validate-task", HookType.PRE_TASK, validate_task)

        # Run hooks before task execution
        result = await hooks.run(HookType.PRE_TASK, task_data)
        if result.abort:
            print(f"Task aborted: {result.abort_reason}")
        else:
            execute_task(result.data)
    """

    def __init__(self):
        """Initialize the hooks manager."""
        # Hooks organized by type
        self._hooks: dict[HookType, list[RegisteredHook]] = {
            hook_type: [] for hook_type in HookType
        }

        # Quick lookup by name
        self._hooks_by_name: dict[str, RegisteredHook] = {}

        # Statistics
        self._total_runs: int = 0
        self._total_aborts: int = 0
        self._total_errors: int = 0

    def register(
        self,
        name: str,
        hook_type: HookType,
        handler: HookHandler,
        priority: int = 100,
        enabled: bool = True,
    ) -> RegisteredHook:
        """Register a hook.

        Args:
            name: Unique name for this hook
            hook_type: Type of hook (when to run)
            handler: Function to call (sync or async)
            priority: Execution order (lower = earlier)
            enabled: Whether to enable immediately

        Returns:
            The registered hook

        Raises:
            ValueError: If a hook with this name already exists
        """
        if name in self._hooks_by_name:
            raise ValueError(f"Hook '{name}' already exists")

        hook = RegisteredHook(
            name=name,
            hook_type=hook_type,
            handler=handler,
            priority=priority,
            enabled=enabled,
        )

        self._hooks[hook_type].append(hook)
        self._hooks_by_name[name] = hook

        # Keep hooks sorted by priority
        self._hooks[hook_type].sort(key=lambda h: h.priority)

        logger.info(f"Registered hook '{name}' for {hook_type.value} (priority={priority})")
        return hook

    def unregister(self, name: str) -> bool:
        """Unregister a hook by name.

        Args:
            name: Name of hook to remove

        Returns:
            True if hook was removed, False if not found
        """
        hook = self._hooks_by_name.pop(name, None)
        if not hook:
            return False

        self._hooks[hook.hook_type].remove(hook)
        logger.info(f"Unregistered hook '{name}'")
        return True

    def enable(self, name: str) -> bool:
        """Enable a hook by name.

        Args:
            name: Name of hook to enable

        Returns:
            True if hook was enabled, False if not found
        """
        hook = self._hooks_by_name.get(name)
        if not hook:
            return False
        hook.enabled = True
        logger.debug(f"Enabled hook '{name}'")
        return True

    def disable(self, name: str) -> bool:
        """Disable a hook by name.

        Args:
            name: Name of hook to disable

        Returns:
            True if hook was disabled, False if not found
        """
        hook = self._hooks_by_name.get(name)
        if not hook:
            return False
        hook.enabled = False
        logger.debug(f"Disabled hook '{name}'")
        return True

    def get_hook(self, name: str) -> RegisteredHook | None:
        """Get a registered hook by name.

        Args:
            name: Name of the hook

        Returns:
            The RegisteredHook or None if not found
        """
        return self._hooks_by_name.get(name)

    def list_hooks(
        self,
        hook_type: HookType | None = None,
        enabled_only: bool = False,
    ) -> list[RegisteredHook]:
        """List registered hooks.

        Args:
            hook_type: Filter by hook type (None = all types)
            enabled_only: Only return enabled hooks

        Returns:
            List of matching hooks
        """
        if hook_type is not None:
            hooks = list(self._hooks[hook_type])
        else:
            hooks = list(self._hooks_by_name.values())

        if enabled_only:
            hooks = [h for h in hooks if h.enabled]

        return sorted(hooks, key=lambda h: (h.hook_type.value, h.priority))

    async def run(
        self,
        hook_type: HookType,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> HookResult:
        """Run all hooks of a given type.

        Hooks are executed in priority order. Each hook receives the data
        (possibly modified by previous hooks) and can:
        - Return modified data
        - Return None to keep data unchanged
        - Raise HookAbortError to abort the operation

        Args:
            hook_type: Type of hooks to run
            data: Data to process (e.g., task dict, session dict)
            metadata: Additional context for hooks

        Returns:
            HookResult with final data and abort status
        """
        self._total_runs += 1
        operation_id = str(uuid.uuid4())[:8]

        # Get enabled hooks sorted by priority
        hooks = [h for h in self._hooks[hook_type] if h.enabled]

        if not hooks:
            return HookResult(success=True, data=data)

        current_data = data.copy()
        modified = False
        total_duration = 0.0

        for hook in hooks:
            context = HookContext(
                hook_type=hook_type,
                operation_id=operation_id,
                timestamp=datetime.now(),
                data=current_data,
                metadata=metadata or {},
                modified=modified,
            )

            start_time = datetime.now()
            try:
                hook.call_count += 1

                # Execute the hook
                result = hook.handler(context)
                if asyncio.iscoroutine(result):
                    result = await result

                # Calculate duration
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                total_duration += duration_ms

                # Process result
                if isinstance(result, HookResult):
                    if result.abort:
                        self._total_aborts += 1
                        logger.info(
                            f"Hook '{hook.name}' aborted operation: {result.abort_reason}"
                        )
                        return HookResult(
                            success=True,
                            data=current_data,
                            abort=True,
                            abort_reason=result.abort_reason,
                            duration_ms=total_duration,
                        )
                    if result.data is not None:
                        current_data = result.data
                        modified = True
                elif isinstance(result, dict):
                    current_data = result
                    modified = True
                # None means no change

                logger.debug(
                    f"Hook '{hook.name}' completed in {duration_ms:.2f}ms "
                    f"(modified={modified})"
                )

            except HookAbortError as e:
                self._total_aborts += 1
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(f"Hook '{hook.name}' aborted: {e.reason}")
                return HookResult(
                    success=True,
                    data=current_data,
                    abort=True,
                    abort_reason=e.reason,
                    duration_ms=total_duration + duration_ms,
                )

            except Exception as e:
                hook.error_count += 1
                self._total_errors += 1
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Hook '{hook.name}' error: {e}",
                    exc_info=True,
                )
                # Continue with other hooks despite error
                total_duration += duration_ms

        return HookResult(
            success=True,
            data=current_data,
            abort=False,
            duration_ms=total_duration,
        )

    def run_sync(
        self,
        hook_type: HookType,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> HookResult:
        """Run hooks synchronously (for sync-only handlers).

        Same as run() but for synchronous contexts. Async hooks are skipped.

        Args:
            hook_type: Type of hooks to run
            data: Data to process
            metadata: Additional context for hooks

        Returns:
            HookResult with final data and abort status
        """
        self._total_runs += 1
        operation_id = str(uuid.uuid4())[:8]

        hooks = [h for h in self._hooks[hook_type] if h.enabled]

        if not hooks:
            return HookResult(success=True, data=data)

        current_data = data.copy()
        modified = False
        total_duration = 0.0

        for hook in hooks:
            context = HookContext(
                hook_type=hook_type,
                operation_id=operation_id,
                timestamp=datetime.now(),
                data=current_data,
                metadata=metadata or {},
                modified=modified,
            )

            start_time = datetime.now()
            try:
                hook.call_count += 1

                result = hook.handler(context)
                if asyncio.iscoroutine(result):
                    logger.warning(f"Skipping async hook '{hook.name}' in sync run")
                    result.close()
                    continue

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                total_duration += duration_ms

                if isinstance(result, HookResult):
                    if result.abort:
                        self._total_aborts += 1
                        return HookResult(
                            success=True,
                            data=current_data,
                            abort=True,
                            abort_reason=result.abort_reason,
                            duration_ms=total_duration,
                        )
                    if result.data is not None:
                        current_data = result.data
                        modified = True
                elif isinstance(result, dict):
                    current_data = result
                    modified = True

            except HookAbortError as e:
                self._total_aborts += 1
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                return HookResult(
                    success=True,
                    data=current_data,
                    abort=True,
                    abort_reason=e.reason,
                    duration_ms=total_duration + duration_ms,
                )

            except Exception as e:
                hook.error_count += 1
                self._total_errors += 1
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(f"Hook '{hook.name}' error: {e}", exc_info=True)
                total_duration += duration_ms

        return HookResult(
            success=True,
            data=current_data,
            abort=False,
            duration_ms=total_duration,
        )

    def clear(self, hook_type: HookType | None = None) -> int:
        """Clear registered hooks.

        Args:
            hook_type: Type to clear (None = clear all)

        Returns:
            Number of hooks cleared
        """
        count = 0

        if hook_type is not None:
            for hook in self._hooks[hook_type]:
                del self._hooks_by_name[hook.name]
                count += 1
            self._hooks[hook_type].clear()
        else:
            count = len(self._hooks_by_name)
            for hook_list in self._hooks.values():
                hook_list.clear()
            self._hooks_by_name.clear()

        logger.info(f"Cleared {count} hooks")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get hooks statistics.

        Returns:
            Dictionary with hook counts, runs, aborts, errors
        """
        hooks_by_type = {
            hook_type.value: len(hooks)
            for hook_type, hooks in self._hooks.items()
            if hooks
        }

        enabled_count = sum(1 for h in self._hooks_by_name.values() if h.enabled)

        return {
            "total_hooks": len(self._hooks_by_name),
            "enabled_hooks": enabled_count,
            "disabled_hooks": len(self._hooks_by_name) - enabled_count,
            "hooks_by_type": hooks_by_type,
            "total_runs": self._total_runs,
            "total_aborts": self._total_aborts,
            "total_errors": self._total_errors,
        }

    def get_hook_info(self, name: str) -> dict[str, Any] | None:
        """Get detailed info about a hook.

        Args:
            name: Name of the hook

        Returns:
            Dictionary with hook details or None if not found
        """
        hook = self._hooks_by_name.get(name)
        if not hook:
            return None

        return {
            "name": hook.name,
            "hook_type": hook.hook_type.value,
            "priority": hook.priority,
            "enabled": hook.enabled,
            "created_at": hook.created_at.isoformat(),
            "call_count": hook.call_count,
            "error_count": hook.error_count,
        }


# Singleton instance
_hooks_manager: HooksManager | None = None


def get_hooks_manager() -> HooksManager:
    """Get or create the singleton HooksManager instance.

    Returns:
        The global HooksManager instance
    """
    global _hooks_manager
    if _hooks_manager is None:
        _hooks_manager = HooksManager()
    return _hooks_manager


# Decorator for registering hooks
def hook(
    name: str,
    hook_type: HookType,
    priority: int = 100,
    enabled: bool = True,
):
    """Decorator to register a function as a hook.

    Example:
        @hook("validate-task", HookType.PRE_TASK)
        def validate_task(ctx: HookContext) -> dict | None:
            if not ctx.data.get("description"):
                raise HookAbortError("Task needs description")
            return None

    Args:
        name: Unique hook name
        hook_type: When to run the hook
        priority: Execution order (lower = earlier)
        enabled: Whether to enable immediately

    Returns:
        Decorator function
    """

    def decorator(func: HookHandler) -> HookHandler:
        manager = get_hooks_manager()
        manager.register(name, hook_type, func, priority, enabled)
        return func

    return decorator
