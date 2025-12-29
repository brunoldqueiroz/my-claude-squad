---
description: Optimize a specific agent's prompt for better performance
argument-hint: <agent-name>
agent: squad-orchestrator
---

# Improve Agent

Analyze and optimize a specific agent's prompt for better performance, clearer role definition, and improved trigger coverage.

## Usage

```
/improve-agent spark-specialist     # Improve spark-specialist prompt
/improve-agent rag-specialist       # Improve rag-specialist prompt
/improve-agent all                  # Audit all agents (report only)
```

## Quality Checklist

| Element | Weight | Criteria |
|---------|--------|----------|
| Role Clarity | 20% | First paragraph defines role clearly |
| Expertise Tables | 15% | Uses tables, not prose, for capabilities |
| Code Examples | 20% | Runnable, typed, documented examples |
| Research Protocol | 15% | Lists libraries, tools, workflow |
| Context Resilience | 15% | Has checkpoint format section |
| Memory Integration | 15% | Codebase-first workflow documented |

## Analysis Steps

### 1. Read Agent File
- Parse YAML frontmatter
- Check required sections exist
- Extract trigger keywords from examples

### 2. Evaluate Structure
- **YAML frontmatter**: name, description, model, color
- **Core content**: Role definition, expertise areas
- **Required sections**:
  - RESEARCH-FIRST PROTOCOL
  - CONTEXT RESILIENCE
  - MEMORY INTEGRATION

### 3. Check Trigger Coverage
- Count `<example>` tags in description
- Extract technology keywords from body
- Cross-reference with coordinator.py

### 4. Research Current Best Practices
- Use Context7 for library documentation
- Use Exa for latest patterns
- Check if agent knowledge is outdated

### 5. Generate Improvement Plan

```markdown
## Agent Improvement: [agent-name]

### Current Score
- Role Clarity: [score]/20
- Expertise Tables: [score]/15
- Code Examples: [score]/20
- Research Protocol: [score]/15
- Context Resilience: [score]/15
- Memory Integration: [score]/15
- **Total**: [total]/100

### Issues Found
1. [Issue with severity]
2. [Issue with severity]

### Recommended Improvements
1. [Specific improvement]
2. [Specific improvement]

### Example Additions
Add these examples to description:
```
<example>
Context: [scenario]
user: "[query]"
assistant: "[response]"
<commentary>[why this agent]</commentary>
</example>
```

### Keyword Additions
Add to coordinator.py routing_rules:
- "[keyword]" → [agent-name]
```

## Model Tier Review

| Tier | Criteria | Current Agents |
|------|----------|----------------|
| opus | Orchestration only | squad-orchestrator |
| sonnet | Technical specialists | All domain experts |
| haiku | Simple utilities | git-commit-writer |

**Review Questions:**
- Is this agent doing simple work that haiku could handle?
- Is this agent doing orchestration that needs opus?
- Is the model tier documented in the agent?

## Reference

See `skills/self-improvement-patterns/SKILL.md` for:
- Agent prompt optimization checklist
- Trigger keyword analysis patterns
- Model tier guidelines
