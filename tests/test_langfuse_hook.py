"""Tests for Langfuse hook script."""

import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestLangfuseHookImport:
    """Test module import and dependencies."""

    def test_script_exists(self):
        """Verify the hook script file exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "langfuse_hook.py"
        assert script_path.exists(), "langfuse_hook.py not found"

    def test_script_is_executable(self):
        """Verify the script has execute permissions."""
        script_path = Path(__file__).parent.parent / "scripts" / "langfuse_hook.py"
        assert os.access(script_path, os.X_OK), "Script is not executable"


class TestGetLangfuseClient:
    """Test Langfuse client initialization."""

    def test_missing_public_key_exits(self, monkeypatch):
        """Should exit if LANGFUSE_PUBLIC_KEY is not set."""
        # Must set empty string to override .env values
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")

        import importlib
        import langfuse_hook
        importlib.reload(langfuse_hook)

        with pytest.raises(SystemExit) as exc_info:
            langfuse_hook.get_langfuse_client()
        assert exc_info.value.code == 1

    def test_missing_secret_key_exits(self, monkeypatch):
        """Should exit if LANGFUSE_SECRET_KEY is not set."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")

        import importlib
        import langfuse_hook
        importlib.reload(langfuse_hook)

        with pytest.raises(SystemExit) as exc_info:
            langfuse_hook.get_langfuse_client()
        assert exc_info.value.code == 1

    @patch("langfuse.Langfuse")
    def test_creates_client_with_credentials(self, mock_langfuse, monkeypatch):
        """Should create Langfuse client with environment credentials."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test-key")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test-key")
        monkeypatch.setenv("LANGFUSE_HOST", "https://custom.langfuse.com")

        # Need to reimport to pick up the mock
        import importlib
        import langfuse_hook
        importlib.reload(langfuse_hook)

        client = langfuse_hook.get_langfuse_client()

        mock_langfuse.assert_called_once_with(
            public_key="pk-test-key",
            secret_key="sk-test-key",
            host="https://custom.langfuse.com",
        )

    @patch("langfuse.Langfuse")
    def test_uses_default_host(self, mock_langfuse, monkeypatch):
        """Should use default host if LANGFUSE_HOST not set."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        # Set empty to override .env value and trigger default
        monkeypatch.setenv("LANGFUSE_HOST", "")

        import importlib
        import langfuse_hook
        importlib.reload(langfuse_hook)

        langfuse_hook.get_langfuse_client()

        # When host is empty, it falls back to default
        mock_langfuse.assert_called_once_with(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://cloud.langfuse.com",
        )


class TestLogToolUse:
    """Test tool use logging."""

    def test_logs_tool_call_as_span(self):
        """Should create span for tool call."""
        from langfuse_hook import log_tool_use

        mock_langfuse = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.start_span.return_value = mock_span

        hook_data = {
            "session_id": "session-123",
            "tool_name": "Write",
            "tool_input": {"file_path": "/test.txt", "content": "hello"},
            "tool_response": {"success": True},
            "tool_use_id": "toolu_abc",
            "cwd": "/home/user",
            "permission_mode": "default",
        }

        log_tool_use(mock_langfuse, hook_data)

        # Verify span was created
        mock_langfuse.start_span.assert_called_once()
        call_kwargs = mock_langfuse.start_span.call_args[1]
        assert call_kwargs["name"] == "tool:Write"
        assert call_kwargs["input"] == {"file_path": "/test.txt", "content": "hello"}

        # Verify span was updated and ended
        mock_span.update.assert_called_once_with(output={"success": True})
        mock_span.update_trace.assert_called_once()
        mock_span.end.assert_called_once()

    def test_handles_missing_fields(self):
        """Should handle missing optional fields gracefully."""
        from langfuse_hook import log_tool_use

        mock_langfuse = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.start_span.return_value = mock_span

        hook_data = {
            "hook_event_name": "PostToolUse",
        }

        log_tool_use(mock_langfuse, hook_data)

        mock_langfuse.start_span.assert_called_once()
        mock_span.end.assert_called_once()


