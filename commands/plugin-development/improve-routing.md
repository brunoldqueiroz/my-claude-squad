---
description: Analyze and improve the task routing algorithm in coordinator.py
argument-hint: <action (analyze|improve|add-keywords)>
allowed-tools:
  - Read
  - Edit
  - Grep
  - Glob
  - Bash
  - mcp__squad__get_metrics
  - mcp__squad__get_events
  - mcp__squad__memory_query
agent: squad-orchestrator
---

# Improve Routing

Analyze and improve the task routing algorithm in the orchestrator's coordinator.py.

## Usage

```
/improve-routing analyze       # Analyze current routing effectiveness
/improve-routing improve       # Implement routing improvements
/improve-routing add-keywords  # Add missing trigger keywords
```

## What This Command Does

### Analyze Mode

1. **Extract Current Routing Rules**
   - Read `orchestrator/coordinator.py`
   - Count keywords per agent
   - Identify agents with few triggers

2. **Cross-Reference with Agents**
   - Check each agent's `<example>` tags
   - Extract technology keywords from body
   - Compare with routing_rules

3. **Check Historical Data**
   - Query events for routing failures
   - Check metrics for low-confidence routes
   - Identify common unrouted patterns

4. **Generate Gap Report**
   ```markdown
   ## Routing Analysis

   ### Coverage by Agent
   | Agent | Keywords | Examples | Coverage |
   |-------|----------|----------|----------|
   | spark-specialist | 5 | 3 | Good |
   | rag-specialist | 2 | 4 | Low keywords |

   ### Missing Patterns
   - "pyspark" → should route to spark-specialist
   - "vector" → should route to rag-specialist

   ### Low Confidence Routes
   - Complex queries often fall back to orchestrator
   - AI + Data hybrid tasks unclear
   ```

### Improve Mode

1. **Enhance Scoring Algorithm**
   - Implement multi-factor scoring
   - Add weight for keyword match
   - Add weight for description similarity
   - Add weight for historical success

2. **Add Missing Keywords**
   - Based on analysis findings
   - From agent examples
   - From technology documentation

3. **Test Changes**
   - Run existing routing tests
   - Add new test cases for edge cases

### Add-Keywords Mode

Interactive mode to add new routing keywords:

1. Show current keyword list for target agent
2. Suggest keywords from agent body
3. Add user-specified keywords
4. Validate no conflicts with other agents

## Output Format

```markdown
## Routing Improvement Report

### Changes Made
| File | Change | Reason |
|------|--------|--------|
| coordinator.py | Added 12 keywords | Gap analysis |
| coordinator.py | Enhanced scoring | Better multi-domain |

### New Keywords Added
| Agent | Keywords Added |
|-------|----------------|
| spark-specialist | pyspark, rdd, dataframe |
| rag-specialist | vector, embedding, retrieval |

### Test Results
- Existing tests: PASS
- New edge cases: PASS

### Before/After Comparison
- Coverage: 78% → 92%
- Avg confidence: 0.65 → 0.82
```

## Reference

See `skills/self-improvement-patterns/SKILL.md` for:
- Routing enhancement patterns
- Weighted scoring algorithm
- Keyword extraction techniques
