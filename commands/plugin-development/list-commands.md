---
name: list-commands
description: List all commands organized by category
agent: plugin-developer
arguments:
  - name: category
    description: Filter by category (optional)
    required: false
---

# List Commands

Display all commands in the plugin organized by category.

## Usage

```
/list-commands
/list-commands --category data-engineering
/list-commands --category ai-engineering
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `category` | No | - | Filter to specific category |

## Agent Assignment

This command uses the **plugin-developer** agent.

## Output Format

```markdown
# Plugin Commands

## Summary
- Total: [count] commands
- Categories: [count]

## Orchestration
| Command | Description |
|---------|-------------|
| /plan-task | Analyze task and create execution plan |
| /execute-squad | Execute planned task with agents |
| /status | Show current task status |

## Data Engineering
| Command | Description |
|---------|-------------|
| /create-pipeline | Generate data pipeline boilerplate |
| /optimize-query | Analyze and optimize SQL |
| /analyze-data | Profile dataset |

[... more categories ...]
```

## What Gets Analyzed

The command reads:
- All files in `commands/*/` directories
- Category from directory name
- Description from YAML frontmatter

## Example Output

```markdown
# Plugin Commands

## Summary
- Total: 26 commands
- Categories: 7

## Orchestration (3)

| Command | Description |
|---------|-------------|
| `/plan-task` | Analyze a task and create execution plan with agent assignments |
| `/execute-squad` | Execute the planned task using assigned agents |
| `/status` | Show current task status and agent progress |

## Data Engineering (3)

| Command | Description |
|---------|-------------|
| `/create-pipeline` | Generate data pipeline boilerplate (ETL/ELT) |
| `/optimize-query` | Analyze and optimize SQL query |
| `/analyze-data` | Profile and analyze dataset |

## DevOps (3)

| Command | Description |
|---------|-------------|
| `/deploy` | Generate deployment configuration |
| `/containerize` | Create Dockerfile for project |
| `/k8s-manifest` | Generate Kubernetes manifests |

## Documentation (3)

| Command | Description |
|---------|-------------|
| `/doc-pipeline` | Document a data pipeline |
| `/doc-api` | Generate API documentation |
| `/commit` | Generate conventional commit message |

## Research (1)

| Command | Description |
|---------|-------------|
| `/lookup-docs` | Look up documentation for any library |

## AI Engineering (5)

| Command | Description |
|---------|-------------|
| `/create-rag` | Generate RAG application boilerplate |
| `/create-agent` | Generate multi-agent system structure |
| `/create-chatbot` | Generate chatbot application |
| `/create-mcp-server` | Generate MCP server template |
| `/optimize-rag` | Analyze and optimize RAG pipeline |

## Plugin Development (8)

| Command | Description |
|---------|-------------|
| `/new-agent` | Generate a new specialist agent |
| `/new-skill` | Generate a new SKILL.md reference |
| `/new-command` | Generate a new slash command |
| `/list-agents` | List all agents |
| `/list-commands` | List all commands |
| `/validate-plugin` | Validate plugin structure |
| `/update-readme` | Regenerate README |
| `/plugin-status` | Show plugin statistics |
```

## See Also

- `/list-agents` - List all agents
- `/plugin-status` - Show full statistics
