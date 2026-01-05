#!/usr/bin/env python3
"""Claude Code hook script for Langfuse observability.

Logs tool calls and sessions to Langfuse for observability.
Reads hook data from stdin and sends traces to Langfuse.

Setup:
1. Install: pip install langfuse
2. Set environment variables:
   - LANGFUSE_PUBLIC_KEY
   - LANGFUSE_SECRET_KEY
   - LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)

Usage in Claude Code hooks (settings.json):
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{"type": "command", "command": "python /path/to/langfuse_hook.py"}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "python /path/to/langfuse_hook.py"}]
    }]
  }
}
"""

import json
import os
import sys
from datetime import datetime

# Session trace cache (per-process, resets on script restart)
_session_traces = {}


def get_langfuse_client():
    """Initialize Langfuse client from environment variables."""
    try:
        from langfuse import Langfuse
    except ImportError:
        print("Error: langfuse not installed. Run: pip install langfuse", file=sys.stderr)
        sys.exit(1)

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        print("Error: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set", file=sys.stderr)
        sys.exit(1)

    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )


def log_tool_use(langfuse, hook_data: dict) -> None:
    """Log a tool call to Langfuse."""
    session_id = hook_data.get("session_id", "unknown")
    tool_name = hook_data.get("tool_name", "unknown")
    tool_input = hook_data.get("tool_input", {})
    tool_response = hook_data.get("tool_response", {})
    tool_use_id = hook_data.get("tool_use_id", "")

    # Create or get trace for this session
    trace = langfuse.trace(
        id=session_id,
        name=f"claude-code-session",
        session_id=session_id,
        metadata={
            "cwd": hook_data.get("cwd", ""),
            "permission_mode": hook_data.get("permission_mode", ""),
        },
    )

    # Log the tool call as a span
    trace.span(
        name=tool_name,
        input=tool_input,
        output=tool_response,
        metadata={
            "tool_use_id": tool_use_id,
            "hook_event": "PostToolUse",
        },
    )


def log_session_end(langfuse, hook_data: dict) -> None:
    """Log session end to Langfuse."""
    session_id = hook_data.get("session_id", "unknown")

    # Update the trace to mark session complete
    trace = langfuse.trace(
        id=session_id,
        name=f"claude-code-session",
        session_id=session_id,
        metadata={
            "cwd": hook_data.get("cwd", ""),
            "completed_at": datetime.now().isoformat(),
        },
    )

    trace.span(
        name="session_end",
        metadata={"hook_event": "Stop"},
    )


def main():
    """Main entry point for the hook script."""
    # Read JSON from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)
        hook_data = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    hook_event = hook_data.get("hook_event_name", "")

    # Initialize Langfuse
    langfuse = get_langfuse_client()

    try:
        if hook_event == "PostToolUse":
            log_tool_use(langfuse, hook_data)
        elif hook_event == "Stop":
            log_session_end(langfuse, hook_data)
        else:
            # Unknown event, just log it
            session_id = hook_data.get("session_id", "unknown")
            trace = langfuse.trace(
                id=session_id,
                name="claude-code-session",
                session_id=session_id,
            )
            trace.span(
                name=hook_event,
                input=hook_data,
            )
    finally:
        # Ensure all events are flushed
        langfuse.flush()


if __name__ == "__main__":
    main()
