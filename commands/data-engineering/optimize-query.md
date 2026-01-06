---
description: Analyze and optimize SQL query performance
argument-hint: [query or file path]
agent: sql-specialist
---

# Optimize Query

Analyze a SQL query and provide optimization recommendations.

## Usage

```
/optimize-query <query or file path>
```

Provide either:
- A SQL query directly
- Path to a .sql file
- Description of the slow query

## Analysis Process

1. **Parse Query**: Understand query structure
2. **Identify Issues**: Look for common anti-patterns
3. **Suggest Optimizations**: Provide specific fixes
4. **Explain Trade-offs**: Note any considerations

## Anti-Patterns Checked

### Index Issues
- Functions on indexed columns
- Implicit type conversions
- OR conditions preventing index use

### Join Issues
- Missing join predicates (Cartesian products)
- Suboptimal join order
- Unnecessary self-joins

### Query Structure
- SELECT * usage
- Unnecessary DISTINCT
- Correlated subqueries
- Inefficient NOT IN with NULLs

### Performance
- Missing filters (large table scans)
- Unnecessary sorting
- Over-aggregation

## Output Format

```markdown
# Query Analysis

## Original Query
[formatted query]

## Issues Found

### 1. [Issue Title]
**Severity**: High | Medium | Low
**Location**: Line X

**Problem**: [Explanation]

**Before**:
```sql
[problematic code]
```

**After**:
```sql
[fixed code]
```

**Impact**: [Expected improvement]

## Optimized Query
[Full optimized query]

## Additional Recommendations
- Consider adding index on X
- Statistics may be stale
- Query may benefit from partitioning
```

## Example

Input:
```sql
SELECT * FROM orders WHERE YEAR(order_date) = 2024
```

Output:
- Issue: Function on indexed column prevents index use
- Fix: Use range predicate instead
- Optimized: `WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'`
