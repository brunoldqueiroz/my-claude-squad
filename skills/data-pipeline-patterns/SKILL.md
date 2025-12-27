---
name: data-pipeline-patterns
description: Data pipeline design patterns for ETL/ELT, batch and streaming, idempotency, and error handling.
---

# Data Pipeline Patterns

## Overview

This skill provides patterns and best practices for designing robust data pipelines.

## ETL vs ELT

### ETL (Extract, Transform, Load)
- Transform data before loading to target
- Better for complex transformations
- Reduces load on target system
- Traditional approach for data warehouses

```
Source → Extract → Transform → Load → Target
```

### ELT (Extract, Load, Transform)
- Load raw data first, transform in target
- Leverages target system compute
- Better for cloud data warehouses
- Enables data lake architecture

```
Source → Extract → Load → Transform → Target
                    ↓
                Raw Zone → Processed Zone → Curated Zone
```

## Batch vs Streaming

### Batch Processing
- Scheduled intervals (hourly, daily)
- Higher latency, lower cost
- Easier error handling
- Good for: Reports, aggregations, ML training

### Streaming Processing
- Near real-time (seconds to minutes)
- Lower latency, higher complexity
- Requires careful state management
- Good for: Dashboards, alerts, fraud detection

### Lambda Architecture
```
         ┌─────────────────┐
         │  Batch Layer    │──── Historical accuracy
Source → │                 │
         │  Speed Layer    │──── Real-time updates
         └────────┬────────┘
                  ↓
            Serving Layer
```

### Kappa Architecture
```
Source → Stream Processing → Serving Layer
              ↓
         Log/Event Store (replay capability)
```

## Idempotency Patterns

### 1. Delete-and-Insert
```sql
DELETE FROM target WHERE date = '{{ ds }}';
INSERT INTO target SELECT * FROM staging WHERE date = '{{ ds }}';
```

### 2. Merge/Upsert
```sql
MERGE INTO target t
USING source s ON t.id = s.id
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...
```

### 3. Partition Overwrite
```python
df.write.mode("overwrite").partitionBy("date").parquet(path)
```

### 4. Checkpointing
- Track last processed record/timestamp
- Resume from checkpoint on failure
- Use database or file-based tracking

## Error Handling Strategies

### 1. Dead Letter Queue (DLQ)
```
Input → Process → Success → Output
           ↓
        Failure → DLQ → Manual Review
```

### 2. Retry with Backoff
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def process_record(record):
    ...
```

### 3. Circuit Breaker
- Track failure rate
- Open circuit after threshold
- Fail fast to prevent cascade
- Auto-recover after timeout

### 4. Graceful Degradation
- Continue with partial data
- Log failures for later reprocessing
- Alert on threshold exceeded

## Data Quality Patterns

### 1. Schema Validation
- Validate against expected schema
- Reject or quarantine invalid records

### 2. Expectation Testing
```python
# Great Expectations
expect_column_values_to_not_be_null("customer_id")
expect_column_values_to_be_in_set("status", ["active", "inactive"])
expect_column_mean_to_be_between("amount", 100, 500)
```

### 3. Anomaly Detection
- Track row counts
- Monitor null rates
- Alert on significant deviations

### 4. Reconciliation
- Compare source and target counts
- Checksum critical columns
- Validate aggregates match

## Orchestration Patterns

### 1. Sequential
```
Task A → Task B → Task C
```

### 2. Parallel
```
       ┌─ Task B ─┐
Task A ─┤         ├─ Task D
       └─ Task C ─┘
```

### 3. Dynamic Task Generation
```python
for table in tables:
    extract_task = PythonOperator(task_id=f"extract_{table}", ...)
    load_task = PythonOperator(task_id=f"load_{table}", ...)
    extract_task >> load_task
```

### 4. Sensor Pattern
```
Sensor (wait for data) → Process → Complete
```

## Anti-Patterns

### 1. Non-Idempotent Pipelines
- **What it is**: Pipelines that produce different results or fail when re-run
- **Why it's wrong**: Makes recovery from failures difficult and causes data inconsistencies
- **Correct approach**: Use delete-and-insert, merge/upsert, or partition overwrite patterns

### 2. Tight Coupling Between Pipeline Stages
- **What it is**: Direct dependencies between stages without clear interfaces
- **Why it's wrong**: Changes to one stage break downstream stages; difficult to test in isolation
- **Correct approach**: Define clear contracts between stages; use staging tables or files

### 3. Silent Data Loss
- **What it is**: Filtering or dropping records without logging or dead-letter queues
- **Why it's wrong**: Data disappears with no audit trail; issues go undetected
- **Correct approach**: Log filtered records; use DLQ for failed records; alert on thresholds

### 4. Hardcoded Configurations
- **What it is**: Embedding connection strings, dates, or paths directly in code
- **Why it's wrong**: Requires code changes for environment differences; exposes secrets
- **Correct approach**: Use environment variables, config files, or secrets managers

### 5. No Backfill Strategy
- **What it is**: Pipelines that can only process current data
- **Why it's wrong**: Cannot recover from outages or reprocess historical data
- **Correct approach**: Design for date-parameterized runs; support date range processing

---

## Best Practices

1. **Make pipelines idempotent** - Safe to rerun
2. **Implement proper logging** - Debug and monitor
3. **Handle schema evolution** - Plan for changes
4. **Test with production-like data** - Catch edge cases
5. **Monitor and alert** - Know when things break
6. **Document dependencies** - Understand relationships
7. **Version control everything** - Code, configs, schemas
