---
name: testing-strategies
description: Testing strategies for data pipelines including unit tests, integration tests, and data quality testing.
---

# Testing Strategies for Data Engineering

## Overview

This skill provides testing patterns and strategies for data pipelines and transformations.

## Testing Pyramid for Data

```
          /\
         /  \
        / E2E\        ← Few, slow, expensive
       /------\
      /  Integ \      ← Medium count
     /----------\
    /   Unit     \    ← Many, fast, cheap
   /--------------\
  / Data Quality   \  ← Continuous, automated
 /------------------\
```

## Unit Testing

### Testing Transformations
```python
import pytest
import pandas as pd
from transformations import calculate_customer_metrics

class TestCustomerMetrics:
    @pytest.fixture
    def sample_orders(self):
        return pd.DataFrame({
            "customer_id": [1, 1, 2, 2, 2],
            "amount": [100, 200, 50, 75, 125],
            "order_date": pd.to_datetime([
                "2024-01-01", "2024-01-15",
                "2024-01-05", "2024-01-10", "2024-01-20"
            ])
        })

    def test_calculates_total_amount(self, sample_orders):
        result = calculate_customer_metrics(sample_orders)

        assert result.loc[result["customer_id"] == 1, "total_amount"].values[0] == 300
        assert result.loc[result["customer_id"] == 2, "total_amount"].values[0] == 250

    def test_counts_orders_correctly(self, sample_orders):
        result = calculate_customer_metrics(sample_orders)

        assert result.loc[result["customer_id"] == 1, "order_count"].values[0] == 2
        assert result.loc[result["customer_id"] == 2, "order_count"].values[0] == 3

    def test_handles_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["customer_id", "amount", "order_date"])
        result = calculate_customer_metrics(empty_df)

        assert len(result) == 0
```

### Testing Spark Transformations
```python
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from chispa import assert_df_equality

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[2]").appName("test").getOrCreate()

class TestSparkTransformations:
    def test_filter_active_customers(self, spark):
        # Arrange
        input_data = [
            ("1", "active", 100),
            ("2", "inactive", 200),
            ("3", "active", 150),
        ]
        input_df = spark.createDataFrame(
            input_data, ["customer_id", "status", "amount"]
        )

        expected_data = [
            ("1", "active", 100),
            ("3", "active", 150),
        ]
        expected_df = spark.createDataFrame(
            expected_data, ["customer_id", "status", "amount"]
        )

        # Act
        result_df = filter_active_customers(input_df)

        # Assert
        assert_df_equality(result_df, expected_df, ignore_row_order=True)
```

### Testing SQL Queries
```python
import pytest
from sqlalchemy import create_engine, text

@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:")
    # Setup test schema
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                amount DECIMAL(10,2),
                order_date DATE
            )
        """))
        conn.execute(text("""
            INSERT INTO orders VALUES
            (1, 100, 50.00, '2024-01-01'),
            (2, 100, 75.00, '2024-01-02'),
            (3, 200, 100.00, '2024-01-01')
        """))
        conn.commit()
    return engine

def test_customer_total_query(test_engine):
    query = """
        SELECT customer_id, SUM(amount) as total
        FROM orders
        GROUP BY customer_id
    """
    with test_engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()

    assert dict(result) == {100: 125.0, 200: 100.0}
```

## Integration Testing

### Testing DAGs (Airflow)
```python
import pytest
from airflow.models import DagBag
from datetime import datetime

@pytest.fixture
def dagbag():
    return DagBag(include_examples=False)

class TestDAGs:
    def test_no_import_errors(self, dagbag):
        assert len(dagbag.import_errors) == 0, \
            f"DAG import errors: {dagbag.import_errors}"

    def test_daily_etl_dag_structure(self, dagbag):
        dag = dagbag.get_dag("daily_etl")

        assert dag is not None
        assert dag.schedule_interval == "@daily"
        assert len(dag.tasks) >= 3

    def test_task_dependencies(self, dagbag):
        dag = dagbag.get_dag("daily_etl")
        extract = dag.get_task("extract")
        transform = dag.get_task("transform")
        load = dag.get_task("load")

        assert transform in extract.downstream_list
        assert load in transform.downstream_list
```

### Testing Database Connections
```python
import pytest
from unittest.mock import patch, MagicMock
from snowflake_loader import load_to_snowflake

class TestSnowflakeLoader:
    @patch("snowflake_loader.snowflake.connector.connect")
    def test_successful_load(self, mock_connect):
        # Setup mock
        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor

        # Execute
        result = load_to_snowflake(
            data=[{"id": 1, "name": "test"}],
            table="test_table"
        )

        # Verify
        assert result["rows_loaded"] == 1
        mock_cursor.execute.assert_called()

    @patch("snowflake_loader.snowflake.connector.connect")
    def test_connection_failure_raises(self, mock_connect):
        mock_connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            load_to_snowflake(data=[{"id": 1}], table="test_table")
```

## Data Quality Testing

### Great Expectations
```python
import great_expectations as gx

# Create expectation suite
context = gx.get_context()
suite = context.add_expectation_suite("orders_quality")

# Define expectations
expectations = [
    # Completeness
    gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
    gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id"),

    # Uniqueness
    gx.expectations.ExpectColumnValuesToBeUnique(column="order_id"),

    # Validity
    gx.expectations.ExpectColumnValuesToBeInSet(
        column="status",
        value_set=["pending", "completed", "cancelled"]
    ),
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="amount",
        min_value=0,
        max_value=1000000
    ),

    # Freshness
    gx.expectations.ExpectColumnMaxToBeBetween(
        column="order_date",
        min_value={"$PARAMETER": "yesterday"},
        max_value={"$PARAMETER": "today"}
    ),
]
```

