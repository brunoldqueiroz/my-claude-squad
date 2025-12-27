---
name: self-improvement-patterns
description: Reference patterns for auditing, analyzing, and improving the my-claude-squad plugin itself.
---

# Self-Improvement Patterns

Reference patterns for continuous improvement of the my-claude-squad plugin across orchestrator code, agents, commands, skills, and tests.

---

## Orchestrator Code Improvement

### Improvement Areas

| Component | File | Common Issues |
|-----------|------|---------------|
| Task Routing | `coordinator.py` | Hardcoded keywords, missing patterns, low confidence |
| Task Decomposition | `coordinator.py` | Naive splitting, missed dependencies |
| Circuit Breaker | `scheduler.py` | Static thresholds, no per-agent tuning |
| Memory | `memory.py` | Unlimited growth, missing indexes |
| Events | `events.py` | History overflow, missing event types |
| Metrics | `metrics.py` | Incomplete coverage, no alerting |

### Routing Enhancement Pattern

```python
# Before: Hardcoded keyword matching
routing_rules = {
    "snowflake": "snowflake-specialist",
    "spark": "spark-specialist",
}

# After: Weighted multi-factor scoring
def route_task(self, task_description: str) -> Agent | None:
    candidates = []
    for agent in self.registry.list_agents():
        score = self._calculate_match_score(task_description, agent)
        if score > 0.0:
            candidates.append((agent, score))

    if not candidates:
        return self.registry.get_agent("squad-orchestrator")

    return max(candidates, key=lambda x: x[1])[0]

def _calculate_match_score(self, task: str, agent: Agent) -> float:
    score = 0.0
    task_lower = task.lower()

    # Keyword match (weight: 0.4)
    for trigger in agent.triggers:
        if trigger.lower() in task_lower:
            score += 0.4
            break

    # Description similarity (weight: 0.3)
    # Check if key terms from agent description appear in task

    # Example match (weight: 0.2)
    # Check against <example> patterns

    # Historical success rate (weight: 0.1)
    # Query memory for past routing success

    return score
```

### Decomposition Enhancement Pattern

```python
# Before: Naive string splitting
connectors = [" and ", " then ", " with ", ", "]

# After: Phase-aware decomposition
def decompose_task(self, task_description: str) -> list[TaskNode]:
    """Decompose task with dependency awareness."""
    # 1. Identify action verbs
    # 2. Detect temporal dependencies ("then", "after")
    # 3. Detect data dependencies ("using output from")
    # 4. Group related subtasks
    # 5. Assign agents with confidence scores
    # 6. Build dependency graph
    pass
```

---

## Agent Prompt Optimization

### Quality Checklist

| Element | Weight | Criteria |
|---------|--------|----------|
| Role Clarity | 20% | First paragraph defines role clearly |
| Expertise Tables | 15% | Uses tables, not prose |
| Code Examples | 20% | Runnable, typed, documented |
| Research Protocol | 15% | Lists libraries, tools, workflow |
| Context Resilience | 15% | Has checkpoint format |
| Memory Integration | 15% | Codebase-first workflow |

### Trigger Keyword Analysis

```python
def analyze_triggers(agent_file: str) -> dict:
    """Analyze agent trigger effectiveness."""
    content = Path(agent_file).read_text()
    frontmatter, body = parse_frontmatter(content)

    # Extract from <example> tags
    examples = extract_examples(frontmatter.get("description", ""))

    # Extract tech keywords from body
    tech_keywords = extract_tech_keywords(body)

    # Check coverage against routing_rules
    routing_coverage = check_routing_coverage(agent_name)

    return {
        "examples": len(examples),
        "tech_keywords": tech_keywords,
        "routing_coverage": routing_coverage,
    }
```

### Model Tier Review

| Tier | Current Count | Criteria |
|------|---------------|----------|
| opus | 1 (unified) | Only for orchestration |
| sonnet | 15 | Technical specialists |
| haiku | 1 | Simple utilities |

**Review questions:**
- Is any sonnet agent doing simple work that haiku could handle?
- Is any sonnet agent doing orchestration that needs opus?
- Are model assignments documented in the agent?

---

## Command Coverage Analysis

### Coverage by Category

| Category | Commands | Gap Analysis |
|----------|----------|--------------|
| orchestration | plan-task, execute-squad, status | Workflow visualization? |
| data-engineering | create-pipeline, optimize-query, analyze-data | Schema evolution? |
| devops | deploy, containerize, k8s-manifest | CI/CD integration? |
| documentation | doc-pipeline, doc-api, commit | Changelog? |
| ai-engineering | create-rag, create-agent, create-chatbot, create-mcp-server, optimize-rag | Evaluation? |
| plugin-development | new-agent, new-skill, new-command, list-agents, list-commands, validate-plugin, update-readme, plugin-status | Benchmarks? |

### Command Quality Checklist

