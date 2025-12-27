"""Tests for orchestrator/tracing.py - Langfuse integration."""

from unittest.mock import MagicMock, patch

import pytest


class TestIsEnabled:
    """Tests for is_enabled function."""

    def test_enabled_with_both_keys(self, monkeypatch):
        """Returns True when both keys are set."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        from orchestrator.tracing import is_enabled

        assert is_enabled() is True

    def test_disabled_missing_public_key(self, monkeypatch):
        """Returns False when public key is missing."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

        from orchestrator.tracing import is_enabled

        assert is_enabled() is False

    def test_disabled_missing_secret_key(self, monkeypatch):
        """Returns False when secret key is missing."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        from orchestrator.tracing import is_enabled

        assert is_enabled() is False

    def test_disabled_missing_both_keys(self, monkeypatch):
        """Returns False when both keys are missing."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        from orchestrator.tracing import is_enabled

        assert is_enabled() is False


class TestInit:
    """Tests for init function."""

    def test_init_success(self, langfuse_env, mock_langfuse):
        """init() returns True on successful initialization."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            result = tracing.init()

        assert result is True

    def test_init_disabled_without_keys(self, monkeypatch):
        """init() returns False when keys are missing."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        result = tracing.init()

        assert result is False

    def test_init_only_runs_once(self, langfuse_env, mock_langfuse):
        """init() only initializes once."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse) as mock_cls:
            tracing.init()
            tracing.init()
            tracing.init()

            # Should only create client once
            assert mock_cls.call_count == 1

    def test_init_handles_auth_failure(self, langfuse_env):
        """init() handles authentication failure gracefully."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        mock_client = MagicMock()
        mock_client.auth_check.side_effect = Exception("Auth failed")

        with patch("orchestrator.tracing.Langfuse", return_value=mock_client):
            result = tracing.init()

        assert result is False


class TestGetLangfuse:
    """Tests for get_langfuse function."""

    def test_returns_none_before_init(self, monkeypatch):
        """get_langfuse returns None before initialization."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        result = tracing.get_langfuse()

        assert result is None

    def test_returns_client_after_init(self, langfuse_env, mock_langfuse):
        """get_langfuse returns client after initialization."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            tracing.init()
            result = tracing.get_langfuse()

        assert result is mock_langfuse


class TestScoreTask:
    """Tests for score_task function."""

    def test_score_task_when_enabled(self, langfuse_env, mock_langfuse):
        """score_task calls score_current_trace when enabled."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            tracing.init()
            tracing.score_task("quality", 0.9, "Good result")

        mock_langfuse.score_current_trace.assert_called_once_with(
            name="quality", value=0.9, comment="Good result"
        )

    def test_score_task_when_disabled(self, monkeypatch):
        """score_task is a no-op when disabled."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        # Should not raise
        tracing.score_task("quality", 0.9)


class TestUpdateTrace:
    """Tests for update_trace function."""

    def test_update_trace_when_enabled(self, langfuse_env, mock_langfuse):
        """update_trace calls update_current_trace when enabled."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            tracing.init()
            tracing.update_trace(
                user_id="user123",
                session_id="session456",
                metadata={"key": "value"},
                tags=["test"],
            )

        mock_langfuse.update_current_trace.assert_called_once_with(
            user_id="user123",
            session_id="session456",
            metadata={"key": "value"},
            tags=["test"],
        )

    def test_update_trace_when_disabled(self, monkeypatch):
        """update_trace is a no-op when disabled."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        # Should not raise
        tracing.update_trace(user_id="test")


class TestUpdateSpan:
    """Tests for update_span function."""

    def test_update_span_when_enabled(self, langfuse_env, mock_langfuse):
        """update_span calls update_current_span when enabled."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            tracing.init()
            tracing.update_span(
                metadata={"key": "value"},
                output="result",
                level="DEBUG",
                status_message="OK",
            )

        mock_langfuse.update_current_span.assert_called_once_with(
            metadata={"key": "value"},
            output="result",
            level="DEBUG",
            status_message="OK",
        )

    def test_update_span_when_disabled(self, monkeypatch):
        """update_span is a no-op when disabled."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        # Should not raise
        tracing.update_span(output="test")


class TestFlush:
    """Tests for flush function."""

    def test_flush_when_enabled(self, langfuse_env, mock_langfuse):
        """flush calls client.flush when enabled."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            tracing.init()
            tracing.flush()

        mock_langfuse.flush.assert_called_once()

    def test_flush_when_disabled(self, monkeypatch):
        """flush is a no-op when disabled."""
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        # Should not raise
        tracing.flush()


class TestShutdown:
    """Tests for shutdown function."""

    def test_shutdown_resets_state(self, langfuse_env, mock_langfuse):
        """shutdown resets module state."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            tracing.init()
            assert tracing._initialized is True
            assert tracing._langfuse is not None

            tracing.shutdown()

            assert tracing._initialized is False
            assert tracing._langfuse is None

    def test_shutdown_flushes_first(self, langfuse_env, mock_langfuse):
        """shutdown flushes before resetting."""
        import orchestrator.tracing as tracing

        tracing._initialized = False
        tracing._langfuse = None

        with patch("orchestrator.tracing.Langfuse", return_value=mock_langfuse):
            tracing.init()
            tracing.shutdown()

        mock_langfuse.flush.assert_called()
