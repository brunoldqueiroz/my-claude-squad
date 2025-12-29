---
description: Execute a planned task using the assigned specialist agents
argument-hint: [plan-reference or task]
---

# Execute Squad

Execute a multi-agent task plan, coordinating specialist agents.

## Process

1. **Load Plan**: If a plan exists, load it. Otherwise, create one first.

2. **Execute in Order**:
   - Process tasks respecting dependencies
   - Launch parallel tasks simultaneously where possible
   - Collect outputs from each agent

3. **Coordinate Handoffs**:
   - Pass relevant context between agents
   - Share file paths and references
   - Consolidate outputs

4. **Handle Failures**:
   - If an agent fails, assess impact
   - Retry or adjust plan as needed
   - Report issues clearly

5. **Consolidate Results**:
   - Gather all outputs
   - Verify completeness
   - Report final status

## Agent Invocation

Use the Task tool to invoke specialist agents:

```
Task(
    subagent_type="general-purpose",
    prompt="[Specific task for the agent, including context and requirements]",
    description="[Brief description]"
)
```

## Coordination Example

For a pipeline task:

1. **Phase 1** (Sequential):
   - Invoke aws-specialist for infrastructure
   - Wait for completion, capture resource IDs

2. **Phase 2** (Parallel):
   - Invoke snowflake-specialist with S3 details
   - Invoke python-developer with connection info
   - Both can work simultaneously

3. **Phase 3** (Sequential):
   - Invoke airflow-specialist with all components
   - Needs outputs from Phase 2

4. **Phase 4** (Parallel):
   - Invoke documenter for docs
   - Invoke git-commit-writer for commit

## Output

Report execution status:

```markdown
# Execution Report

## Status: [Completed | Partial | Failed]

## Completed Tasks
- [x] Task 1 (agent-name): [output summary]
- [x] Task 2 (agent-name): [output summary]

## Files Created/Modified
- path/to/file1.py
- path/to/file2.sql

## Issues Encountered
- [Any issues and resolutions]

## Next Steps
- [If any follow-up needed]
```
