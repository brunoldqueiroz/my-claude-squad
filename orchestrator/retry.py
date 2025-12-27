"""Retry utilities with exponential backoff.

Provides async and sync retry decorators with configurable backoff strategies.
"""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Exception | None = None):
        super().__init__(message)
        self.last_exception = last_exception


def calculate_backoff(
    attempt: int,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    factor: float = 2.0,
    jitter: bool = True,
) -> float:
    """Calculate delay for exponential backoff.

    Args:
        attempt: Current attempt number (0-indexed)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        factor: Multiplier for each attempt
        jitter: Add random jitter to prevent thundering herd

    Returns:
        Delay in seconds
    """
    delay = initial_delay * (factor ** attempt)
    delay = min(delay, max_delay)

    if jitter:
        # Add +/- 25% jitter
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


async def retry_with_backoff_async(
    fn: Callable[..., Awaitable[T]],
    *args: Any,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
    **kwargs: Any,
) -> T:
    """Retry an async function with exponential backoff.

    Args:
        fn: Async function to retry
        *args: Positional arguments for fn
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        factor: Multiplier for each attempt
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Callback called before each retry (attempt, exception)
        **kwargs: Keyword arguments for fn

    Returns:
        Result of successful function call

    Raises:
        RetryError: If all attempts fail
    """
    last_exception: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e

            if attempt == max_attempts - 1:
                # Last attempt, don't retry
                break

            delay = calculate_backoff(
                attempt,
                initial_delay=initial_delay,
                max_delay=max_delay,
                factor=factor,
            )

            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            if on_retry:
                on_retry(attempt, e)

            await asyncio.sleep(delay)

    raise RetryError(
        f"All {max_attempts} attempts failed",
        last_exception=last_exception,
    )


def retry_with_backoff_sync(
    fn: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
    **kwargs: Any,
) -> T:
    """Retry a sync function with exponential backoff.

    Args:
        fn: Function to retry
        *args: Positional arguments for fn
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        factor: Multiplier for each attempt
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Callback called before each retry (attempt, exception)
        **kwargs: Keyword arguments for fn

    Returns:
        Result of successful function call

    Raises:
        RetryError: If all attempts fail
    """
    last_exception: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return fn(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e

            if attempt == max_attempts - 1:
                break

            delay = calculate_backoff(
                attempt,
                initial_delay=initial_delay,
                max_delay=max_delay,
                factor=factor,
            )

            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            if on_retry:
                on_retry(attempt, e)

            time.sleep(delay)

    raise RetryError(
        f"All {max_attempts} attempts failed",
        last_exception=last_exception,
    )


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for sync functions with retry logic.

    Usage:
        @with_retry(max_attempts=3, initial_delay=1.0)
        def my_function():
            ...
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_with_backoff_sync(
                fn,
                *args,
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                factor=factor,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )

        return wrapper

    return decorator


def with_retry_async(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async functions with retry logic.

    Usage:
        @with_retry_async(max_attempts=3, initial_delay=1.0)
        async def my_async_function():
            ...
    """

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff_async(
                fn,
                *args,
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                factor=factor,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )

        return wrapper

    return decorator