class TestLogSessionEnd:
    """Test session end logging."""

    def test_logs_session_end_span(self):
        """Should create span to mark session end."""
        from langfuse_hook import log_session_end

        mock_langfuse = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.start_span.return_value = mock_span

        hook_data = {
            "session_id": "session-456",
            "cwd": "/project",
        }

        log_session_end(mock_langfuse, hook_data)

        # Verify span was created
        mock_langfuse.start_span.assert_called_once()
        call_kwargs = mock_langfuse.start_span.call_args[1]
        assert call_kwargs["name"] == "session_end"
        assert "completed_at" in call_kwargs["metadata"]

        # Verify trace was updated with session_id
        mock_span.update_trace.assert_called_once()
        trace_kwargs = mock_span.update_trace.call_args[1]
        assert trace_kwargs["session_id"] == "session-456"

        mock_span.end.assert_called_once()


class TestMainFunction:
    """Test main entry point."""

    @patch("langfuse_hook.get_langfuse_client")
    def test_empty_stdin_exits_cleanly(self, mock_get_client, monkeypatch):
        """Should exit without error on empty stdin."""
        monkeypatch.setattr("sys.stdin", StringIO(""))

        from langfuse_hook import main

        # Should not raise
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    @patch("langfuse_hook.get_langfuse_client")
    def test_invalid_json_exits_with_error(self, mock_get_client, monkeypatch):
        """Should exit with error on invalid JSON."""
        monkeypatch.setattr("sys.stdin", StringIO("not valid json"))

        from langfuse_hook import main

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("langfuse_hook.log_tool_use")
    @patch("langfuse_hook.get_langfuse_client")
    def test_routes_post_tool_use_event(self, mock_get_client, mock_log_tool, monkeypatch):
        """Should route PostToolUse event to log_tool_use."""
        mock_langfuse = MagicMock()
        mock_get_client.return_value = mock_langfuse

        input_data = json.dumps({
            "hook_event_name": "PostToolUse",
            "session_id": "sess-1",
            "tool_name": "Read",
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        from langfuse_hook import main

        main()

        mock_log_tool.assert_called_once()
        mock_langfuse.flush.assert_called_once()

    @patch("langfuse_hook.log_session_end")
    @patch("langfuse_hook.get_langfuse_client")
    def test_routes_stop_event(self, mock_get_client, mock_log_end, monkeypatch):
        """Should route Stop event to log_session_end."""
        mock_langfuse = MagicMock()
        mock_get_client.return_value = mock_langfuse

        input_data = json.dumps({
            "hook_event_name": "Stop",
            "session_id": "sess-2",
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        from langfuse_hook import main

        main()

        mock_log_end.assert_called_once()
        mock_langfuse.flush.assert_called_once()

    @patch("langfuse_hook.get_langfuse_client")
    def test_handles_unknown_event(self, mock_get_client, monkeypatch):
        """Should handle unknown events without error."""
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_get_client.return_value = mock_langfuse

        input_data = json.dumps({
            "hook_event_name": "SomeUnknownEvent",
            "session_id": "sess-3",
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        from langfuse_hook import main

        main()

        mock_langfuse.trace.assert_called_once()
        mock_trace.span.assert_called_once()
        mock_langfuse.flush.assert_called_once()

    @patch("langfuse_hook.get_langfuse_client")
    def test_always_flushes_on_completion(self, mock_get_client, monkeypatch):
        """Should always flush Langfuse client, even on error in logging."""
        mock_langfuse = MagicMock()
        mock_langfuse.start_span.side_effect = Exception("Span error")
        mock_get_client.return_value = mock_langfuse

        input_data = json.dumps({
            "hook_event_name": "PostToolUse",
            "session_id": "sess-4",
        })
        monkeypatch.setattr("sys.stdin", StringIO(input_data))

        from langfuse_hook import main

        with pytest.raises(Exception, match="Span error"):
            main()

        # Flush should still be called
        mock_langfuse.flush.assert_called_once()


class TestHookDataParsing:
    """Test parsing of hook data fields."""

    def test_extracts_all_post_tool_use_fields(self):
        """Should correctly extract all PostToolUse fields."""
        from langfuse_hook import log_tool_use

        mock_langfuse = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.start_span.return_value = mock_span

        hook_data = {
            "hook_event_name": "PostToolUse",
            "session_id": "abc-123",
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "tool_response": {"output": "file1\nfile2"},
            "tool_use_id": "toolu_xyz",
            "cwd": "/home/user/project",
            "permission_mode": "acceptEdits",
            "transcript_path": "/tmp/transcript.json",
        }

        log_tool_use(mock_langfuse, hook_data)

        span_call = mock_langfuse.start_span.call_args
        assert span_call[1]["name"] == "tool:Bash"
        assert span_call[1]["input"] == {"command": "ls -la"}
        mock_span.update.assert_called_once_with(output={"output": "file1\nfile2"})
