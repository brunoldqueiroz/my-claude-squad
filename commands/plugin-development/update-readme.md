---
name: update-readme
description: Regenerate README.md from current plugin state
agent: plugin-developer
arguments: []
---

# Update README

Regenerate the README.md file to reflect the current plugin state.

## Usage

```
/update-readme
```

## Agent Assignment

This command uses the **plugin-developer** agent.

## What Gets Updated

1. **Agent Count** in overview
2. **Agent Tables** by domain
3. **Command List** by category
4. **Skills List**
5. **Tech Stack Coverage**

## Process

1. Read all files in `agents/`
2. Read all files in `commands/*/`
3. Read all files in `skills/*/`
4. Categorize by domain
5. Update counts and tables
6. Preserve custom content sections

## Sections Preserved

- Installation instructions
- Usage examples (if custom)
- License
- Custom documentation

## Sections Updated

- Overview (agent count)
- Agents table
- Commands list
- Skills list
- Tech stack (if auto-generated)

## Example Changes

### Before

```markdown
## Overview

This plugin provides 15 specialized AI agents...

## Agents

| Agent | Specialty |
|-------|-----------|
| python-developer | Python for data engineering |
[... old list ...]
```

### After

```markdown
## Overview

This plugin provides 17 specialized AI agents...

## Agents

| Agent | Specialty |
|-------|-----------|
| squad-orchestrator | Master orchestrator for all domains |
[... complete updated list ...]
| plugin-developer | Component creation |
```

## Output

The command will:

1. Show diff of changes
2. Ask for confirmation
3. Update README.md

```markdown
## README Update Preview

### Changes
- Agent count: 15 → 17
- Added agents: squad-orchestrator, plugin-developer
- Added commands: /audit-plugin, /improve-routing, /improve-agent, /add-tests
- Added skill: self-improvement-patterns

### Sections Updated
- Overview
- Orchestrator section
- Self-Improvement Commands section

Proceed with update? [Y/n]
```

## See Also

- `/plugin-status` - Check current state before update
- `/validate-plugin` - Validate after update
- `/list-agents` - See agent list format
