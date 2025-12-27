---
name: plugin-development-patterns
description: Reference patterns for creating agents, skills, and commands for this Claude Code plugin.
---

# Plugin Development Patterns

Reference patterns for creating agents, skills, and commands for this Claude Code plugin.

---

## Agent File Template

### YAML Frontmatter Structure

```yaml
---
name: lowercase-hyphenated-name
description: |
  Brief description of when to use this agent.

  Examples:
  <example>
  Context: [Situation description]
  user: "[User's request]"
  assistant: "I'll use the [agent-name] agent to..."
  <commentary>[Why this agent is appropriate]</commentary>
  </example>

  <example>
  Context: [Different situation]
  user: "[Different request]"
  assistant: "[Response]"
  <commentary>[Explanation]</commentary>
  </example>
model: opus | sonnet | haiku
color: [colorname]
---
```

### Model Selection Criteria

| Model | Use For | Examples |
|-------|---------|----------|
| **opus** | Complex orchestration, multi-agent coordination, planning | planner-orchestrator, ai-orchestrator, plugin-architect |
| **sonnet** | Technical specialists, domain expertise, implementation | python-developer, rag-specialist, sql-specialist |
| **haiku** | Simple, focused tasks with minimal reasoning | git-commit-writer |

### Color Assignments (Used)

| Color | Agents |
|-------|--------|
| blue | planner-orchestrator, snowflake-specialist |
| green | python-developer, llm-specialist |
| cyan | sql-specialist, documenter |
| orange | spark-specialist, agent-framework-specialist |
| yellow | airflow-specialist, automation-specialist |
| red | sql-server-specialist |
| purple | container-specialist, rag-specialist |
| magenta | kubernetes-specialist, ai-orchestrator |
| gray | git-commit-writer |
| pink | plugin-architect |
| white | plugin-developer |

### Agent Content Structure

Every agent MUST follow this structure:

```markdown
---
[YAML Frontmatter]
---

You are a **[Role Title]** specializing in [domain].

## Your Role
[Brief description of responsibilities]

## Core Expertise
[Tables and lists of capabilities]

## Implementation Patterns
[Code templates with real examples]

## Best Practices
[Do's and don'ts]

---

## RESEARCH-FIRST PROTOCOL
[Libraries to verify, research workflow]

---

## CONTEXT RESILIENCE
[Output format for recovery, checkpoint template]

---

## MEMORY INTEGRATION
[Codebase check, skills reference, external docs]
```

---

## Required Agent Sections

### 1. Core Expertise Section

Use tables for technology comparisons:

```markdown
## Core Expertise

| Technology | Proficiency | Use Cases |
|------------|-------------|-----------|
| [Tech 1] | Expert | [When to use] |
| [Tech 2] | Advanced | [When to use] |
```

### 2. Implementation Patterns Section

Include runnable code examples:

```markdown
## Implementation Patterns

### Pattern Name
```python
# Clear, runnable example with:
# - Type hints
# - Docstrings
# - Error handling
def example_function(param: str) -> dict:
    """Description of what this does."""
    return {"result": param}
```

**When to use**: [Situation description]
```

### 3. RESEARCH-FIRST PROTOCOL Section

```markdown
---

## RESEARCH-FIRST PROTOCOL

### Libraries to Verify

| Library | Reason | Action |
|---------|--------|--------|
| `library-name` | API changes frequently | Check Context7 before use |
| `other-lib` | New features added often | Verify current patterns |

### Research Workflow

1. **Assess Confidence**: Is my knowledge current?
2. **Check Context7**: `mcp__upstash-context7-mcp__get-library-docs`
3. **Search Examples**: `mcp__exa__get_code_context_exa`
4. **Web Search**: For latest practices
5. **Codebase First**: Check existing patterns with Grep/Glob

### When to Ask User

- Business logic decisions
- Architecture trade-offs with no clear winner
- Security-sensitive configurations
- External service credentials or endpoints
```

### 4. CONTEXT RESILIENCE Section

```markdown
---

## CONTEXT RESILIENCE

### Output Format

After completing work, output:

```markdown
## CHECKPOINT: [Task Name] Complete

### Completed Work
- [x] [Task 1 description]
- [x] [Task 2 description]

### Artifacts Created
| File | Purpose |
|------|---------|
| `/path/to/file` | [What it does] |

### Recovery Instructions
If context is lost:
1. Read [specific files]
2. Check [specific state]
3. Continue from [specific point]
```

### Recovery Protocol

When resuming after context loss:
1. Look for checkpoint summaries
2. Read TodoWrite for task status
3. Examine referenced files
4. Ask user to confirm state if unclear
```

### 5. MEMORY INTEGRATION Section

```markdown
---

## MEMORY INTEGRATION

### Before Implementation

1. **Codebase First**: Search for similar patterns
   ```
   Grep: "pattern_name"
   Glob: "**/*similar*.py"
   ```

2. **Skills Check**: Reference relevant skills
   - `skills/[relevant-skill]/SKILL.md`

3. **External Docs**: Use research tools
   - Context7 for library docs
   - Exa for code examples

### Session Memory

- Use TodoWrite for multi-step tasks
- Create checkpoint after each phase
- Update todos immediately on completion
```

---

## Skill File Template

### File Location

Skills are stored in: `skills/{skill-name}/SKILL.md`

### Structure

