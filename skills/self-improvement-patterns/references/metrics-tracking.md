# Agent Performance Metrics

Detailed reference for tracking and analyzing agent performance.

## Metrics Categories

### 1. Usage Metrics

Track how often each agent is invoked.

```markdown
## Tracking Template

| Agent | Weekly Invocations | Trend | Notes |
|-------|-------------------|-------|-------|
| python-developer | 12 | ↑ | Most used |
| sql-specialist | 8 | → | Stable |
| airflow-specialist | 3 | ↓ | Less DAG work |
```

### 2. Task Completion Metrics

Track success/failure patterns.

```markdown
## Completion Tracking

| Agent | Tasks Started | Completed | Blocked | Success Rate |
|-------|--------------|-----------|---------|--------------|
| python-developer | 12 | 11 | 1 | 92% |
| sql-specialist | 8 | 8 | 0 | 100% |
```

#### Failure Analysis Template

```markdown
## Failure Analysis: [Agent Name]

### Recent Failures
1. **Task**: [description]
   - **Blocker**: [what prevented completion]
   - **Resolution**: [how it was resolved]
   - **Prevention**: [how to prevent recurrence]
```

### 3. Efficiency Metrics

Track how efficiently agents complete tasks.

```markdown
## Efficiency Tracking

| Agent | Avg Duration | Avg Tool Calls | Avg Iterations |
|-------|-------------|----------------|----------------|
| python-developer | 8 min | 15 | 2.3 |
| sql-specialist | 5 min | 8 | 1.5 |
```

### 4. Collaboration Metrics

Track multi-agent patterns.

```markdown
## Collaboration Patterns

### Common Sequences
1. python-developer → documenter (18x)
2. sql-specialist → python-developer (12x)
3. aws-specialist → container-specialist (8x)

### Team Compositions
| Task Type | Typical Team | Frequency |
|-----------|--------------|-----------|
| ETL Pipeline | sql + python + airflow | 34% |
| API Feature | python + aws + container | 22% |
| Migration | sql + python + documenter | 15% |
```

## Collection Methods

### Manual Tracking (Checkpoint-Based)

Add to session checkpoints:

```markdown
## Metrics for This Session

### Agents Used
- python-developer: 2 tasks (completed: 2)
- sql-specialist: 1 task (completed: 1)

### Duration
- Total session: 45 min
- python-developer avg: 12 min/task
- sql-specialist: 8 min

### Tools Used
- Edit: 23 calls
- Bash: 15 calls
- Read: 45 calls
```

### Git-Based Analysis

Extract metrics from commit history:

```bash
# Commits by AI in last 30 days
git log --since="30 days ago" --author="Claude" --oneline | wc -l

# Files modified per commit (average)
git log --since="30 days ago" --stat --author="Claude" | \
  grep "files changed" | \
  awk '{sum+=$1; count++} END {print sum/count}'

# Most modified file types
git log --since="30 days ago" --name-only --author="Claude" | \
  grep -E "^\S" | \
  sed 's/.*\.//' | \
  sort | uniq -c | sort -rn
```

### Hook-Based Collection

Use session hooks to log metrics:

```bash
# hooks/stop.sh addition
echo "$(date -Iseconds),${AGENT:-unknown},${TASK_DURATION:-0},${TASK_STATUS:-unknown}" \
  >> .metrics/agent-usage.csv
```

## Analysis Patterns

### Weekly Review Template

```markdown
## Weekly Metrics Review

### Period: [Start Date] - [End Date]

### Summary
- Total tasks: [count]
- Overall success rate: [percentage]
- Most active agent: [name]
- Most improved: [name]

### Agent Performance

| Agent | Tasks | Success | Trend |
|-------|-------|---------|-------|
| ... | ... | ... | ... |

### Insights
1. [Key finding 1]
2. [Key finding 2]

### Action Items
- [ ] [Improvement 1]
- [ ] [Improvement 2]
```

### Improvement Prioritization

Based on metrics, prioritize improvements:

```markdown
## Improvement Priority Matrix

### High Impact, Low Effort (Do First)
- Agent X: Add example for common failure case

### High Impact, High Effort (Plan)
- Agent Y: Major prompt rewrite for clarity

### Low Impact, Low Effort (Quick Wins)
- Agent Z: Fix typo in description

### Low Impact, High Effort (Skip)
- Agent W: Rarely used, complex to improve
```

## Benchmarking

### Inter-Agent Comparison

Compare similar agents:

```markdown
## SQL Agents Comparison

| Metric | sql-specialist | snowflake-specialist | sql-server-specialist |
|--------|---------------|---------------------|----------------------|
| Usage | 38 | 22 | 15 |
| Success | 97% | 95% | 93% |
| Avg Duration | 5 min | 6 min | 7 min |

### Analysis
- sql-specialist is general-purpose, highest usage
- Platform-specific agents have slightly lower success
- Consider improving error handling in sql-server
```

### Trend Analysis

Track changes over time:

```markdown
## 4-Week Trend: python-developer

| Week | Tasks | Success | Duration |
|------|-------|---------|----------|
| W1 | 10 | 90% | 10 min |
| W2 | 12 | 92% | 9 min |
| W3 | 11 | 91% | 8 min |
| W4 | 14 | 94% | 8 min |

### Trend: Improving ↑
Success rate up 4%, duration down 2 min.
Likely due to: Enhanced error handling prompt added W2.
```

## Dashboard Format

Simple text-based dashboard for quick review:

```
╔═══════════════════════════════════════════════════════════╗
║               AGENT METRICS DASHBOARD                      ║
╠═══════════════════════════════════════════════════════════╣
║  Period: Last 7 Days                                       ║
║  Total Tasks: 34 | Success Rate: 94%                       ║
╠═══════════════════════════════════════════════════════════╣
║  TOP AGENTS                                                ║
║  1. python-developer  ████████████░░░ 12 tasks (100%)     ║
║  2. sql-specialist    ████████░░░░░░░  8 tasks (100%)     ║
║  3. documenter        ██████░░░░░░░░░  6 tasks (100%)     ║
║  4. airflow-specialist ███░░░░░░░░░░░░  3 tasks (67%)     ║
╠═══════════════════════════════════════════════════════════╣
║  ALERTS                                                    ║
║  ⚠ airflow-specialist: 2 failures this week               ║
║  ⚠ container-specialist: Not used in 14 days              ║
╚═══════════════════════════════════════════════════════════╝
```
