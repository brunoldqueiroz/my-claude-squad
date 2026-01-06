---
description: Save current session state for context resilience and recovery
agent: squad-orchestrator
---

# Checkpoint

Manually save a session checkpoint for context resilience and later recovery.

## When to Use

- Before starting a risky operation
- At natural breakpoints in complex tasks
- Before context window fills up
- To preserve progress state for resumption

## Information to Capture

### 1. Session Context
```markdown
## Session Checkpoint: [LABEL]
**Timestamp**: [ISO timestamp]
**Working Directory**: [cwd]
**Branch**: [git branch]

## Current Task
[What the user was trying to accomplish]

## Progress Summary
- Completed: [list of completed items]
- In Progress: [current work]
- Pending: [remaining tasks]

## Key Decisions Made
[Important choices and their rationale]

## Files Modified This Session
[List of files with brief descriptions]

## Open Questions/Blockers
[Issues that need resolution]

## Next Steps
[What should happen next to continue]
```

### 2. Git State
```bash
git status --porcelain
git diff --stat
git log --oneline -5
```

### 3. Todo List State
Capture current TodoWrite state if active.

## Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `label` | Optional descriptive label | `pre-refactor`, `v1-complete` |

## Output Location

Checkpoints are saved to:
```
.checkpoints/
├── checkpoint-2024-01-15T14-30-00.md
├── checkpoint-2024-01-15T16-45-00.md
└── latest.md -> checkpoint-2024-01-15T16-45-00.md
```

## Example Usage

```
/checkpoint pre-migration
```

Creates:
```markdown
## Session Checkpoint: pre-migration
**Timestamp**: 2024-01-15T14:30:00Z
**Working Directory**: /home/user/project
**Branch**: feature/data-pipeline

## Current Task
Implementing data pipeline migration from legacy system

## Progress Summary
- Completed: Schema analysis, extraction scripts
- In Progress: Transformation logic
- Pending: Loading scripts, testing, documentation

## Key Decisions Made
- Using incremental loading with watermarks
- Chose Snowflake MERGE over DELETE+INSERT
- Keeping legacy system read-only during migration

## Files Modified This Session
- src/extract/legacy_connector.py (new)
- src/transform/normalizer.py (new)
- dbt/models/staging/stg_orders.sql (modified)

## Open Questions/Blockers
- Need credentials for production legacy database

## Next Steps
1. Complete transformation logic
2. Write unit tests for normalizer
3. Test with sample data
```

## Recovery Usage

When resuming a session:
1. Read the checkpoint: `cat .checkpoints/latest.md`
2. Review context and continue where you left off
3. The checkpoint provides all context needed for continuation

## Integration with Hooks

The `hooks/stop.sh` creates automatic checkpoints on session end. This command allows manual checkpoints at any time.
