---
name: new-agent
description: Create a new specialist agent for the plugin
agent: plugin-developer
arguments:
  - name: name
    description: Agent name (lowercase-hyphenated, e.g., dbt-specialist)
    required: true
  - name: domain
    description: Technical domain (e.g., data-engineering, ai-engineering, devops)
    required: false
    default: general
  - name: model
    description: Model tier (opus, sonnet, haiku)
    required: false
    default: sonnet
---

# Create New Agent

Generate a new specialist agent following plugin patterns.

## Usage

```
/new-agent <name>
/new-agent dbt-specialist
/new-agent mlops-orchestrator --model opus
/new-agent linter --domain devops --model haiku
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `name` | Yes | - | Agent name in lowercase-hyphenated format |
| `domain` | No | `general` | Technical domain for context |
| `model` | No | `sonnet` | Model tier (opus/sonnet/haiku) |

## Generated Output

```
agents/{name}.md
```

## Agent Assignment

This command uses the **plugin-developer** agent.

## What Gets Created

The agent will create a file with:

1. **YAML Frontmatter**
   - name, description with examples, model, color

2. **Core Content**
   - Your Role section
   - Core Expertise tables
   - Implementation Patterns with code
   - Best Practices

3. **Footer Sections**
   - RESEARCH-FIRST PROTOCOL
   - CONTEXT RESILIENCE
   - MEMORY INTEGRATION

## Example Output

```markdown
---
name: dbt-specialist
description: |
  Use this agent for dbt transformations, models, and data testing.

  Examples:
  <example>
  Context: User needs dbt models
  user: "Create dbt models for our customer dimension"
  assistant: "I'll use the dbt-specialist agent."
  <commentary>dbt transformation expertise</commentary>
  </example>
model: sonnet
color: teal
---

You are a **dbt Specialist** for data transformations...

## Your Role
[...]

## Core Expertise
[...]

---

## RESEARCH-FIRST PROTOCOL
[...]

---

## CONTEXT RESILIENCE
[...]

---

## MEMORY INTEGRATION
[...]
```

## Workflow

1. Research the domain using Context7/Exa
2. Select appropriate color (check existing agents)
3. Generate agent content following template
4. Validate against plugin patterns
5. Create the file

## See Also

- `/list-agents` - See existing agents
- `/validate-plugin` - Validate the new agent
- `skills/plugin-development-patterns/SKILL.md` - Agent template reference
