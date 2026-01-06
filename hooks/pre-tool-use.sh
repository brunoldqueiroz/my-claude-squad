#!/bin/bash
# Pre Tool Use Hook for my-claude-squad
#
# This hook runs before tool execution to suggest relevant agents.
# It reads the tool name from stdin and outputs agent suggestions.
#
# Usage: Configure in .claude/settings.json:
#   "hooks": {
#     "PreToolUse": [
#       {
#         "command": "./hooks/pre-tool-use.sh",
#         "tools": ["Write", "Edit", "Bash"]
#       }
#     ]
#   }

# Read tool info from stdin (JSON format)
TOOL_INFO=$(cat)
TOOL_NAME=$(echo "$TOOL_INFO" | jq -r '.tool // empty' 2>/dev/null)

# If no tool name, exit silently
[ -z "$TOOL_NAME" ] && exit 0

# Suggest agents based on tool being used
case "$TOOL_NAME" in
  Write|Edit)
    # Check if editing Python files
    FILE_PATH=$(echo "$TOOL_INFO" | jq -r '.input.file_path // empty' 2>/dev/null)
    if [[ "$FILE_PATH" == *.py ]]; then
      echo "<user-prompt-submit-hook>"
      echo "AGENT SUGGESTION: Consider using python-developer for Python code."
      echo "</user-prompt-submit-hook>"
    elif [[ "$FILE_PATH" == *.sql ]]; then
      echo "<user-prompt-submit-hook>"
      echo "AGENT SUGGESTION: Consider using sql-specialist for SQL code."
      echo "</user-prompt-submit-hook>"
    elif [[ "$FILE_PATH" == *Dockerfile* ]]; then
      echo "<user-prompt-submit-hook>"
      echo "AGENT SUGGESTION: Consider using container-specialist for Dockerfile."
      echo "</user-prompt-submit-hook>"
    fi
    ;;
  Bash)
    COMMAND=$(echo "$TOOL_INFO" | jq -r '.input.command // empty' 2>/dev/null)
    if [[ "$COMMAND" == *docker* ]]; then
      echo "<user-prompt-submit-hook>"
      echo "AGENT SUGGESTION: Consider using container-specialist for Docker operations."
      echo "</user-prompt-submit-hook>"
    elif [[ "$COMMAND" == *kubectl* ]] || [[ "$COMMAND" == *helm* ]]; then
      echo "<user-prompt-submit-hook>"
      echo "AGENT SUGGESTION: Consider using kubernetes-specialist for K8s operations."
      echo "</user-prompt-submit-hook>"
    elif [[ "$COMMAND" == *aws* ]] || [[ "$COMMAND" == *terraform* ]]; then
      echo "<user-prompt-submit-hook>"
      echo "AGENT SUGGESTION: Consider using aws-specialist for AWS/Terraform operations."
      echo "</user-prompt-submit-hook>"
    fi
    ;;
esac

exit 0
