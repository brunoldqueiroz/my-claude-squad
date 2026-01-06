---
description: Generate data pipeline boilerplate for ETL/ELT workflows
argument-hint: <source> to <target> [options]
agent: python-developer
---

# Create Pipeline

Generate data pipeline boilerplate code for common ETL/ELT patterns.

## Usage

```
/create-pipeline <source> to <target> [--incremental] [--schedule <cron>]
```

## Supported Sources

- **API**: REST API endpoint
- **S3**: AWS S3 bucket
- **PostgreSQL**: PostgreSQL database
- **MySQL**: MySQL database
- **Files**: CSV, JSON, Parquet files

## Supported Targets

- **Snowflake**: Snowflake data warehouse
- **Redshift**: Amazon Redshift
- **S3**: AWS S3 (data lake)
- **PostgreSQL**: PostgreSQL database

## Options

- `--incremental`: Generate incremental loading logic
- `--schedule <cron>`: Include Airflow DAG with schedule
- `--with-tests`: Include pytest test files
- `--with-docs`: Include documentation template

## Generated Files

```
pipeline_name/
├── src/
│   ├── __init__.py
│   ├── extract.py      # Extraction logic
│   ├── transform.py    # Transformation logic
│   ├── load.py         # Loading logic
│   └── config.py       # Configuration
├── dags/
│   └── pipeline_dag.py # Airflow DAG (if --schedule)
├── tests/
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_load.py
├── config/
│   └── config.yaml     # Pipeline configuration
├── requirements.txt
└── README.md
```

## Example

```
/create-pipeline s3 to snowflake --incremental --schedule "0 6 * * *"
```

Generates:
- S3 extraction using boto3
- Snowflake loading using snowflake-connector
- Incremental logic with watermarks
- Airflow DAG running at 6 AM daily

## Pipeline Patterns

### Full Refresh
- Truncate and reload target
- Simple, idempotent
- Use for small tables or dimension tables

### Incremental - Append
- Load only new records
- Track last loaded timestamp/ID
- Use for append-only fact tables

### Incremental - Merge
- Upsert based on key
- Track modifications
- Use for slowly changing data

### CDC (Change Data Capture)
- Process change events
- Maintain change history
- Use for real-time updates