```markdown
# Skill Name

Brief description of what patterns this skill covers.

---

## Section 1: [Main Topic]

### Subsection with Comparison Table

| Option | Best For | Trade-offs |
|--------|----------|------------|
| Option A | [Use case] | [Pros/Cons] |
| Option B | [Use case] | [Pros/Cons] |

### Code Example

```language
// Runnable example with comments
```

---

## Section 2: [Another Topic]

[Content...]

---

## Anti-Patterns

### Anti-Pattern Name
- **What it is**: [Description]
- **Why it's wrong**: [Explanation]
- **Correct approach**: [Solution]

---

## Best Practices

1. **Practice Name**: [Description]
2. **Another Practice**: [Description]

---

## Research Tools

| Tool | Use For |
|------|---------|
| `mcp__upstash-context7-mcp__get-library-docs` | [Library] documentation |
| `mcp__exa__get_code_context_exa` | Code examples |

### Libraries to Always Verify

- `library-name` - [Reason to verify]
```

---

## Command File Template

### File Location

Commands are stored in: `commands/{category}/{command-name}.md`

### Categories

| Category | Purpose |
|----------|---------|
| `orchestration` | Task decomposition, coordination |
| `data-engineering` | ETL, pipelines, queries |
| `devops` | Deployment, containers, k8s |
| `documentation` | Docs, commits, ADRs |
| `research` | Documentation lookup |
| `ai-engineering` | RAG, agents, LLMs |
| `plugin-development` | Plugin extension |

### YAML Frontmatter

```yaml
---
name: command-name
description: What the command does
arguments:
  - name: arg_name
    description: What this argument is
    required: true | false
    default: "default_value"
---
```

### Content Structure

```markdown
# Command Name

Brief description of what this command does.

## Usage

```
/command-name <required-arg> [optional-arg]
/command-name my-value --flag value
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `name` | Yes | - | What it is |
| `option` | No | `default` | What it controls |

## Generated Output

```
project-name/
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
└── README.md
```

## Agent Assignment

This command uses the **[agent-name]** agent.

## Example Output

```python
# Example of what gets generated
```

## Options

| Option | Values | Description |
|--------|--------|-------------|
| `--flag` | value1, value2 | What it does |
```

---

## Example Formatting in Descriptions

### Good Example (follows pattern)

```yaml
description: |
  Use this agent for Python data engineering tasks including ETL scripts, APIs, and testing.

  Examples:
  <example>
  Context: User needs a data transformation script
  user: "Write a Python script to transform CSV to Parquet"
  assistant: "I'll use the python-developer agent for this transformation task."
  <commentary>Data transformation is core Python developer expertise</commentary>
  </example>

  <example>
  Context: User needs API development
  user: "Create a FastAPI endpoint for our data service"
  assistant: "I'll use the python-developer agent to create the API."
  <commentary>API development falls under Python developer scope</commentary>
  </example>
```

### Bad Example (avoid)

```yaml
description: This agent does Python stuff.  # Too vague, no examples
```

---

## Quality Checklist

### Before Creating an Agent

- [ ] Name follows `lowercase-hyphenated` convention
- [ ] Description includes 2-3 `<example>` blocks
- [ ] Model tier is appropriate (opus/sonnet/haiku)
- [ ] Color doesn't conflict with existing agents
- [ ] Core Expertise section has technology tables
- [ ] Implementation Patterns include runnable code
- [ ] RESEARCH-FIRST section lists libraries to verify
- [ ] CONTEXT RESILIENCE includes checkpoint template
- [ ] MEMORY INTEGRATION includes codebase-first workflow

### Before Creating a Skill

- [ ] Name describes the pattern domain
- [ ] Comparison tables for options/trade-offs
- [ ] Code examples are runnable
- [ ] Anti-patterns section exists
- [ ] Research tools section exists

### Before Creating a Command

- [ ] Name is clear and action-oriented
- [ ] Category is appropriate
- [ ] Arguments are well-documented
- [ ] Generated output structure is shown
- [ ] Agent assignment is specified
- [ ] Example output is provided

---

## Critical Rules

### Git Commit Writer Rule

The `git-commit-writer` agent and `/commit` command must **NEVER** include:
- "Generated with Claude Code"
- "Generated by AI"
- "Co-Authored-By: Claude"
- Any mention of Claude, Anthropic, or AI
- Robot emojis or AI-related symbols

Commit messages must appear human-written.

### Research-First Rule

Every agent that works with external libraries MUST:
1. Include a "Libraries to Verify" table
2. List specific tools for research
3. Define when to ask user for clarification

### Context Resilience Rule

Every agent MUST include:
1. A checkpoint output format
2. Recovery instructions
3. File reference patterns

---

## Adding New Domains

When adding a new domain (e.g., "ML Ops"):

### Step 1: Analyze the Domain

- What specialists are needed?
- What skills should they reference?
- What commands would users want?

### Step 2: Create the Skill First

- Define patterns and best practices
- Create decision frameworks
- Document anti-patterns

### Step 3: Create Specialists

- One agent per major responsibility
- Use sonnet for technical work
- Reference the new skill

### Step 4: Create Orchestrator (if needed)

- Only if coordinating multiple specialists
- Use opus model
- Define phase-based workflow

### Step 5: Create Commands

- One command per user action
- Map to appropriate agent
- Define expected outputs

### Step 6: Update Orchestrators

- Add new agents to planner-orchestrator
- Add to ai-orchestrator if AI-related
- Update README.md
