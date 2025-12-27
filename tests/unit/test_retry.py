"""Tests for orchestrator/retry.py - Retry utilities."""

import asyncio
from unittest.mock import Mock

import pytest

from orchestrator.retry import (
    RetryError,
    calculate_backoff,
    retry_with_backoff_async,
    retry_with_backoff_sync,
    with_retry,
    with_retry_async,
)


class TestCalculateBackoff:
    """Tests for backoff calculation."""

    def test_initial_attempt(self):
        """First attempt (0) returns initial_delay."""
        delay = calculate_backoff(attempt=0, initial_delay=1.0, jitter=False)
        assert delay == 1.0

    def test_exponential_growth(self):
        """Delay doubles with each attempt (default factor=2)."""
        delays = [
            calculate_backoff(attempt=i, initial_delay=1.0, factor=2.0, jitter=False)
            for i in range(4)
        ]
        assert delays == [1.0, 2.0, 4.0, 8.0]

    def test_max_delay_capped(self):
        """Delay is capped at max_delay."""
        delay = calculate_backoff(
            attempt=10, initial_delay=1.0, max_delay=5.0, jitter=False
        )
        assert delay == 5.0

    def test_jitter_varies_result(self):
        """Jitter causes variation in results."""
        delays = {
            calculate_backoff(attempt=5, initial_delay=1.0, jitter=True)
            for _ in range(10)
        }
        # With jitter, we should get some variation
        assert len(delays) > 1

    def test_custom_factor(self):
        """Custom factor changes growth rate."""
        delay = calculate_backoff(attempt=2, initial_delay=1.0, factor=3.0, jitter=False)
        assert delay == 9.0  # 1.0 * 3^2

    def test_never_negative(self):
        """Result is never negative even with extreme jitter."""
        for _ in range(100):
            delay = calculate_backoff(attempt=0, initial_delay=0.001, jitter=True)
            assert delay >= 0


class TestRetrySyncSuccess:
    """Tests for sync retry success cases."""

    def test_success_first_attempt(self):
        """No retries when first attempt succeeds."""
        call_count = 0

        def success_fn():
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry_with_backoff_sync(success_fn, max_attempts=3)

        assert result == "success"
        assert call_count == 1

    def test_success_after_failures(self):
        """Retries until success."""
        call_count = 0

        def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = retry_with_backoff_sync(
            flaky_fn, max_attempts=5, initial_delay=0.01
        )

        assert result == "success"
        assert call_count == 3


class TestRetrySyncFailure:
    """Tests for sync retry failure cases."""

    def test_all_attempts_fail(self):
        """Raises RetryError when all attempts fail."""

        def always_fail():
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            retry_with_backoff_sync(always_fail, max_attempts=3, initial_delay=0.01)

        assert "All 3 attempts failed" in str(exc_info.value)

    def test_retry_error_preserves_last_exception(self):
        """RetryError includes the last exception."""

        def fail_with_message():
            raise ValueError("Specific error message")

        with pytest.raises(RetryError) as exc_info:
            retry_with_backoff_sync(
                fail_with_message, max_attempts=2, initial_delay=0.01
            )

        assert exc_info.value.last_exception is not None
        assert isinstance(exc_info.value.last_exception, ValueError)


class TestRetrySyncCallback:
    """Tests for sync retry callback."""

    def test_on_retry_callback_called(self):
        """on_retry callback is called before each retry."""
        attempts = []

        def flaky_fn():
            if len(attempts) < 2:
                raise ValueError("Not yet")
            return "success"

        def on_retry(attempt, exception):
            attempts.append((attempt, str(exception)))

        retry_with_backoff_sync(
            flaky_fn, max_attempts=5, initial_delay=0.01, on_retry=on_retry
        )

        assert len(attempts) == 2
        assert attempts[0][0] == 0  # First retry after attempt 0
        assert attempts[1][0] == 1


class TestRetrySyncExceptionFilter:
    """Tests for retryable exception filtering."""

    def test_only_retries_specified_exceptions(self):
        """Only retries on specified exception types."""
        call_count = 0

        def fail_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Wrong type")

        with pytest.raises(TypeError):
            retry_with_backoff_sync(
                fail_with_type_error,
                max_attempts=3,
                initial_delay=0.01,
                retryable_exceptions=(ValueError,),  # Not TypeError
            )

        # Should fail immediately without retrying
        assert call_count == 1


class TestRetryAsyncSuccess:
    """Tests for async retry success cases."""

    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        """No retries when first attempt succeeds."""
        call_count = 0

        async def success_fn():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_with_backoff_async(success_fn, max_attempts=3)

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_failures(self):
        """Retries until success."""
        call_count = 0

        async def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = await retry_with_backoff_async(
            flaky_fn, max_attempts=5, initial_delay=0.01
        )

        assert result == "success"
        assert call_count == 3


class TestRetryAsyncFailure:
    """Tests for async retry failure cases."""

    @pytest.mark.asyncio
    async def test_all_attempts_fail(self):
        """Raises RetryError when all attempts fail."""

        async def always_fail():
            raise ValueError("Always fails")

        with pytest.raises(RetryError):
            await retry_with_backoff_async(
                always_fail, max_attempts=3, initial_delay=0.01
            )


class TestWithRetryDecorator:
    """Tests for @with_retry sync decorator."""

    def test_decorator_success(self):
        """Decorated function works on success."""

        @with_retry(max_attempts=3, initial_delay=0.01)
        def success_fn():
            return "decorated success"

        result = success_fn()
        assert result == "decorated success"

    def test_decorator_retries(self):
        """Decorated function retries on failure."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.01)
        def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Not yet")
            return "success"

        result = flaky_fn()
        assert result == "success"
        assert call_count == 2

    def test_decorator_fails(self):
        """Decorated function raises RetryError on exhaustion."""

        @with_retry(max_attempts=2, initial_delay=0.01)
        def always_fail():
            raise ValueError("Fail")

        with pytest.raises(RetryError):
            always_fail()


class TestWithRetryAsyncDecorator:
    """Tests for @with_retry_async decorator."""

    @pytest.mark.asyncio
    async def test_async_decorator_success(self):
        """Async decorated function works on success."""

        @with_retry_async(max_attempts=3, initial_delay=0.01)
        async def success_fn():
            return "async success"

        result = await success_fn()
        assert result == "async success"

    @pytest.mark.asyncio
    async def test_async_decorator_retries(self):
        """Async decorated function retries on failure."""
        call_count = 0

        @with_retry_async(max_attempts=3, initial_delay=0.01)
        async def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Not yet")
            return "success"

        result = await flaky_fn()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_decorator_fails(self):
        """Async decorated function raises RetryError on exhaustion."""

        @with_retry_async(max_attempts=2, initial_delay=0.01)
        async def always_fail():
            raise ValueError("Fail")

        with pytest.raises(RetryError):
            await always_fail()
