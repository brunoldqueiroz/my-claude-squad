# Developer Guide

This guide explains how to extend my-claude-squad with new agents, skills, commands, and MCP tools.

## Adding a New Agent

Agents are markdown files in the `agents/` directory.

### 1. Create the Agent File

```bash
touch agents/my-new-agent.md
```

### 2. Define the Agent Structure

```markdown
---
name: my-new-agent
description: |
  Use this agent for [specific domain] tasks.

  Examples:
  <example>
  Context: User needs [specific task]
  user: "Request that triggers this agent"
  assistant: "I'll use my-new-agent to handle this."
  <commentary>Matches because of [specific keywords]</commentary>
  </example>
model: sonnet
color: cyan
---

## Your Role

You are the **my-new-agent** specialist. Your responsibility is [core expertise].

## Core Expertise

| Technology | Expertise Level |
|------------|-----------------|
| Tool A | Expert |
| Tool B | Advanced |

## Implementation Patterns

### Pattern 1: [Common Use Case]

```python
# Example code
```

## Best Practices

**DO:**
- Best practice 1
- Best practice 2

**DON'T:**
- Anti-pattern 1
- Anti-pattern 2

## RESEARCH-FIRST PROTOCOL

### Libraries to Verify
- Library A: [what to check]
- Library B: [what to check]

### Research Workflow
1. Use Context7 for official documentation
2. Use Exa for code examples
3. Verify syntax before implementation

## CONTEXT RESILIENCE

### Checkpoint Format
```
## [Task] Progress

### Completed
- [x] Step 1

### Current File
- path/to/file.py

### Next Steps
- [ ] Remaining work
```

### Recovery Protocol
If context is compacted, read the last checkpoint and continue from there.

## MEMORY INTEGRATION

Before implementing, check:
1. Similar patterns in codebase
2. Existing utilities
3. Project conventions
```

### 3. Register with Routing

Add keyword rules to `orchestrator/coordinator.py`:

```python
routing_rules = {
    # ... existing rules ...
    "my-keyword": "my-new-agent",
    "another-keyword": "my-new-agent",
}
```

### 4. Test the Agent

```python
from orchestrator.coordinator import Coordinator

coordinator = Coordinator(agents_dir, memory)
result = coordinator.route_task("task with my-keyword")
assert result.agent == "my-new-agent"
```

## Adding a New Skill

Skills are reference documents in `skills/` directories.

### 1. Create the Skill Directory

```bash
mkdir -p skills/my-skill
```

### 2. Create SKILL.md

```markdown
# My Skill

This skill provides patterns for [domain].

## Overview

Brief description of the skill's purpose.

## Key Patterns

### Pattern 1: [Name]

**When to Use:** [Context]

**Implementation:**
```python
# Example code
```

**Best Practices:**
- Practice 1
- Practice 2

### Pattern 2: [Name]

...

## Common Mistakes

1. **Mistake 1:** [Description]
   - **Solution:** [How to fix]

2. **Mistake 2:** [Description]
   - **Solution:** [How to fix]

## Related Resources

- Link to documentation
- Link to examples
```

Skills are automatically served via `squad://skills/{name}`.

## Adding a New Command

Commands are markdown templates in `commands/` directories.

### 1. Create the Command File

```bash
mkdir -p commands/my-category
touch commands/my-category/my-command.md
```

### 2. Define the Command

```markdown
---
description: Brief description of what this command does
argument-hint: <expected arguments>
allowed-tools:
  - Bash
  - Read
  - Write
---

# My Command

## Purpose

What this command accomplishes.

## Steps

1. Step 1
2. Step 2
3. Step 3

## Examples

### Example 1: Basic Usage

```bash
/my-command arg1 arg2
```

Expected output:
- Result 1
- Result 2
```

Commands are served via `squad://commands/{category}/{name}`.

## Adding a New MCP Tool

MCP tools are Python functions in `orchestrator/server.py`.

### 1. Add the Tool Function

```python
@mcp.tool()
def my_new_tool(
    param1: str,
    param2: int = 10,
    optional_param: str | None = None
) -> dict:
    """
    Brief description of what this tool does.

    Longer description with usage details.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        optional_param: Description of optional param

    Returns:
        Dict with success status and results
    """
    try:
        # Implementation
        result = do_something(param1, param2)

        return {
            "success": True,
            "result": result,
            "message": "Operation completed"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Suggestion for fixing the error"
        }
```

### 2. Add Tests

Create tests in `tests/unit/test_server.py`:

```python
def test_my_new_tool_success():
    result = my_new_tool("value1", 20)
    assert result["success"] is True
    assert "result" in result

def test_my_new_tool_error():
    result = my_new_tool("invalid")
    assert result["success"] is False
    assert "error" in result
```

### 3. Document the Tool

Add to `docs/api-reference.md`:

```markdown
### my_new_tool

Brief description.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| param1 | string | Yes | Description |
| param2 | integer | No | Description (default: 10) |

**Returns:**
```json
{
  "success": true,
  "result": "..."
}
```
```

## Adding a New Hook

Hooks intercept operations before/after execution.

### 1. Define the Hook Handler

