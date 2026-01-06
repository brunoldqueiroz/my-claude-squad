# Migration Project

Multi-agent collaboration for database or platform migrations.

## Overview

Use this template when:
- Migrating between database platforms (e.g., SQL Server → Snowflake)
- Moving data between environments
- Upgrading schema versions with data transformation
- Consolidating multiple sources into a unified platform

## Agent Sequence

```
┌─────────────────────────────────────────────────────────────┐
│  1. SQL Specialist (Source)                                 │
│     └── Analyze source schema, extract DDL                  │
├─────────────────────────────────────────────────────────────┤
│  2. SQL/Target Specialist                                   │
│     └── Design target schema, handle platform differences   │
├─────────────────────────────────────────────────────────────┤
│  3. Python Developer                                        │
│     └── Build migration scripts, data validation           │
├─────────────────────────────────────────────────────────────┤
│  4. Airflow Specialist                                      │
│     └── Orchestrate migration, handle dependencies          │
├─────────────────────────────────────────────────────────────┤
│  5. Documenter                                              │
│     └── Migration plan, rollback procedures, validation     │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Source Analysis (sql-specialist)

### Input
- Source database access
- Scope of migration (tables, views, procedures)

### Tasks
1. Extract complete schema DDL
2. Document table relationships (FKs)
3. Identify data volumes per table
4. Catalog stored procedures/functions
5. Note platform-specific features in use

### Output
```markdown
## Source Analysis Report

### Tables (X total)
| Table | Rows | Size | Dependencies |
|-------|------|------|--------------|
| orders | 10M | 2GB | customers, products |

### Platform-Specific Features
- SQL Server: IDENTITY columns, NVARCHAR(MAX)
- Stored procedures: 15 (list attached)

### Data Types Mapping Needed
| Source Type | Occurrences | Notes |
|-------------|-------------|-------|
| NVARCHAR(MAX) | 12 | Map to VARCHAR in target |
```

### Quality Gate
- [ ] All objects documented
- [ ] Dependencies mapped
- [ ] Volume estimates accurate

## Phase 2: Target Design (snowflake-specialist or target platform)

### Input
- Source analysis from Phase 1
- Target platform requirements
- Performance requirements

### Tasks
1. Design target schema
2. Map data types between platforms
3. Handle platform-specific features
4. Design clustering/partitioning strategy
5. Plan for missing features (stored procs → external)

### Output
```sql
-- Target DDL with platform adaptations
-- Type mapping documentation
-- Clustering key decisions
-- Feature migration notes
```

### Quality Gate
- [ ] All source objects have target equivalents
- [ ] Data type mappings preserve precision
- [ ] Performance considerations documented

## Phase 3: Migration Scripts (python-developer)

### Input
- Source and target schemas
- Data volume information
- Transformation requirements

### Tasks
1. Build extraction scripts (chunked for large tables)
2. Implement transformations
3. Create loading scripts with idempotency
4. Build validation scripts (row counts, checksums)
5. Add progress tracking and logging

### Output
```
migration/
├── extract/
│   ├── full_extract.py
│   └── incremental_extract.py
├── transform/
│   └── transformations.py
├── load/
│   └── loader.py
├── validate/
│   ├── row_counts.py
│   └── data_quality.py
└── utils/
    └── progress_tracker.py
```

### Quality Gate
- [ ] Scripts handle interruption/resume
- [ ] Validation covers all tables
- [ ] Large tables chunked appropriately

## Phase 4: Orchestration (airflow-specialist)

### Input
- Migration scripts from Phase 3
- Dependency order from Phase 1
- Scheduling constraints

### Tasks
1. Create migration DAG with proper dependencies
2. Handle table ordering (FK dependencies)
3. Add checkpoints for resume capability
4. Configure alerting
5. Plan parallel execution where possible

### Output
```python
# dags/migration_dag.py
# - Respects FK dependencies
# - Parallel where possible
# - Checkpoint support
```

### Quality Gate
- [ ] Dependencies correctly ordered
- [ ] Parallel execution maximized
- [ ] Failure recovery tested

## Phase 5: Documentation (documenter)

### Input
- All migration artifacts
- Decisions made

### Tasks
1. Write migration plan document
2. Create rollback procedures
3. Document validation criteria
4. Write cutover runbook
5. Create post-migration checklist

### Output
```
docs/
├── migration-plan.md
├── rollback-procedures.md
├── validation-criteria.md
├── cutover-runbook.md
└── post-migration-checklist.md
```

## Migration Patterns

### Big Bang
All tables migrated in one window. Use when:
- Small data volumes
- Can afford downtime
- Simple dependencies

### Phased
Tables migrated in groups. Use when:
- Large volumes
- Limited downtime windows
- Can operate with partial migration

### Parallel Running
Both systems active during transition. Use when:
- Zero downtime required
- Complex validation needed
- Gradual cutover preferred

## Validation Strategy

```markdown
## Validation Checklist

### Row Counts
| Table | Source | Target | Match |
|-------|--------|--------|-------|
| orders | 10,000,000 | 10,000,000 | ✓ |

### Sample Data Verification
- Random sample of 1000 rows per table
- Compare key columns

### Aggregate Validation
- SUM of numeric columns
- COUNT DISTINCT of key columns

### Business Logic Validation
- Key reports produce same results
- Critical queries return matching data
```
