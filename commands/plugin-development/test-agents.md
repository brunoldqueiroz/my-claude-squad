---
description: Run the agent test suite to validate all agent configurations
agent: plugin-developer
---

# Test Agents

Run the agent test suite to validate all agent configurations.

## Usage

```
/test-agents [options]
```

## Options

- `--verbose` - Show detailed test output
- `--coverage` - Include coverage report
- `--fix` - Attempt to auto-fix common issues (not implemented)

## Process

1. **Install test dependencies** (if needed):
   ```bash
   pip install pytest pyyaml
   ```

2. **Run pytest**:
   ```bash
   pytest tests/test_agents.py -v
   ```

3. **Review results**:
   - All tests should pass
   - Warnings indicate potential issues (not failures)
   - Failures must be fixed before committing

## What Gets Tested

### Frontmatter Validation
- Required fields: `name`, `description`, `model`, `color`
- Valid model values: `sonnet`, `opus`, `haiku`
- Valid color values: terminal colors
- Name matches filename

### Tool Configuration
- `tools` field exists
- `permissionMode` field exists
- Read tool always present
- Edit tool for writing agents
- MCP tools follow `mcp__<server>` format

### Triggers
- Triggers defined for each agent
- Lowercase trigger keywords
- No critical overlaps

### Content Quality
- Prompt body exists (>100 chars)
- Role/persona definition present
- Expertise section documented
- Usage examples in description

### Consistency
- No duplicate agent names
- Consistent structure across agents

## Example Output

```
tests/test_agents.py::TestAgentFrontmatter::test_agent_has_required_fields[python-developer] PASSED
tests/test_agents.py::TestAgentFrontmatter::test_agent_has_valid_model[python-developer] PASSED
tests/test_agents.py::TestAgentTools::test_agent_has_tools_field[python-developer] PASSED
...
========================= 85 passed in 0.42s =========================
```

## Fixing Common Issues

### Missing `tools` field
Add to agent frontmatter:
```yaml
tools: Read, Edit, Write, Bash, Grep, Glob, mcp__exa, mcp__upstash-context7-mcp
```

### Missing `permissionMode`
Add to agent frontmatter:
```yaml
permissionMode: acceptEdits
```

### Invalid model
Use one of: `sonnet`, `opus`, `haiku`

### Missing examples
Add `<example>` tags to description:
```yaml
description: |
  Agent description here.

  <example>
  Context: When to use
  user: "User request"
  assistant: "Agent response"
  </example>
```
