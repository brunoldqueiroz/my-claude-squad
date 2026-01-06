# Data Pipeline Build

Multi-agent collaboration for end-to-end ETL/ELT pipeline implementation.

## Overview

Use this template when building a complete data pipeline that requires:
- Database schema design
- Python extraction/transformation code
- Orchestration (Airflow DAGs)
- Documentation

## Agent Sequence

```
┌─────────────────────────────────────────────────────────────┐
│  1. SQL Specialist                                          │
│     └── Design target schema, staging tables                │
├─────────────────────────────────────────────────────────────┤
│  2. Python Developer                                        │
│     └── Implement extraction, transformation logic          │
├─────────────────────────────────────────────────────────────┤
│  3. Airflow Specialist                                      │
│     └── Create DAG, configure scheduling                    │
├─────────────────────────────────────────────────────────────┤
│  4. Documenter                                              │
│     └── README, data dictionary, runbook                    │
├─────────────────────────────────────────────────────────────┤
│  5. Git Commit Writer                                       │
│     └── Structured commit message                           │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Schema Design (sql-specialist)

### Input
- Source system description
- Business requirements
- Data volume estimates

### Tasks
1. Analyze source data structure
2. Design target schema (facts, dimensions if needed)
3. Create staging table DDL
4. Design idempotent load patterns (MERGE vs INSERT)
5. Define primary keys and indexes

### Output
```sql
-- Target tables DDL
-- Staging tables DDL
-- MERGE/upsert statements
-- Index recommendations
```

### Quality Gate
- [ ] Schema supports all required queries
- [ ] Incremental load pattern defined
- [ ] Data types match source precision

## Phase 2: ETL Code (python-developer)

### Input
- Schema from Phase 1
- Source connection details
- Transformation requirements

### Tasks
1. Implement extraction (API/database connectors)
2. Write transformation logic
3. Implement loading with retry logic
4. Add watermark tracking
5. Write unit tests

### Output
```
src/
├── extract/
│   └── source_connector.py
├── transform/
│   └── transformations.py
├── load/
│   └── loader.py
└── tests/
    └── test_transformations.py
```

### Quality Gate
- [ ] All transformations have tests
- [ ] Error handling covers common failures
- [ ] Watermark logic is idempotent

## Phase 3: Orchestration (airflow-specialist)

### Input
- ETL code from Phase 2
- Scheduling requirements
- Dependency information

### Tasks
1. Create DAG structure
2. Define task dependencies
3. Configure retry policies
4. Add alerting/notifications
5. Set up connections and variables

### Output
```python
# dags/pipeline_dag.py
# config/connections.yaml
# config/variables.yaml
```

### Quality Gate
- [ ] DAG is idempotent (re-runnable)
- [ ] Proper error handling and alerts
- [ ] Backfill strategy defined

## Phase 4: Documentation (documenter)

### Input
- All code from Phases 1-3
- Business context

### Tasks
1. Write README with setup instructions
2. Create data dictionary
3. Document DAG dependencies
4. Write runbook for operations

### Output
```
docs/
├── README.md
├── data-dictionary.md
├── architecture.md
└── runbook.md
```

### Quality Gate
- [ ] README enables new team member setup
- [ ] Data dictionary covers all columns
- [ ] Runbook covers common failure scenarios

## Phase 5: Commit (git-commit-writer)

### Input
- All files created/modified

### Tasks
1. Review all changes
2. Write conventional commit message
3. Ensure no secrets committed

### Output
```
feat(pipeline): add orders ETL pipeline

- Add target schema with staging tables
- Implement Python ETL with watermark tracking
- Create Airflow DAG with daily schedule
- Add comprehensive documentation

Closes #123
```

## Handoff Protocol

Between each phase, the handoff includes:

1. **Summary of work done**: What was created/modified
2. **Key decisions**: Important choices and rationale
3. **Open questions**: Issues for next agent to address
4. **Files to review**: Specific files the next agent needs

## Example Execution

```markdown
## Task: Build Orders ETL from Salesforce to Snowflake

### Phase 1: sql-specialist
Created target schema `analytics.fact_orders` with dimensions.
Staging table uses MERGE pattern for idempotency.
Decision: Used SCD Type 2 for customer dimension.

### Phase 2: python-developer
Implemented Salesforce connector using simple-salesforce.
Transformations handle NULL values and type coercion.
Tests cover all edge cases in transformation logic.

### Phase 3: airflow-specialist
DAG runs daily at 6 AM UTC after Salesforce sync.
Retry policy: 3 attempts with exponential backoff.
Slack alerts on failure.

### Phase 4: documenter
Full README with local development setup.
Data dictionary with business definitions.
Runbook covers manual backfill process.

### Phase 5: git-commit-writer
Commit: feat(orders): add Salesforce to Snowflake ETL pipeline
```