- [ ] Has YAML frontmatter with arguments
- [ ] Usage section shows examples
- [ ] Generated output structure documented
- [ ] Agent assignment specified
- [ ] Example output provided

---

## Test Coverage Improvement

### Current Test Structure

```
tests/
├── unit/           # Module-specific tests
│   ├── test_agent_registry.py
│   ├── test_coordinator.py
│   ├── test_scheduler.py
│   └── ...
├── integration/    # Cross-module tests
│   └── test_mcp_tools.py
└── fixtures/       # Test data
```

### Test Types Needed

| Type | Purpose | Priority |
|------|---------|----------|
| Unit (edge cases) | Boundary conditions | High |
| Integration | MCP tool chains | High |
| End-to-end | Full workflows | Medium |
| Property | Invariant verification | Low |
| Chaos | Failure injection | Low |

### Coverage Improvement Pattern

```python
# Identify uncovered code
# uv run pytest --cov=orchestrator --cov-report=term-missing

# Focus on:
# 1. Error handling branches
# 2. Edge cases in routing
# 3. Circuit breaker state transitions
# 4. Event handler chains
```

---

## Documentation Standards

### Required Documentation

| Document | Status | Location |
|----------|--------|----------|
| README.md | Required | Root |
| CLAUDE.md | Required | Root |
| Agent READMEs | Optional | Per-agent |
| ADRs | Recommended | docs/adr/ |
| Troubleshooting | Recommended | docs/ |

### README Checklist

- [ ] Overview with key value prop
- [ ] Installation instructions
- [ ] Quick start example
- [ ] Agent list with descriptions
- [ ] Command list with usage
- [ ] Test instructions
- [ ] Architecture overview

---

## Audit Framework

### Quick Audit (5-10 minutes)

```bash
# 1. Structure validation
# Run /validate-plugin

# 2. Test health
uv run pytest --tb=no -q

# 3. Coverage check
uv run pytest --cov=orchestrator --cov-report=term-missing

# 4. Error patterns
# Check get_events for recent failures
```

### Deep Audit (30+ minutes)

```markdown
## Audit Report Template

### Summary
- Files audited: [count]
- Issues found: [count by severity]
- Recommendations: [count]

### Orchestrator Analysis
- Routing rules coverage: [percentage]
- Decomposition quality: [assessment]
- Error handling: [assessment]

### Agent Analysis
- Total agents: [count]
- Missing sections: [list]
- Trigger coverage: [percentage]

### Test Analysis
- Unit coverage: [percentage]
- Integration coverage: [percentage]
- Missing test types: [list]

### Recommendations
1. [Priority 1 - Critical]
2. [Priority 2 - Important]
3. [Priority 3 - Nice to have]
```

---

## Anti-Patterns

### 1. Premature Optimization

- **What it is**: Optimizing before measuring
- **Why it's wrong**: Wastes effort on non-bottlenecks
- **Correct approach**: Profile first, optimize hot paths

### 2. Breaking Changes Without Migration

- **What it is**: Changing interfaces without compatibility
- **Why it's wrong**: Breaks existing usage
- **Correct approach**: Deprecation warnings, migration guides

### 3. Tests After Implementation

- **What it is**: Writing tests after code is complete
- **Why it's wrong**: Misses edge cases, encourages shortcuts
- **Correct approach**: TDD or test alongside implementation

### 4. Over-Engineering Improvements

- **What it is**: Adding complex solutions for simple problems
- **Why it's wrong**: Increases maintenance burden
- **Correct approach**: Start simple, iterate based on need

---

## Improvement Workflow

### Phase 1: Discovery

1. Run automated audits
2. Review metrics and events
3. Identify patterns in failures
4. Document findings

### Phase 2: Planning

1. Categorize issues by domain
2. Prioritize by impact and effort
3. Create dependency graph
4. Estimate scope

### Phase 3: Implementation

1. Start with lowest-risk changes
2. Follow existing patterns
3. Add tests before changing code
4. Document decisions

### Phase 4: Validation

1. Run full test suite
2. Manual testing of changed features
3. Performance comparison
4. Documentation update

---

## Research Tools

| Tool | Use For |
|------|---------|
| `mcp__exa__get_code_context_exa` | Plugin architecture patterns |
| `mcp__upstash-context7-mcp__get-library-docs` | FastMCP, DuckDB, Pydantic |
| `get_metrics` | Performance analysis |
| `get_events` | Failure pattern detection |
| `memory_query` | Historical improvement data |

### Tracking Improvements

```python
# Store improvement findings
memory_store(
    key=f"audit-{datetime.now().strftime('%Y%m%d')}",
    value=json.dumps({
        "issues_found": [...],
        "recommendations": [...],
        "priority_items": [...],
    }),
    namespace="squad-improvement"
)

# Query past improvements
memory_query(
    pattern="%audit%",
    namespace="squad-improvement"
)
```
