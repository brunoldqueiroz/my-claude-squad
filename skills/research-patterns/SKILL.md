---
name: research-patterns
description: Research-first protocols, uncertainty handling, and Context7/Exa usage patterns for all agents.
---

# Research Patterns Skill

Guidelines for agents to research effectively and handle uncertainty.

## Research-First Protocol

Before providing solutions, agents MUST:

### 1. Assess Confidence

Ask yourself:
- Do I have up-to-date knowledge about this library/API?
- Could the syntax or best practices have changed recently?
- Am I making assumptions that should be verified?

### 2. Research When Uncertain

Use these tools in order of preference:

| Tool | Use Case | Example |
|------|----------|---------|
| `mcp__upstash-context7-mcp__resolve-library-id` | Find library ID | Search "pandas" |
| `mcp__upstash-context7-mcp__get-library-docs` | Get library docs | Get pandas DataFrame docs |
| `mcp__exa__get_code_context_exa` | Code examples | "pandas merge dataframes examples" |
| `WebSearch` | Latest practices | "best practices 2025" |
| `WebFetch` | Specific docs | Fetch official documentation |

### 3. Declare Uncertainty

If still uncertain after research:
- State assumptions explicitly
- Ask user for clarification on critical decisions
- Provide options with trade-offs

### 4. Validate Before Recommending

- Check syntax against current documentation
- Verify patterns against best practices
- Include verification steps in output

---

## Decision Framework

| Situation | Action | Reason |
|-----------|--------|--------|
| Library/API syntax | Research (Context7) | APIs change frequently |
| Standard patterns exist | Research (Exa) | Verify best practices |
| Multiple valid approaches | Ask user | Business logic matters |
| Domain-specific question | Research tools | Get current info |
| Business logic unknown | Ask user | Can't assume intent |
| Performance optimization | Research + Validate | Version-specific |

---

## Research Tool Patterns

### Pattern 1: Library Documentation Lookup

```
Step 1: Resolve library ID
  Tool: mcp__upstash-context7-mcp__resolve-library-id
  Input: { "libraryName": "pandas" }
  Output: Library ID like "/pandas/pandas"

Step 2: Get specific documentation
  Tool: mcp__upstash-context7-mcp__get-library-docs
  Input: {
    "context7CompatibleLibraryID": "/pandas/pandas",
    "topic": "merge join",
    "tokens": 5000
  }
  Output: Current documentation with examples
```

### Pattern 2: Code Examples Search

```
Tool: mcp__exa__get_code_context_exa
Input: {
  "query": "FastAPI dependency injection authentication example",
  "tokensNum": 5000
}
Output: Relevant code examples from high-quality sources
```

### Pattern 3: Best Practices Verification

```
Tool: WebSearch
Input: {
  "query": "Snowflake warehouse sizing best practices 2025"
}
Output: Current recommendations and patterns
```

---

## Context Resilience Patterns

### State Preservation

After completing significant work, always output:

```markdown
## Work Summary

**Files Created/Modified:**
- `/path/to/file1.py` (created)
- `/path/to/file2.sql` (modified)

**Current Phase:** [Phase name/number]

**Key Decisions Made:**
- Decision 1: [rationale]
- Decision 2: [rationale]

**Next Steps:**
1. [Next action]
2. [Following action]

**Assumptions Made:**
- Assumption 1 (verified/unverified)
- Assumption 2 (verified/unverified)
```

### Recovery Protocol

If resuming after context loss:

1. Check for status summary at conversation start
2. Look for file references to previous work
3. Read referenced files to understand current state
4. Ask user to confirm current state if unclear

### Checkpoint Pattern

For multi-phase work, create checkpoints:

```markdown
## CHECKPOINT: Phase [N] Complete

### Completed Work
- [x] Task 1
- [x] Task 2

### Artifacts Created
- File: `/path/to/output.py`
- Config: `/path/to/config.yaml`

### State for Next Phase
- Input for Phase [N+1]: [description]
- Dependencies resolved: [list]

### Recovery Instructions
If context is lost, load these files:
1. `/path/to/output.py` - main implementation
2. `/path/to/config.yaml` - configuration
```

---

## Memory Integration Patterns

### Session Memory

Use TodoWrite to track multi-step tasks:
- Create todos for each phase
- Mark as in_progress when starting
- Mark as completed immediately when done
- Add new todos as discovered

### Persistent Memory

Check for project context:
1. Read `CLAUDE.md` for project conventions
2. Read `.claude/` directory for settings
3. Check existing codebase patterns with Grep/Glob

### Knowledge Retrieval Order

Before implementing solutions:
1. **Local First**: Search codebase for similar patterns
2. **Skills Check**: Reference skills directory for templates
3. **External Docs**: Use Context7 for library documentation
4. **Web Search**: For latest best practices

---

## Uncertainty Handling Patterns

### High Confidence (Proceed)

When you can proceed without asking:
- Well-established patterns with clear best practices
- Syntax verified against current documentation
- Similar patterns exist in the codebase
- Request is specific and unambiguous

### Medium Confidence (Research + Declare)

When to research and declare assumptions:
- Library version not specified
- Multiple valid approaches exist
- Performance implications unclear
- Integration with unknown systems

Output format:
```markdown
## Assumptions Made

1. **Assumption**: Using pandas 2.x syntax
   **Rationale**: Current best practice
   **Risk if wrong**: May not work with pandas 1.x

2. **Assumption**: Database supports window functions
   **Rationale**: Standard SQL feature
   **Risk if wrong**: Query will fail
```

### Low Confidence (Ask User)

When to ask the user:
- Business logic decisions
- Technology choice with significant trade-offs
- Security-sensitive implementations
- Cost-impacting decisions
- Irreversible operations

---

## Example: Research Before Implementation

### Scenario: User asks to "optimize a pandas DataFrame operation"

**Step 1: Assess**
- Is this pandas 1.x or 2.x? (Major API differences)
- What operation specifically? (Different optimization strategies)
- What's the data size? (Affects approach)

**Step 2: Research**
```
# Get current pandas best practices
Tool: mcp__upstash-context7-mcp__get-library-docs
Input: {
  "context7CompatibleLibraryID": "/pandas/pandas",
  "topic": "performance optimization",
  "tokens": 5000
}
```

**Step 3: Validate Understanding**
- Check if the existing code uses deprecated patterns
- Verify the optimization applies to their pandas version
- Confirm the approach matches their data size

**Step 4: Provide Solution with Context**
```markdown
## Optimization Recommendation

**Researched**: Current pandas 2.x best practices

**Approach**: [specific optimization]

**Why this works**: [explanation based on docs]

**Verification**: Run this to confirm improvement:
```python
# Timing code here
```

**Assumptions**:
- Using pandas >= 2.0
- Data fits in memory
```

---

## Anti-Patterns to Avoid

1. **Guessing Syntax**
   - DON'T: Assume library syntax from memory
   - DO: Verify with Context7 or documentation

2. **Outdated Patterns**
   - DON'T: Use patterns from training data without verification
   - DO: Check for current best practices

3. **Silent Assumptions**
   - DON'T: Make critical assumptions without stating them
   - DO: Explicitly list assumptions and their risks

4. **Proceeding Without Context**
   - DON'T: Start work without understanding existing patterns
   - DO: Check codebase first for conventions

5. **Losing State**
   - DON'T: Rely on conversation context for important state
   - DO: Reference files and create checkpoints
