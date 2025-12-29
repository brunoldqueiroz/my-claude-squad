---
name: self-improvement-patterns
description: Reference patterns for auditing, analyzing, and improving the my-claude-squad prompt library.
---

# Self-Improvement Patterns

Reference patterns for continuous improvement of the my-claude-squad prompt library across agents, skills, commands, and documentation.

> **Note**: As of v0.2.0, this is a prompt-only library. The custom MCP orchestrator was removed and archived as `v0.1.0-custom-orchestrator`.

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

### Required Agent Sections

Every agent file must include:

1. **YAML Frontmatter**
   - `name:` - Agent identifier
   - `description:` - With `<example>` tags
   - `model:` - opus, sonnet, or haiku
   - `color:` - Unique color assignment
   - `triggers:` - Keyword list for routing

2. **Core Expertise** - Domain knowledge tables and patterns

3. **RESEARCH-FIRST PROTOCOL** - When to verify knowledge

4. **CONTEXT RESILIENCE** - Checkpoint and recovery format

5. **MEMORY INTEGRATION** - Codebase-first workflow

### Model Tier Review

| Tier | Purpose | Criteria |
|------|---------|----------|
| opus | Orchestration | Multi-agent coordination, complex decomposition |
| sonnet | Specialists | Technical experts, implementation tasks |
| haiku | Utilities | Simple tasks, quick responses |

---

## Skill Quality Standards

### Required Skill Sections

| Section | Purpose |
|---------|---------|
| YAML Frontmatter | Name and description |
| Overview | What the skill covers |
| Comparison Tables | Decision support |
| Code Examples | Runnable patterns |
| Anti-Patterns | What to avoid |
| Best Practices | What to do |
| Research Tools | MCP tools for verification |

### Research Tools Template

```markdown
## Research Tools

| Tool | Use For |
|------|---------|
| `mcp__upstash-context7-mcp__get-library-docs` | Library documentation |
| `mcp__exa__get_code_context_exa` | Code examples and patterns |

### Libraries to Always Verify

- `library-name` - Reason to verify (API changes, version differences)
```

---

## Command Standards

### Required Command Frontmatter

```yaml
---
name: command-name
description: What the command does
arguments:
  - name: arg_name
    description: What this argument is
    required: true | false
    default: "default_value"
agent: specialist-name
---
```

### Command Quality Checklist

- [ ] Has `name:` field matching filename
- [ ] Has `description:` field
- [ ] Uses `arguments:` array (not `argument-hint:`)
- [ ] No `allowed-tools:` (deprecated)
- [ ] Has `agent:` field specifying handler
- [ ] Body includes usage examples
- [ ] Output format documented

---

## Coverage Analysis

### Agent Coverage by Domain

| Domain | Agents | Gap Analysis |
|--------|--------|--------------|
| Data Engineering | 6 | dbt-specialist? |
| Cloud & DevOps | 3 | Complete |
| AI Engineering | 4 | MLOps? |
| Dev Tools | 3 | Complete |
| Coordination | 1 | Complete |

### Skill Coverage

| Category | Skills | Gap Analysis |
|----------|--------|--------------|
| Patterns | 5 | Complete |
| Standards | 2 | Complete |
| Templates | 1 | Complete |
| Research | 2 | Complete |

### Command Coverage

| Category | Commands | Gap Analysis |
|----------|----------|--------------|
| orchestration | 3 | Workflow visualization? |
| data-engineering | 3 | Schema evolution? |
| devops | 3 | CI/CD integration? |
| documentation | 3 | Changelog? |
| ai-engineering | 5 | Evaluation? |
| plugin-development | 10+ | Complete |
| research | 1 | Complete |

---

## Audit Framework

### Quick Audit (5-10 minutes)

```bash
# 1. Count components
ls agents/*.md | wc -l      # Should be 17
ls skills/*/SKILL.md | wc -l # Should be 10
find commands -name "*.md" | wc -l  # Should be 30

# 2. Check agent structure
for f in agents/*.md; do
  grep -q "RESEARCH-FIRST PROTOCOL" "$f" || echo "Missing research: $f"
  grep -q "CONTEXT RESILIENCE" "$f" || echo "Missing resilience: $f"
  grep -q "MEMORY INTEGRATION" "$f" || echo "Missing memory: $f"
done

# 3. Check command frontmatter
grep -l "allowed-tools:" commands/*/*.md  # Should return empty
grep -l "argument-hint:" commands/*/*.md  # Should return empty (deprecated)
```

### Deep Audit Template

```markdown
## Audit Report

### Summary
- Files audited: [count]
- Issues found: [count by severity]
- Recommendations: [count]

### Agent Analysis
- Total agents: [count]
- Missing sections: [list]
- Color conflicts: [list]

### Skill Analysis
- Total skills: [count]
- Missing Research Tools: [list]
- Obsolete references: [list]

### Command Analysis
- Total commands: [count]
- Using deprecated fields: [list]
- Missing agent assignment: [list]

### Recommendations
1. [Priority 1 - Critical]
2. [Priority 2 - Important]
3. [Priority 3 - Nice to have]
```

---

## Anti-Patterns

### 1. Obsolete References

- **What it is**: Referencing removed files or features
- **Why it's wrong**: Confuses users and AI agents
- **Correct approach**: Keep all references current with architecture

### 2. Inconsistent Frontmatter

- **What it is**: Different formats across similar files
- **Why it's wrong**: Reduces parseability and tooling support
- **Correct approach**: Standardize on one format, document it

### 3. Missing Research Sections

- **What it is**: Agent/skill without research protocol
- **Why it's wrong**: Leads to outdated or incorrect information
- **Correct approach**: Always include when to verify knowledge

### 4. Over-Engineering Improvements

- **What it is**: Adding complexity for simple problems
- **Why it's wrong**: Increases maintenance burden
- **Correct approach**: Start simple, iterate based on need

---

## Improvement Workflow

### Phase 1: Discovery

1. Run quick audit commands
2. Check for deprecated fields
3. Identify missing sections
4. Document findings

### Phase 2: Planning

1. Categorize issues by component type
2. Prioritize by impact
3. Group related changes
4. Estimate scope

### Phase 3: Implementation

1. Start with highest-impact changes
2. Follow existing patterns
3. Use parallel execution where possible
4. Validate each change

### Phase 4: Validation

1. Re-run audit commands
2. Check counts match expected
3. Verify no regressions
4. Update documentation

---

## Research Tools

| Tool | Use For |
|------|---------|
| `mcp__upstash-context7-mcp__get-library-docs` | MCP server documentation |
| `mcp__exa__get_code_context_exa` | Prompt engineering patterns |
| `Glob` | Find files by pattern |
| `Grep` | Search file contents |
| `Read` | Examine file structure |

### Useful Searches

```bash
# Find all agents with specific color
grep -l "color: orange" agents/*.md

# Find commands missing name field
for f in commands/*/*.md; do
  grep -q "^name:" "$f" || echo "$f"
done

# Find skills missing Research Tools
for f in skills/*/SKILL.md; do
  grep -q "Research Tools" "$f" || echo "$f"
done
```
