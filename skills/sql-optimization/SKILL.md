---
name: sql-optimization
description: SQL query optimization techniques including execution plans, indexing, and platform-specific optimizations.
---

# SQL Optimization

## Overview

This skill provides techniques for optimizing SQL queries across different platforms.

## Execution Plan Analysis

### Key Metrics
- **Estimated vs Actual Rows** - Large differences indicate stats issues
- **Cost** - Relative measure of resource usage
- **Execution Time** - Wall clock time for operation
- **Memory Grants** - Memory requested vs used

### Operations to Watch
| Operation | Issue | Solution |
|-----------|-------|----------|
| Table Scan | Full table read | Add appropriate index |
| Key Lookup | Extra I/O for columns | Create covering index |
| Sort | Memory pressure | Add index with ORDER BY columns |
| Hash Match | Large memory grants | Reduce dataset size before join |
| Nested Loop | Many iterations | Consider hash/merge join |

## Index Strategies

### B-Tree Index (Default)
```sql
-- Equality and range queries
CREATE INDEX idx_orders_date ON orders(order_date);

-- Composite for multi-column filters
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
```

### Covering Index
```sql
-- Include non-key columns to avoid lookups
CREATE INDEX idx_orders_covering
ON orders(customer_id, order_date)
INCLUDE (amount, status);
```

### Filtered Index
```sql
-- Index subset of rows
CREATE INDEX idx_orders_active
ON orders(customer_id)
WHERE status = 'active';
```

### Columnstore Index
```sql
-- For analytics workloads
CREATE COLUMNSTORE INDEX idx_orders_cs
ON orders(order_date, customer_id, amount);
```

## Common Anti-Patterns

### 1. Functions on Indexed Columns
```sql
-- BAD: Prevents index usage
WHERE YEAR(order_date) = 2024

-- GOOD: Sargable predicate
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
```

### 2. Implicit Type Conversion
```sql
-- BAD: String compared to int
WHERE customer_id = '12345'

-- GOOD: Match types
WHERE customer_id = 12345
```

### 3. NOT IN with NULLs
```sql
-- BAD: NULL handling issues
WHERE id NOT IN (SELECT id FROM other_table)

-- GOOD: Use NOT EXISTS
WHERE NOT EXISTS (SELECT 1 FROM other_table WHERE other_table.id = main.id)
```

### 4. SELECT *
```sql
-- BAD: Fetches unnecessary columns
SELECT * FROM orders

-- GOOD: Select needed columns
SELECT order_id, customer_id, amount FROM orders
```

### 5. OR Conditions
```sql
-- BAD: May prevent index usage
WHERE customer_id = 1 OR product_id = 2

-- GOOD: Union separate queries
SELECT * FROM orders WHERE customer_id = 1
UNION ALL
SELECT * FROM orders WHERE product_id = 2 AND customer_id != 1
```

## Join Optimization

### Join Types
| Type | Use When |
|------|----------|
| Nested Loop | Small outer table, indexed inner |
| Hash Join | No useful indexes, medium tables |
| Merge Join | Pre-sorted data on join keys |

### Join Order
- Start with most restrictive table
- Apply filters early
- Reduce rows before joins

### Broadcast Join (Distributed)
```sql
-- Spark/Snowflake: Small table broadcast
SELECT /*+ BROADCAST(dim) */ ...
FROM fact
JOIN dim ON fact.key = dim.key
```

## Platform-Specific Optimizations

### Snowflake
```sql
-- Clustering for large tables
ALTER TABLE orders CLUSTER BY (order_date, customer_id);

-- Search optimization for point queries
ALTER TABLE customers ADD SEARCH OPTIMIZATION ON EQUALITY(email);

-- Result caching (enabled by default)
SELECT * FROM orders WHERE order_date = '2024-01-01';
```

### SQL Server
```sql
-- Query hints
SELECT * FROM orders WITH (INDEX(idx_name)) WHERE ...

-- Parameter sniffing fix
OPTION (OPTIMIZE FOR UNKNOWN)

-- Query store for plan stability
ALTER DATABASE db SET QUERY_STORE = ON;
```

### PostgreSQL
```sql
-- Parallel query (PG 9.6+)
SET max_parallel_workers_per_gather = 4;

-- Partial index
CREATE INDEX idx_active ON orders(id) WHERE active = true;

-- Expression index
CREATE INDEX idx_lower_email ON users(lower(email));
```

## Query Rewriting Techniques

### CTE vs Subquery
```sql
-- CTEs for readability, may or may not optimize
WITH recent_orders AS (
    SELECT * FROM orders WHERE order_date >= CURRENT_DATE - 30
)
SELECT * FROM recent_orders WHERE status = 'completed';
```

### Window Function vs Self-Join
```sql
-- BAD: Self-join for running total
SELECT a.*, (SELECT SUM(b.amount) FROM orders b WHERE b.id <= a.id)
FROM orders a

-- GOOD: Window function
SELECT *, SUM(amount) OVER (ORDER BY id) AS running_total
FROM orders
```

### Materialization
```sql
-- Create intermediate table for complex queries
CREATE TABLE order_summary AS
SELECT customer_id, SUM(amount) AS total
FROM orders
GROUP BY customer_id;

-- Query the materialized result
SELECT * FROM order_summary WHERE total > 1000;
```

## Statistics and Cardinality

### Update Statistics
```sql
-- SQL Server
UPDATE STATISTICS orders;

-- PostgreSQL
ANALYZE orders;

-- Snowflake (automatic)
```

### Histogram Issues
- Uneven data distribution
- Skewed join keys
- Parameterized queries

## Monitoring Queries

### Find Expensive Queries
```sql
-- Snowflake
SELECT query_id, query_text, total_elapsed_time
FROM snowflake.account_usage.query_history
ORDER BY total_elapsed_time DESC
LIMIT 20;

-- SQL Server
SELECT TOP 20
    qs.total_elapsed_time / qs.execution_count AS avg_time,
    SUBSTRING(st.text, ...) AS query
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY avg_time DESC;
```

## Best Practices

1. **Read execution plans** - Understand before optimizing
2. **Test with realistic data** - Small tests miss issues
3. **Index selectively** - Too many indexes hurt writes
4. **Update statistics** - Optimizer needs accurate info
5. **Monitor query performance** - Track over time
6. **Document optimizations** - Explain why for future maintainers
