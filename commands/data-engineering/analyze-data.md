---
description: Profile and analyze a dataset for quality and patterns
argument-hint: <file path or table name>
agent: python-developer
---

# Analyze Data

Profile and analyze a dataset to understand its structure, quality, and patterns.

## Usage

```
/analyze-data <file path or table name>
```

Supports:
- CSV files
- Parquet files
- JSON files
- Database tables (with connection)

## Analysis Performed

### Schema Analysis
- Column names and types
- Inferred vs actual types
- Nested structure (for JSON)

### Statistics
- Row count
- Column cardinality
- Min, max, mean, median
- Standard deviation
- Percentiles (25th, 50th, 75th, 95th, 99th)

### Data Quality
- Null counts and percentages
- Duplicate rows
- Empty strings
- Whitespace issues

### Value Analysis
- Top N most frequent values
- Unique value counts
- Pattern detection (emails, dates, IDs)
- Outlier detection

### Relationships
- Potential primary keys
- Potential foreign keys
- Correlations between numeric columns

## Output Format

```markdown
# Data Profile: [Dataset Name]

## Overview
| Metric | Value |
|--------|-------|
| Rows | 1,234,567 |
| Columns | 15 |
| Size | 256 MB |
| Duplicates | 0 (0.00%) |

## Column Summary

| Column | Type | Non-Null | Unique | Top Value |
|--------|------|----------|--------|-----------|
| order_id | string | 100% | 1,234,567 | - |
| customer_id | int | 100% | 45,678 | 12345 (2.3%) |
| amount | float | 99.8% | 8,234 | 99.99 (5.1%) |
| status | string | 100% | 3 | completed (65%) |

## Column Details

### order_id
- **Type**: string
- **Unique**: 1,234,567 (100%)
- **Pattern**: UUID format
- **Potential PK**: Yes

### amount
- **Type**: float
- **Range**: 0.01 - 99,999.99
- **Mean**: 245.67
- **Median**: 189.00
- **Std Dev**: 312.45
- **Nulls**: 2,500 (0.2%)
- **Outliers**: 150 values > 10,000

## Data Quality Issues

| Issue | Column | Count | Percentage |
|-------|--------|-------|------------|
| Null values | amount | 2,500 | 0.2% |
| Future dates | order_date | 15 | 0.001% |
| Negative values | quantity | 3 | 0.0002% |

## Recommendations
1. Consider handling null amounts (impute or filter)
2. Investigate future dates - likely data entry errors
3. Negative quantities may indicate returns
```

## Example

```
/analyze-data data/orders.parquet
```

Produces a comprehensive profile of the orders dataset.
