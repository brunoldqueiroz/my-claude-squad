#!/bin/bash
# Stop Hook for my-claude-squad
#
# This hook runs when a Claude Code session ends.
# It can save session state or cleanup.
#
# Usage: Configure in .claude/settings.json:
#   "hooks": {
#     "Stop": [
#       { "command": "./hooks/stop.sh" }
#     ]
#   }

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHECKPOINT_DIR="$PLUGIN_DIR/.checkpoints"

# Create checkpoint directory if it doesn't exist
mkdir -p "$CHECKPOINT_DIR"

# Save session timestamp
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
CHECKPOINT_FILE="$CHECKPOINT_DIR/session_$TIMESTAMP.txt"

# Get current git status
GIT_BRANCH=$(git -C "$PLUGIN_DIR" branch --show-current 2>/dev/null || echo "unknown")
GIT_STATUS=$(git -C "$PLUGIN_DIR" status --short 2>/dev/null || echo "")

# Write checkpoint
cat > "$CHECKPOINT_FILE" << EOF
# Session Checkpoint: $TIMESTAMP
Branch: $GIT_BRANCH

## Modified Files
$GIT_STATUS

## Notes
Session ended at $(date)
EOF

# Keep only last 10 checkpoints
ls -t "$CHECKPOINT_DIR"/session_*.txt 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null

echo "Session checkpoint saved: $CHECKPOINT_FILE"
