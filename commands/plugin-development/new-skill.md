---
name: new-skill
description: Create a new SKILL.md reference for the plugin
arguments:
  - name: name
    description: Skill name (lowercase-hyphenated, e.g., cicd-patterns)
    required: true
---

# Create New Skill

Generate a new SKILL.md reference file with patterns and best practices.

## Usage

```
/new-skill <name>
/new-skill cicd-patterns
/new-skill cost-optimization
/new-skill security-scanning
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `name` | Yes | - | Skill name in lowercase-hyphenated format |

## Generated Output

```
skills/{name}/SKILL.md
```

## Agent Assignment

This command uses the **plugin-developer** agent.

## What Gets Created

The skill will contain:

1. **Overview Section**
   - What patterns this skill covers

2. **Main Content**
   - Comparison tables for options
   - Decision frameworks
   - Code examples

3. **Anti-Patterns**
   - Common mistakes and corrections

4. **Best Practices**
   - Recommended approaches

5. **Research Tools**
   - Relevant tools and libraries to verify

## Example Output

```markdown
# CI/CD Patterns

Reference patterns for CI/CD pipeline design and optimization.

---

## Pipeline Architecture

### Comparison Table

| Approach | Best For | Trade-offs |
|----------|----------|------------|
| Monorepo pipeline | Coordinated releases | Complex configuration |
| Per-service pipelines | Independent deployment | Duplication |

### GitHub Actions Example

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      ...
```

---

## Anti-Patterns

### No Caching
- **What it is**: Rebuilding everything from scratch
- **Why it's wrong**: Wastes time and resources
- **Correct approach**: Cache dependencies and build outputs

---

## Best Practices

1. **Fast feedback**: Run fastest tests first
2. **Parallelization**: Run independent jobs concurrently

---

## Research Tools

| Tool | Use For |
|------|---------|
| `mcp__exa__get_code_context_exa` | Pipeline examples |
```

## Workflow

1. Research the pattern domain
2. Identify key comparisons/trade-offs
3. Find real-world examples
4. Document anti-patterns
5. Create the skill file

## See Also

- `/new-agent` - Create agents that reference this skill
- `skills/plugin-development-patterns/SKILL.md` - Skill template reference
