---
description: Run a comprehensive audit of the my-claude-squad plugin
argument-hint: <scope (quick|deep|specific-component)>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - mcp__squad__get_metrics
  - mcp__squad__get_events
  - mcp__squad__get_agent_health
  - mcp__squad__memory_query
agent: squad-orchestrator
---

# Audit Plugin

Run a comprehensive audit of the my-claude-squad plugin to identify issues and improvement opportunities.

## Usage

```
/audit-plugin quick            # 5-10 minute structure and test check
/audit-plugin deep             # Full audit with recommendations
/audit-plugin routing          # Audit routing rules specifically
/audit-plugin agents           # Audit agent prompt quality
/audit-plugin tests            # Audit test coverage
```

## Audit Scopes

### Quick Audit (5-10 minutes)

1. **Structure Validation**
   - Check plugin.json integrity
   - Verify all agents have required sections
   - Check command YAML frontmatter
   - Validate skill structure

2. **Test Health**
   ```bash
   uv run pytest --tb=no -q
   ```

3. **Coverage Check**
   ```bash
   uv run pytest --cov=orchestrator --cov-report=term-missing
   ```

4. **Error Patterns**
   - Query `get_events` for recent failures
   - Check `get_metrics` for anomalies

### Deep Audit (30+ minutes)

1. **Orchestrator Analysis**
   - Review coordinator.py routing coverage
   - Analyze decomposition quality
   - Check error handling paths
   - Review memory growth patterns

2. **Agent Analysis**
   - Check each agent for required sections
   - Verify trigger keyword coverage
   - Review model tier assignments
   - Check for missing examples

3. **Test Analysis**
   - Unit test coverage percentage
   - Integration test coverage
   - Missing test types
   - Edge case coverage

4. **Documentation**
   - README accuracy
   - CLAUDE.md completeness
   - Agent descriptions
   - Command documentation

## Output Format

```markdown
## Plugin Audit Report

### Summary
- Files audited: [count]
- Issues found: [count by severity]
- Recommendations: [count]

### Structure Analysis
- [ ] plugin.json valid
- [ ] All agents have required sections
- [ ] Commands have proper frontmatter
- [ ] Skills follow pattern

### Orchestrator Analysis
- Routing rules coverage: [percentage]
- Decomposition quality: [assessment]
- Error handling: [assessment]
- Memory patterns: [assessment]

### Agent Analysis
- Total agents: [count]
- Missing sections: [list]
- Trigger coverage: [percentage]
- Model tier issues: [list]

### Test Analysis
- Unit coverage: [percentage]
- Integration coverage: [percentage]
- Missing test types: [list]
- Critical gaps: [list]

### Recommendations
1. [Priority 1 - Critical]
2. [Priority 2 - Important]
3. [Priority 3 - Nice to have]

### EXECUTION INSTRUCTIONS
[If issues found, provide fix instructions]
```

## Reference

See `skills/self-improvement-patterns/SKILL.md` for:
- Audit framework details
- Quality checklists
- Common issue patterns
