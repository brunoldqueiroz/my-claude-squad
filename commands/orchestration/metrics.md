---
description: Display agent usage metrics and performance analytics
agent: squad-orchestrator
---

# Agent Metrics

Track and display agent usage patterns and performance analytics.

## Purpose

- Understand which agents are used most frequently
- Identify optimization opportunities
- Track task completion patterns
- Inform agent improvement decisions

## Metrics Categories

### 1. Usage Metrics
```markdown
## Agent Usage (Last 30 Days)

| Agent | Invocations | Avg Duration | Success Rate |
|-------|-------------|--------------|--------------|
| python-developer | 45 | 8.2 min | 94% |
| sql-specialist | 38 | 5.1 min | 97% |
| documenter | 22 | 3.4 min | 100% |
| airflow-specialist | 15 | 12.3 min | 87% |
```

### 2. Tool Usage Per Agent
```markdown
## Tool Usage by Agent

### python-developer
- Edit: 156 calls
- Write: 89 calls
- Bash (pytest): 67 calls
- Read: 234 calls

### sql-specialist
- Edit: 78 calls
- Bash (sql): 45 calls
- Read: 189 calls
```

### 3. Collaboration Patterns
```markdown
## Common Agent Sequences

1. python-developer → documenter (18 times)
2. sql-specialist → python-developer (12 times)
3. airflow-specialist → documenter (8 times)

## Multi-Agent Tasks
- Average agents per task: 2.3
- Most common combination: python + sql (34%)
```

### 4. Task Complexity
```markdown
## Task Distribution

| Complexity | Count | Avg Agents | Avg Duration |
|------------|-------|------------|--------------|
| Simple | 45 | 1.0 | 3 min |
| Medium | 28 | 2.1 | 15 min |
| Complex | 12 | 3.4 | 45 min |
```

## Data Collection

Metrics are derived from:

1. **Session checkpoints** (`.checkpoints/`)
   - Agent invocations
   - Task completion status
   - Duration estimates

2. **Git history**
   - Files modified per session
   - Commit patterns

3. **TodoWrite history**
   - Task completion rates
   - Task complexity

## Output Format

### Summary View (default)
```
/metrics
```

```markdown
## Agent Metrics Summary

Top Agents (This Week):
1. python-developer: 12 tasks, 94% success
2. sql-specialist: 8 tasks, 100% success
3. documenter: 6 tasks, 100% success

Collaboration Score: 2.1 agents/task average
Total Tasks: 26
Success Rate: 96%
```

### Detailed View
```
/metrics --detailed
```

Shows full breakdown of all metrics categories.

### Agent-Specific View
```
/metrics --agent python-developer
```

Shows detailed metrics for a specific agent.

## Improvement Insights

Based on metrics, generate insights:

```markdown
## Recommendations

### High-Impact
- **airflow-specialist** has lower success rate (87%)
  - Review recent failures for patterns
  - Consider enhancing error handling prompts

### Optimization
- **python-developer** frequently followed by **documenter**
  - Consider adding documentation prompt to python-developer
  - Or create combined workflow template

### Underutilized
- **aws-specialist** used only 3 times
  - May indicate team doesn't need or doesn't know about it
  - Consider promoting or deprecating
```

## Implementation Notes

Since this is a prompt-only plugin, metrics collection happens through:

1. Manual tracking in checkpoints
2. Analysis of git history
3. Session summaries

For automated metrics, consider:
- MCP server for persistent storage
- Integration with Langfuse/observability tools
- Hook-based event logging
