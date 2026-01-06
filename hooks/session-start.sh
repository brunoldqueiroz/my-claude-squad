#!/bin/bash
# Session Start Hook for my-claude-squad
#
# This hook runs when a Claude Code session starts in this project.
# It outputs context reminders for the user.
#
# Usage: Configure in .claude/settings.json:
#   "hooks": {
#     "SessionStart": [
#       { "command": "./hooks/session-start.sh" }
#     ]
#   }

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Count plugin components
AGENT_COUNT=$(ls "$PLUGIN_DIR/agents/"*.md 2>/dev/null | wc -l)
COMMAND_COUNT=$(find "$PLUGIN_DIR/commands" -name "*.md" 2>/dev/null | wc -l)
SKILL_COUNT=$(find "$PLUGIN_DIR/skills" -name "SKILL.md" 2>/dev/null | wc -l)

# Output session context (this will be shown to Claude)
cat << EOF
<user-prompt-submit-hook>
## my-claude-squad Plugin Context

This project contains **$AGENT_COUNT agents**, **$COMMAND_COUNT commands**, and **$SKILL_COUNT skills**.

### Agent Selection Reminder
Before implementing any task, consider which specialist agent should handle it:
- Data: python-developer, sql-specialist, snowflake-specialist, spark-specialist
- DevOps: aws-specialist, container-specialist, kubernetes-specialist
- AI: rag-specialist, llm-specialist, agent-framework-specialist, automation-specialist
- Docs: documenter, git-commit-writer
- Plugin: plugin-developer, squad-orchestrator

### Available Commands
Run \`/list-commands\` to see all available commands.

### MCP Tools Available
- Context7: Library documentation lookup
- Exa: Code examples and web search
- Memory: Knowledge graph storage
- Qdrant: Vector search
</user-prompt-submit-hook>
EOF
