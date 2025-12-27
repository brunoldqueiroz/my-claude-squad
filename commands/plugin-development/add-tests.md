---
description: Identify missing tests and add coverage for the orchestrator
argument-hint: <scope (coverage|unit|integration|edge-cases)>
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
agent: squad-orchestrator
---

# Add Tests

Identify missing tests and add coverage for the orchestrator code.

## Usage

```
/add-tests coverage        # Analyze coverage gaps and prioritize
/add-tests unit            # Add missing unit tests
/add-tests integration     # Add missing integration tests
/add-tests edge-cases      # Add edge case tests for existing code
```

## Current Test Structure

```
tests/
├── unit/              # Module-specific tests
│   ├── test_agent_registry.py
│   ├── test_coordinator.py
│   ├── test_scheduler.py
│   ├── test_memory.py
│   ├── test_events.py
│   ├── test_metrics.py
│   ├── test_retry.py
│   ├── test_config.py
│   ├── test_agent_state.py
│   └── test_server.py
├── integration/       # Cross-module tests
│   └── test_mcp_tools.py
└── fixtures/          # Test data
```

## Test Types Needed

| Type | Purpose | Priority |
|------|---------|----------|
| Unit (edge cases) | Boundary conditions | High |
| Integration | MCP tool chains | High |
| End-to-end | Full workflows | Medium |
| Property | Invariant verification | Low |
| Chaos | Failure injection | Low |

## Analysis Steps

### Coverage Mode

1. **Run Coverage Report**
   ```bash
   uv run pytest --cov=orchestrator --cov-report=term-missing
   ```

2. **Identify Gaps**
   - Lines not covered
   - Branches not tested
   - Functions with low coverage

3. **Prioritize by Risk**
   - Core routing logic (HIGH)
   - Error handling paths (HIGH)
   - Edge cases in scheduling (MEDIUM)
   - Utility functions (LOW)

### Unit Mode

Focus on:
1. Error handling branches
2. Edge cases in routing
3. Circuit breaker state transitions
4. Event handler chains

### Integration Mode

Focus on:
1. MCP tool chains
2. Database operations
3. Multi-component workflows

### Edge Cases Mode

Focus on:
1. Empty inputs
2. Maximum limits
3. Concurrent operations
4. Timeout scenarios

## Output Format

```markdown
## Test Coverage Report

### Current Coverage
- Overall: [percentage]
- coordinator.py: [percentage]
- scheduler.py: [percentage]
- memory.py: [percentage]

### Coverage Gaps

| Module | Function | Lines Missing | Priority |
|--------|----------|---------------|----------|
| coordinator.py | route_task | 45-52 | High |
| scheduler.py | _handle_failure | 78-89 | High |

### Tests to Add

#### High Priority
1. test_coordinator.py:
   - test_route_task_unknown_domain
   - test_decompose_empty_task

2. test_scheduler.py:
   - test_circuit_breaker_half_open_success
   - test_circuit_breaker_half_open_failure

#### Medium Priority
[list]

### Implementation Order
1. [First test file to create/modify]
2. [Second test file]
3. ...

---
## EXECUTION INSTRUCTIONS

1. **INVOKE**: `python-developer`
   **TASK**: Add high-priority unit tests
   **PROMPT**: Add these tests to tests/unit/test_coordinator.py:
   [specific test implementations]

2. **INVOKE**: `python-developer`
   **TASK**: Add integration tests
   **DEPENDS ON**: Step 1
   **PROMPT**: Add integration tests for MCP tool chains
```

## Test Patterns

### Unit Test Template

```python
import pytest
from orchestrator.module import function_to_test

class TestFunctionName:
    """Tests for function_to_test."""

    def test_happy_path(self):
        """Test normal operation."""
        result = function_to_test(valid_input)
        assert result == expected

    def test_edge_case_empty(self):
        """Test with empty input."""
        result = function_to_test("")
        assert result == expected_empty

    def test_error_handling(self):
        """Test error case."""
        with pytest.raises(ExpectedError):
            function_to_test(invalid_input)
```

### Integration Test Template

```python
import pytest
from orchestrator.server import create_app

class TestMCPToolChain:
    """Integration tests for MCP tool workflows."""

    @pytest.fixture
    def app(self):
        return create_app()

    def test_route_then_spawn(self, app):
        """Test routing followed by spawning."""
        route_result = app.route_task("spark query")
        assert route_result["agent"] == "spark-specialist"

        spawn_result = app.spawn_agent(
            route_result["agent"],
            "Write spark query"
        )
        assert spawn_result["task_id"] is not None
```

## Reference

See `skills/self-improvement-patterns/SKILL.md` for:
- Test coverage improvement patterns
- Test types and priorities
- Coverage improvement workflow
