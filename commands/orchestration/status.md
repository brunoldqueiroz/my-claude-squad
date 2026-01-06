---
description: Show current task status and agent progress
agent: squad-orchestrator
---

# Status

Display the current status of the task execution.

## Information to Show

1. **Current Task**: What's being worked on
2. **Progress**: Completed vs remaining tasks
3. **Active Agents**: Which specialists are engaged
4. **Files Changed**: What's been created/modified
5. **Issues**: Any blockers or failures

## Output Format

```markdown
# Task Status

## Current: [Task Name]

## Progress
[=========>     ] 65% (6/9 tasks)

## Completed
- [x] Infrastructure setup (aws-specialist)
- [x] Table creation (snowflake-specialist)
- [x] ETL script (python-developer)

## In Progress
- [ ] DAG creation (airflow-specialist) ← Current

## Pending
- [ ] Documentation (documenter)
- [ ] Commit message (git-commit-writer)

## Files Modified
- src/etl/loader.py (created)
- dags/daily_etl.py (in progress)
- infrastructure/main.tf (created)

## Issues
None

## Estimated Remaining
~15 minutes
```

## Usage

This command provides a snapshot of multi-agent task execution. Use it to:

- Check progress on complex tasks
- Identify blockers
- See what files have been changed
- Understand next steps