### dbt Tests
```yaml
# schema.yml
version: 2

models:
  - name: orders
    description: Order transactions
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

      - name: amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "> 0"

    tests:
      - dbt_utils.recency:
          datepart: day
          field: created_at
          interval: 1
```

### Custom Data Quality Checks
```python
class DataQualityChecker:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.issues = []

    def check_not_null(self, columns: list) -> "DataQualityChecker":
        for col in columns:
            null_count = self.df[col].isnull().sum()
            if null_count > 0:
                self.issues.append({
                    "check": "not_null",
                    "column": col,
                    "count": null_count
                })
        return self

    def check_unique(self, columns: list) -> "DataQualityChecker":
        for col in columns:
            dup_count = self.df[col].duplicated().sum()
            if dup_count > 0:
                self.issues.append({
                    "check": "unique",
                    "column": col,
                    "count": dup_count
                })
        return self

    def check_range(self, column: str, min_val, max_val) -> "DataQualityChecker":
        out_of_range = ((self.df[column] < min_val) | (self.df[column] > max_val)).sum()
        if out_of_range > 0:
            self.issues.append({
                "check": "range",
                "column": column,
                "count": out_of_range
            })
        return self

    def validate(self) -> bool:
        if self.issues:
            for issue in self.issues:
                print(f"FAIL: {issue}")
            return False
        return True

# Usage
checker = DataQualityChecker(df)
valid = (
    checker
    .check_not_null(["order_id", "customer_id"])
    .check_unique(["order_id"])
    .check_range("amount", 0, 1000000)
    .validate()
)
```

## Contract Testing

### Schema Contracts
```python
from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

class OrderSchema(BaseModel):
    order_id: str
    customer_id: int
    amount: float
    status: str
    order_date: date

    @validator("status")
    def status_valid(cls, v):
        valid = ["pending", "completed", "cancelled"]
        if v not in valid:
            raise ValueError(f"status must be one of {valid}")
        return v

    @validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

def validate_records(records: list[dict]) -> list[OrderSchema]:
    validated = []
    for record in records:
        validated.append(OrderSchema(**record))
    return validated
```

## Mocking External Services

```python
import pytest
from unittest.mock import patch, MagicMock
import responses
import requests

class TestExternalAPIs:
    @responses.activate
    def test_api_extraction(self):
        # Mock external API
        responses.add(
            responses.GET,
            "https://api.example.com/orders",
            json={"orders": [{"id": 1, "amount": 100}]},
            status=200
        )

        # Call function that uses the API
        result = extract_from_api("https://api.example.com/orders")

        assert len(result["orders"]) == 1
        assert result["orders"][0]["id"] == 1

    @patch("boto3.client")
    def test_s3_upload(self, mock_boto):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        upload_to_s3("test-bucket", "key", b"data")

        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="key",
            Body=b"data"
        )
```

## Test Fixtures and Factories

```python
import pytest
from faker import Faker
import pandas as pd

fake = Faker()

@pytest.fixture
def order_factory():
    def _factory(count: int = 10, **overrides):
        orders = []
        for _ in range(count):
            order = {
                "order_id": fake.uuid4(),
                "customer_id": fake.random_int(1, 1000),
                "amount": round(fake.random.uniform(10, 500), 2),
                "status": fake.random_element(["pending", "completed", "cancelled"]),
                "order_date": fake.date_this_year(),
            }
            order.update(overrides)
            orders.append(order)
        return pd.DataFrame(orders)
    return _factory

def test_with_factory(order_factory):
    # Generate 100 completed orders
    df = order_factory(count=100, status="completed")

    assert len(df) == 100
    assert (df["status"] == "completed").all()
```

## Anti-Patterns

### 1. Testing in Production
- **What it is**: No test environment; changes go directly to production
- **Why it's wrong**: Bugs affect real users and data; no safe place to experiment
- **Correct approach**: Maintain dev/staging environments with production-like data

### 2. Testing Only the Happy Path
- **What it is**: Tests that only cover expected inputs and successful scenarios
- **Why it's wrong**: Misses edge cases, nulls, empty data, and error conditions
- **Correct approach**: Test edge cases explicitly; use property-based testing

### 3. Flaky Tests
- **What it is**: Tests that pass or fail inconsistently
- **Why it's wrong**: Erodes trust in test suite; tests get ignored
- **Correct approach**: Isolate tests; mock external dependencies; fix or remove flaky tests

### 4. No Data Quality Tests
- **What it is**: Code tests exist but no validation of data correctness
- **Why it's wrong**: Pipeline can "succeed" while producing incorrect data
- **Correct approach**: Add data quality checks (Great Expectations, dbt tests) to pipelines

### 5. Slow Test Suites
- **What it is**: Tests that take too long to run
- **Why it's wrong**: Developers skip tests; feedback loop is too slow
- **Correct approach**: Parallelize tests; mock slow dependencies; separate unit/integration

---

## Best Practices

1. **Test data transformations** - Core business logic
2. **Test edge cases** - Empty data, nulls, duplicates
3. **Test with realistic volumes** - Performance issues
4. **Automate data quality** - Run with every pipeline
5. **Version test data** - Reproducible tests
6. **Mock external dependencies** - Fast, reliable tests
7. **Test recovery scenarios** - Failure handling

---

## Research Tools

| Tool | Use For |
|------|---------|
| `mcp__upstash-context7-mcp__get-library-docs` | pytest, Great Expectations, dbt docs |
| `mcp__exa__get_code_context_exa` | Testing patterns and examples |

### Libraries to Always Verify

| Library | Reason |
|---------|--------|
| pytest | Fixture scope, plugin APIs |
| Great Expectations | Expectation syntax, checkpoint format |
| dbt | Test macros, severity levels |
| PySpark testing | DataFrame assertions, SparkSession fixtures |
