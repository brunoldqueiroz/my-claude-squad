---
name: code-review-standards
description: Code review checklists and standards for Python, SQL, infrastructure, and security.
---

# Code Review Standards

## Overview

This skill provides checklists and standards for conducting effective code reviews in data engineering projects.

## General Principles

### Reviewer Mindset
- Be constructive, not critical
- Focus on the code, not the author
- Explain the "why" behind suggestions
- Acknowledge good practices
- Consider the context and constraints

### What to Review
- Correctness - Does it work?
- Clarity - Is it readable?
- Maintainability - Is it easy to change?
- Performance - Is it efficient?
- Security - Is it safe?
- Testing - Is it tested?

## Python Review Checklist

### Code Quality
- [ ] Follows PEP 8 style guide
- [ ] Uses meaningful variable/function names
- [ ] Functions are focused and small (< 50 lines ideal)
- [ ] No deeply nested code (max 3 levels)
- [ ] DRY - No duplicate code
- [ ] No commented-out code

### Type Hints and Docstrings
- [ ] Type hints on all functions
- [ ] Return types specified
- [ ] Docstrings for public functions (Google style)
- [ ] Complex logic has inline comments

```python
# Good
def calculate_total(
    items: list[OrderItem],
    discount: float = 0.0,
) -> Decimal:
    """
    Calculate order total with optional discount.

    Args:
        items: List of order items.
        discount: Discount percentage (0-1).

    Returns:
        Total amount after discount.

    Raises:
        ValueError: If discount is not between 0 and 1.
    """
```

### Error Handling
- [ ] Specific exceptions caught (not bare `except:`)
- [ ] Errors logged with context
- [ ] Appropriate error messages for users
- [ ] Resources cleaned up (context managers)
- [ ] No silent failures

```python
# Good
try:
    result = process_data(df)
except ValidationError as e:
    logger.error("Validation failed", error=str(e), row_count=len(df))
    raise
except DatabaseError as e:
    logger.error("Database error", error=str(e))
    raise PipelineError("Failed to save data") from e
```

### Testing
- [ ] Unit tests for new functions
- [ ] Edge cases covered (empty, null, large)
- [ ] Tests are independent
- [ ] Fixtures used appropriately
- [ ] Mocks for external dependencies
- [ ] Coverage > 80% for new code

### Dependencies
- [ ] No unnecessary dependencies added
- [ ] Versions pinned appropriately
- [ ] Security vulnerabilities checked

## SQL Review Checklist

### Query Correctness
- [ ] Joins are correct (no accidental cross-joins)
- [ ] WHERE clause filters appropriately
- [ ] GROUP BY includes all non-aggregated columns
- [ ] NULL handling is explicit
- [ ] Date/time zones handled correctly

### Performance
- [ ] No SELECT * in production code
- [ ] Filters use indexed columns
- [ ] No functions on indexed columns in WHERE
- [ ] Appropriate join types used
- [ ] Large table operations partitioned

```sql
-- Bad
SELECT * FROM orders WHERE YEAR(order_date) = 2024

-- Good
SELECT order_id, customer_id, amount, order_date
FROM orders
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
```

### Data Quality
- [ ] Deduplication handled
- [ ] NULL coalescence where needed
- [ ] Data type conversions explicit
- [ ] Edge cases handled (empty results)

### Maintainability
- [ ] Uses CTEs for readability
- [ ] Consistent formatting/indentation
- [ ] Complex logic commented
- [ ] Column aliases are meaningful

```sql
-- Good: CTEs for clarity
WITH active_customers AS (
    SELECT customer_id, email
    FROM customers
    WHERE status = 'active'
),
recent_orders AS (
    SELECT customer_id, SUM(amount) AS total_amount
    FROM orders
    WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY customer_id
)
SELECT
    ac.customer_id,
    ac.email,
    COALESCE(ro.total_amount, 0) AS recent_total
FROM active_customers ac
LEFT JOIN recent_orders ro ON ac.customer_id = ro.customer_id
```

## dbt Review Checklist

### Model Quality
- [ ] Proper materialization (view/table/incremental)
- [ ] Incremental logic is correct
- [ ] ref() and source() used properly
- [ ] Documentation in schema.yml
- [ ] Tests defined for key columns

### Testing
- [ ] Primary keys tested (unique, not_null)
- [ ] Foreign keys tested (relationships)
- [ ] Business rules validated (accepted_values, custom tests)
- [ ] Freshness tests on sources

```yaml
# Good: Comprehensive testing
models:
  - name: orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('customers')
              field: customer_id
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'completed', 'cancelled']
```

