# Incremental Loading Patterns

Detailed reference for incremental data loading strategies.

## Watermark Pattern

Track the last processed timestamp or ID to load only new/changed records.

### Database Implementation

```sql
-- Create watermark table
CREATE TABLE pipeline_watermarks (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_watermark TIMESTAMP,
    last_run_at TIMESTAMP,
    records_processed INT
);

-- Get watermark before extraction
SELECT last_watermark
FROM pipeline_watermarks
WHERE pipeline_name = 'orders_etl';

-- Update watermark after successful load
UPDATE pipeline_watermarks
SET last_watermark = :new_watermark,
    last_run_at = CURRENT_TIMESTAMP,
    records_processed = :count
WHERE pipeline_name = 'orders_etl';
```

### Python Implementation

```python
from datetime import datetime
from sqlalchemy import text

def get_watermark(engine, pipeline_name: str) -> datetime:
    """Get the last processed watermark."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT last_watermark FROM pipeline_watermarks WHERE pipeline_name = :name"),
            {"name": pipeline_name}
        ).fetchone()
        return result[0] if result else datetime.min

def update_watermark(engine, pipeline_name: str, watermark: datetime, count: int):
    """Update watermark after successful processing."""
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO pipeline_watermarks (pipeline_name, last_watermark, last_run_at, records_processed)
                VALUES (:name, :wm, :now, :count)
                ON CONFLICT (pipeline_name) DO UPDATE
                SET last_watermark = :wm, last_run_at = :now, records_processed = :count
            """),
            {"name": pipeline_name, "wm": watermark, "now": datetime.utcnow(), "count": count}
        )
        conn.commit()
```

## CDC Pattern (Change Data Capture)

Use database-native CDC features to capture only changed records.

### Snowflake Streams

```sql
-- Create stream on source table
CREATE OR REPLACE STREAM orders_stream ON TABLE raw.orders;

-- Process changes
INSERT INTO staging.orders_changes
SELECT *, METADATA$ACTION, METADATA$ISUPDATE, METADATA$ROW_ID
FROM orders_stream;

-- Stream automatically resets after consumption
```

### Debezium (Kafka Connect)

```json
{
  "name": "orders-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "debezium",
    "database.dbname": "orders",
    "table.include.list": "public.orders",
    "topic.prefix": "cdc",
    "slot.name": "orders_slot"
  }
}
```

## Partition-Based Loading

Load data by partition (date, region, etc.) for parallelism and recovery.

```python
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

def load_partition(partition_date: date):
    """Load a single partition."""
    query = f"""
        SELECT * FROM orders
        WHERE order_date = '{partition_date}'
    """
    df = pd.read_sql(query, source_engine)
    df.to_sql('orders', target_engine, if_exists='append', index=False)
    return len(df)

def load_date_range(start_date: date, end_date: date, workers: int = 4):
    """Load multiple partitions in parallel."""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(load_partition, dates))

    return sum(results)
```

## Idempotency Considerations

All incremental patterns should be idempotent:

| Pattern | Idempotency Approach |
|---------|---------------------|
| Watermark | DELETE + INSERT or MERGE |
| CDC | Use record keys for upsert |
| Partition | TRUNCATE partition + INSERT |

See: `examples/idempotent-merge.sql`
