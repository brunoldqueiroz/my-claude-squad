---
name: validate-plugin
description: Validate plugin structure and all files
arguments: []
---

# Validate Plugin

Validate the entire plugin structure, checking all agents, skills, and commands.

## Usage

```
/validate-plugin
```

## Agent Assignment

This command uses the **plugin-developer** agent.

## What Gets Validated

### Agent Validation

| Check | Severity | Description |
|-------|----------|-------------|
| YAML valid | Error | Frontmatter must parse correctly |
| Name format | Error | Must be lowercase-hyphenated |
| Description examples | Warning | Should have `<example>` blocks |
| Model valid | Error | Must be opus/sonnet/haiku |
| Color valid | Warning | Should be a known color |
| RESEARCH-FIRST section | Warning | Should exist |
| CONTEXT RESILIENCE section | Warning | Should exist |
| MEMORY INTEGRATION section | Warning | Should exist |

### Skill Validation

| Check | Severity | Description |
|-------|----------|-------------|
| File location | Error | Must be skills/*/SKILL.md |
| Has overview | Warning | Should describe patterns |
| Has tables | Warning | Should have comparison tables |
| Has code examples | Warning | Should have runnable code |
| Has anti-patterns | Warning | Should document what to avoid |

### Command Validation

| Check | Severity | Description |
|-------|----------|-------------|
| YAML valid | Error | Frontmatter must parse correctly |
| In category dir | Error | Must be in commands/*/ |
| Has usage | Warning | Should show syntax |
| Has agent assignment | Warning | Should specify agent |

### Structure Validation

| Check | Severity | Description |
|-------|----------|-------------|
| plugin.json exists | Error | Required for plugin |
| README.md exists | Warning | Should document plugin |
| CLAUDE.md exists | Warning | Should have project instructions |

## Output Format

```markdown
# Plugin Validation Report

## Summary
- Errors: [count]
- Warnings: [count]
- Files checked: [count]

## Errors

### agents/broken-agent.md
- ❌ YAML frontmatter invalid: missing 'name' field

### commands/bad-category/missing.md
- ❌ Not in valid category directory

## Warnings

### agents/incomplete-agent.md
- ⚠️ Missing RESEARCH-FIRST PROTOCOL section
- ⚠️ No <example> blocks in description

### skills/old-skill/SKILL.md
- ⚠️ No anti-patterns section

## Passed

✅ 17 agents valid
✅ 8 skills valid
✅ 24 commands valid
✅ Plugin structure valid
```

## Example Output

```markdown
# Plugin Validation Report

## Summary
- Errors: 0
- Warnings: 2
- Files checked: 49

## Warnings

### agents/git-commit-writer.md
- ⚠️ Uses haiku model (verify this is intentional for simple task)

### skills/documentation-templates/SKILL.md
- ⚠️ No anti-patterns section found

## Passed

✅ 19 agents valid
✅ 9 skills valid
✅ 26 commands valid
✅ Plugin structure valid
✅ README.md exists
✅ CLAUDE.md exists
✅ plugin.json valid

## Recommendations

1. Consider adding anti-patterns to documentation-templates skill
2. All agents have required sections
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed (warnings ok) |
| 1 | Errors found |

## See Also

- `/plugin-status` - Quick statistics
- `/update-readme` - Fix README if outdated
