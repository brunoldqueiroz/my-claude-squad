---
name: new-command
description: Create a new slash command for the plugin
agent: plugin-developer
arguments:
  - name: name
    description: Command name (e.g., analyze-costs)
    required: true
  - name: category
    description: Command category directory (e.g., data-engineering, devops)
    required: true
  - name: agent
    description: Agent to assign for this command
    required: false
---

# Create New Command

Generate a new slash command file with proper structure.

## Usage

```
/new-command <name> <category>
/new-command analyze-costs data-engineering
/new-command scan-vulnerabilities devops --agent security-specialist
/new-command generate-migration data-engineering --agent sql-specialist
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `name` | Yes | - | Command name |
| `category` | Yes | - | Category directory |
| `agent` | No | - | Agent to assign |

## Categories

| Category | Purpose |
|----------|---------|
| `orchestration` | Task coordination |
| `data-engineering` | ETL, pipelines, queries |
| `devops` | Deployment, containers |
| `documentation` | Docs, commits |
| `research` | Lookup, search |
| `ai-engineering` | AI applications |
| `plugin-development` | Plugin extension |

## Generated Output

```
commands/{category}/{name}.md
```

## Agent Assignment

This command uses the **plugin-developer** agent.

## What Gets Created

The command file will contain:

1. **YAML Frontmatter**
   - name, description, arguments

2. **Usage Section**
   - Command syntax examples

3. **Arguments Table**
   - All arguments documented

4. **Generated Output**
   - File/directory structure created

5. **Agent Assignment**
   - Which agent handles this command

6. **Example Output**
   - Sample of what gets generated

## Example Output

```markdown
---
name: analyze-costs
description: Analyze cloud infrastructure costs and suggest optimizations
arguments:
  - name: provider
    description: Cloud provider (aws, gcp, azure)
    required: false
    default: aws
  - name: scope
    description: Analysis scope (compute, storage, network, all)
    required: false
    default: all
---

# Analyze Costs

Analyze cloud infrastructure costs and provide optimization recommendations.

## Usage

```
/analyze-costs
/analyze-costs --provider gcp
/analyze-costs --scope compute
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `provider` | No | `aws` | Cloud provider to analyze |
| `scope` | No | `all` | Areas to analyze |

## Generated Output

```
Cost Analysis Report:
├── Current Costs
├── Recommendations
└── Estimated Savings
```

## Agent Assignment

This command uses the **aws-specialist** agent.

## Example Output

```markdown
# Cost Analysis Report

## Current Monthly Costs
| Service | Cost | % of Total |
|---------|------|------------|
| EC2 | $1,234 | 45% |
| S3 | $567 | 21% |

## Recommendations
1. Right-size EC2 instances...
```
```

## Workflow

1. Determine appropriate category
2. Define required arguments
3. Identify agent to assign
4. Document expected output
5. Create the command file

## See Also

- `/list-commands` - See existing commands
- `skills/plugin-development-patterns/SKILL.md` - Command template reference