## Infrastructure Review Checklist

### Terraform/IaC
- [ ] Resources have meaningful names
- [ ] Tags/labels applied consistently
- [ ] Variables used for configurability
- [ ] Outputs defined for dependencies
- [ ] State management configured
- [ ] No hardcoded secrets

```hcl
# Good: Properly tagged resource
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project}-${var.environment}-data-lake"

  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
```

### Docker
- [ ] Multi-stage build for size
- [ ] Specific base image tags (not :latest)
- [ ] Non-root user
- [ ] Health check defined
- [ ] No secrets in image
- [ ] .dockerignore present

### Kubernetes
- [ ] Resource requests AND limits set
- [ ] Liveness and readiness probes
- [ ] Pod disruption budget for HA
- [ ] Secrets not in plain text
- [ ] Labels consistent

## Security Review Checklist

### Authentication & Authorization
- [ ] No hardcoded credentials
- [ ] Secrets in proper secret store
- [ ] Least privilege permissions
- [ ] IAM roles properly scoped
- [ ] Service accounts used (not personal)

### Data Protection
- [ ] Encryption at rest enabled
- [ ] Encryption in transit (TLS)
- [ ] PII handling documented
- [ ] Data masking where appropriate
- [ ] Audit logging enabled

### Code Security
- [ ] No SQL injection vulnerabilities
- [ ] Input validation present
- [ ] No sensitive data in logs
- [ ] Dependencies scanned for CVEs

```python
# Bad: SQL injection risk
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good: Parameterized query
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

## Airflow DAG Review Checklist

- [ ] DAG ID is unique and descriptive
- [ ] Schedule makes sense for the use case
- [ ] catchup=False unless backfill needed
- [ ] max_active_runs prevents parallel issues
- [ ] Retries configured appropriately
- [ ] Timeouts prevent hanging tasks
- [ ] XCom usage is minimal (not large data)
- [ ] Task dependencies are correct
- [ ] Sensors use mode="reschedule"
- [ ] No hardcoded dates

```python
# Good: Well-configured DAG
@dag(
    dag_id="etl_daily_orders",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(hours=2),
    },
    tags=["etl", "orders"],
)
```

## PR Best Practices

### For Authors
1. Keep PRs small (< 400 lines ideal)
2. Write clear description of changes
3. Link to ticket/issue
4. Self-review before requesting review
5. Respond to feedback constructively

### PR Description Template
```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] README updated
- [ ] Docstrings added

## Related
- Closes #123
- Related to #456
```

### For Reviewers
1. Review within 24 hours
2. Be specific in comments
3. Distinguish blocking vs nice-to-have
4. Approve promptly when ready
5. Follow up on requested changes

## Comment Templates

### Request Change
```
Consider using X instead of Y because [reason].

This would [benefit].
```

### Suggestion (Non-blocking)
```
nit: You could simplify this by...

(non-blocking)
```

### Question
```
I'm not sure I understand the purpose of this. Could you explain why...?
```

### Positive Feedback
```
Nice approach here! The use of [X] makes this really clean.
```

## Anti-Patterns

### 1. Nitpick-Heavy Reviews
- **What it is**: Focusing on style minutiae instead of logic and design
- **Why it's wrong**: Delays merges; discourages contributions; misses real issues
- **Correct approach**: Automate style checks; focus on correctness, security, maintainability

### 2. Rubber-Stamp Approvals
- **What it is**: Approving without actually reviewing the code
- **Why it's wrong**: Defeats the purpose of code review; bugs slip through
- **Correct approach**: Take time to understand changes; ask questions if unclear

### 3. Delayed Reviews
- **What it is**: Letting PRs sit for days without review
- **Why it's wrong**: Blocks progress; context is lost; merge conflicts accumulate
- **Correct approach**: Review within 24 hours; set team expectations

### 4. Adversarial Tone
- **What it is**: Harsh criticism or dismissive comments
- **Why it's wrong**: Damages team morale; discourages collaboration
- **Correct approach**: Be constructive; focus on code not person; acknowledge good work

### 5. No Follow-Up
- **What it is**: Requesting changes but not re-reviewing
- **Why it's wrong**: Blocks the PR indefinitely; frustrates authors
- **Correct approach**: Re-review promptly after changes; don't ghost

---

## Best Practices

1. **Review in context** - Understand the broader goal
2. **Be timely** - Don't block progress
3. **Focus on impact** - Prioritize important issues
4. **Learn from reviews** - Both giving and receiving
5. **Use automation** - Linters, formatters, CI checks
6. **Document decisions** - For future reference