```python
from orchestrator.hooks import HooksManager, HookType, HookContext, HookAbortError

def my_hook_handler(ctx: HookContext) -> dict | None:
    """
    Process the hook context.

    Returns:
        None to pass through, or dict to modify data

    Raises:
        HookAbortError to abort the operation
    """
    # Access the data
    data = ctx.data

    # Validate
    if not data.get("required_field"):
        raise HookAbortError("required_field is missing")

    # Modify (optional)
    modified = {**data, "added_field": "value"}
    return modified
```

### 2. Register the Hook

```python
hooks_manager = get_hooks_manager()
hooks_manager.register(
    name="my-hook",
    hook_type=HookType.PRE_TASK,
    handler=my_hook_handler,
    priority=10  # Lower = earlier
)
```

### 3. Hook Types

| Type | When Called |
|------|-------------|
| `PRE_TASK` | Before task execution |
| `POST_TASK` | After task execution |
| `PRE_SPAWN` | Before agent spawn |
| `POST_SPAWN` | After agent spawn |
| `ON_AGENT_ERROR` | When agent fails |
| `PRE_SESSION` | Before session creation |
| `POST_SESSION` | After session completion |
| `ON_SESSION_PAUSE` | When session paused |
| `ON_SESSION_RESUME` | When session resumed |
| `PRE_ROUTE` | Before routing decision |
| `POST_ROUTE` | After routing decision |
| `PRE_MEMORY_STORE` | Before memory storage |
| `POST_MEMORY_QUERY` | After memory query |

## Adding a New Swarm Topology

Topologies are defined in `orchestrator/topology.py`.

### 1. Add the Topology Type

```python
class TopologyType(str, Enum):
    HIERARCHICAL = "hierarchical"
    MESH = "mesh"
    RING = "ring"
    STAR = "star"
    MY_TOPOLOGY = "my_topology"  # Add here
```

### 2. Implement Creation Logic

```python
def _create_my_topology(
    self,
    swarm_id: str,
    name: str,
    agents: list[str],
    coordinator: str | None
) -> Swarm:
    """Create swarm with my topology pattern."""
    members = []

    for agent in agents:
        role = SwarmRole.PEER  # or COORDINATOR/WORKER
        members.append(SwarmMember(
            agent_name=agent,
            role=role,
            # Custom fields for this topology
        ))

    return Swarm(
        id=swarm_id,
        name=name,
        topology=TopologyType.MY_TOPOLOGY,
        members=members,
        active=True
    )
```

### 3. Implement Delegation Logic

```python
def _get_my_topology_target(
    self,
    swarm: Swarm,
    from_agent: str,
    task_description: str
) -> str | None:
    """Get delegation target for my topology."""
    # Custom routing logic
    return target_agent
```

### 4. Implement Workflow Generation

```python
def _create_my_topology_workflow(
    self,
    swarm: Swarm,
    task_description: str
) -> list[dict]:
    """Generate workflow tasks for my topology."""
    tasks = []
    # Generate tasks based on topology pattern
    return tasks
```

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=orchestrator --cov-report=html

# Specific file
uv run pytest tests/unit/test_server.py -v

# By pattern
uv run pytest -k "test_route"
```

### Writing Tests

```python
import pytest
from orchestrator.coordinator import Coordinator
from orchestrator.memory import SwarmMemory

@pytest.fixture
def coordinator(tmp_path):
    """Create test coordinator with temp database."""
    memory = SwarmMemory(tmp_path / "test.duckdb")
    return Coordinator(agents_dir="agents", memory=memory)

def test_route_task(coordinator):
    """Test task routing."""
    result = coordinator.route_task("optimize snowflake query")
    assert result.agent == "snowflake-specialist"

def test_route_task_fallback(coordinator):
    """Test fallback routing."""
    result = coordinator.route_task("unknown task type")
    assert result.agent == "squad-orchestrator"
```

## Code Style

### Python Conventions

- Use type hints for all function parameters and returns
- Use Pydantic models for complex data structures
- Follow PEP 8 naming conventions
- Use docstrings with Args/Returns format

### Agent File Conventions

- Use lowercase hyphenated names
- Include `<example>` tags for trigger extraction
- Include RESEARCH-FIRST PROTOCOL section
- Include CONTEXT RESILIENCE section

### Documentation Conventions

- Use GitHub-flavored Markdown
- Include code examples
- Use tables for structured data
- Keep line length under 100 characters

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Database

```python
import duckdb

conn = duckdb.connect(".swarm/memory.duckdb")
conn.execute("SELECT * FROM agent_runs").fetchall()
```

### Test MCP Server Directly

```bash
uv run squad-mcp
# Type JSON-RPC messages on stdin
```

## Common Issues

### Agent Not Found

Check that:
1. Agent file exists in `agents/`
2. YAML frontmatter has correct `name` field
3. File extension is `.md`

### Routing Not Working

Check that:
1. Keywords are in `routing_rules` dict
2. `<example>` tags contain trigger words
3. Agent name matches file name

### Hooks Not Executing

Check that:
1. Hook is registered (use `list_hooks`)
2. Hook is enabled (use `enable_hook`)
3. Hook type matches the operation

### Semantic Search Failing

Check that:
1. `sentence-transformers` is installed: `uv sync --extra semantic`
2. Model was downloaded (first use downloads ~80MB)
3. Value is not empty when storing
