# Code Review Cycle

Iterative collaboration pattern for code review and refinement.

## Overview

Use this template when:
- Reviewing and improving existing code
- Iterating on implementation quality
- Ensuring code meets standards before merge

This is an **iterative** pattern where agents may exchange multiple times.

## Agent Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                     REVIEW LOOP                             │
│  ┌───────────────┐        ┌───────────────┐                │
│  │   Specialist  │ ←────→ │ Plugin Dev /  │                │
│  │   (author)    │        │ Reviewer      │                │
│  └───────────────┘        └───────────────┘                │
│         │                         │                         │
│         └────────┬────────────────┘                         │
│                  ↓                                          │
│         Continue until approved                             │
└─────────────────────────────────────────────────────────────┘
```

## Iteration 1: Initial Review

### Reviewer Tasks
1. Read all changed files
2. Check against coding standards
3. Identify issues by category:
   - **Critical**: Security, correctness bugs
   - **Major**: Performance, maintainability
   - **Minor**: Style, naming, comments

### Review Output Format
```markdown
## Code Review: [Component]

### Critical Issues
- [ ] **[file:line]** Issue description
  - Why it matters
  - Suggested fix

### Major Issues
- [ ] **[file:line]** Issue description
  - Suggestion

### Minor Issues
- [ ] **[file:line]** Issue description

### Positive Notes
- Good patterns observed
- Well-structured areas

### Summary
X critical, Y major, Z minor issues found.
Recommendation: [Request Changes / Approve with Comments / Approve]
```

## Iteration 2+: Address Feedback

### Author Tasks
1. Address critical issues first
2. Fix major issues
3. Address or respond to minor issues
4. Explain any disagreements with rationale

### Response Format
```markdown
## Review Response

### Critical Issues
- [x] **[file:line]** Fixed: [description of fix]

### Major Issues
- [x] **[file:line]** Fixed: [description]
- [ ] **[file:line]** Disagreed: [rationale]

### Minor Issues
- [x] **[file:line]** Fixed
- [ ] **[file:line]** Won't fix: [reason]
```

## Quality Gates

### For Approval
- [ ] Zero critical issues
- [ ] Zero unaddressed major issues
- [ ] Minor issues addressed or justified

### Review Checklist by Domain

#### Python Code (python-developer)
- [ ] Type hints on public functions
- [ ] Docstrings on public APIs
- [ ] No hardcoded credentials
- [ ] Tests for new functionality
- [ ] Error handling appropriate

#### SQL Code (sql-specialist)
- [ ] No SELECT *
- [ ] Indexes considered
- [ ] No SQL injection risks
- [ ] Naming conventions followed
- [ ] Query performance acceptable

#### Infrastructure (aws/container/k8s)
- [ ] No secrets in code
- [ ] Resource limits defined
- [ ] Idempotent operations
- [ ] Rollback strategy exists

## Example Execution

```markdown
## Iteration 1

### Reviewer (plugin-developer)
Critical: SQL injection vulnerability in user_service.py:45
Major: Missing error handling in data_loader.py:78-92
Minor: Function `proc_data` should be `process_data`

Recommendation: Request Changes

---

## Iteration 2

### Author (python-developer)
Critical: Fixed - Now using parameterized queries
Major: Fixed - Added try/except with proper logging
Minor: Fixed - Renamed function

Ready for re-review.

---

## Iteration 3

### Reviewer (plugin-developer)
All issues addressed.

Recommendation: Approve
```

## Self-Review Option

For solo work, use the same pattern with a single agent:

1. **Write code** (any specialist)
2. **Switch to review mode** (same or plugin-developer)
3. **Address own feedback**
4. **Final review pass**

This simulates pair programming benefits.
