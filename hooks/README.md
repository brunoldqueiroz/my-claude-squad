# Claude Code Hooks

Event hooks that enhance the Claude Code experience with this plugin.

## Available Hooks

### session-start.sh
Runs when a Claude Code session starts. Outputs:
- Plugin component counts (agents, commands, skills)
- Agent selection reminders by domain
- Available MCP tools reminder

### pre-tool-use.sh
Runs before tool execution. Suggests relevant agents based on:
- File type being edited (Python → python-developer, SQL → sql-specialist)
- Bash commands being run (docker → container-specialist, kubectl → kubernetes-specialist)

### stop.sh
Runs when a session ends. Saves:
- Session timestamp
- Git branch and modified files
- Checkpoint file for recovery

## Configuration

Add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "command": "./hooks/session-start.sh"
      }
    ],
    "PreToolUse": [
      {
        "command": "./hooks/pre-tool-use.sh",
        "tools": ["Write", "Edit", "Bash"]
      }
    ],
    "Stop": [
      {
        "command": "./hooks/stop.sh"
      }
    ]
  }
}
```

## Checkpoints

The `stop.sh` hook saves checkpoints to `.checkpoints/` directory. These contain:
- Session end timestamp
- Current git branch
- Modified files at session end

Only the last 10 checkpoints are retained.
