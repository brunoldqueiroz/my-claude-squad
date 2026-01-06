# Collaboration Templates

Pre-defined patterns for multi-agent coordination on complex tasks.

## Purpose

These templates define:
- **Agent sequences**: Which specialists engage and in what order
- **Handoff protocols**: How work passes between agents
- **Coordination patterns**: Sequential, parallel, or iterative flows
- **Quality gates**: Checkpoints between agent transitions

## Available Templates

| Template | Use Case | Agents Involved |
|----------|----------|-----------------|
| [data-pipeline-build](data-pipeline-build.md) | End-to-end ETL/ELT implementation | sql, python, airflow, documenter |
| [full-stack-feature](full-stack-feature.md) | Feature with API + infrastructure | python, aws, container, k8s |
| [code-review-cycle](code-review-cycle.md) | Review and iteration workflow | Any specialist + plugin-developer |
| [migration-project](migration-project.md) | Database/platform migrations | sql, snowflake, python, documenter |

## Coordination Patterns

### Sequential (Waterfall)
```
Agent A → Agent B → Agent C
```
Each agent completes fully before the next begins. Best for dependencies.

### Parallel (Fan-out)
```
        → Agent A →
Task →  → Agent B →  → Merge
        → Agent C →
```
Independent work happens simultaneously. Best for speed.

### Iterative (Review Loop)
```
Agent A ←→ Agent B (repeat until done)
```
Agents refine each other's work. Best for quality.

### Pipeline (Streaming)
```
Agent A → partial → Agent B → partial → Agent C
```
Work streams through agents. Best for large tasks.

## Using Templates

### Option 1: Reference in Plan
```
Use the data-pipeline-build collaboration template for this ETL task.
Specialists needed: sql-specialist, python-developer, airflow-specialist.
```

### Option 2: Invoke via Squad Orchestrator
```
/execute-squad --template data-pipeline-build --task "Build orders ETL"
```

### Option 3: Manual Coordination
Follow the template steps manually, invoking each agent in sequence.

## Template Structure

Each template defines:

```markdown
# Template Name

## Overview
Brief description and when to use.

## Agent Sequence
1. **Agent A** (role): What they do
2. **Agent B** (role): What they do
...

## Handoff Protocol
What information passes between agents.

## Quality Gates
Checkpoints and validation criteria.

## Example Execution
Concrete example of the template in action.
```

## Creating Custom Templates

1. Identify repeating multi-agent patterns in your workflow
2. Document the agent sequence and handoffs
3. Add quality gates at critical transitions
4. Save to `collaboration/` directory
