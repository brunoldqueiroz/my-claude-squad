---
description: Analyze a complex task and create an execution plan with agent assignments
argument-hint: <task description>
agent: squad-orchestrator
---

# Plan Task

Analyze the provided task and create a structured execution plan.

## Process

1. **Understand the Task**: Parse the user's request and identify:
   - Main objective
   - Required technologies
   - Expected deliverables

2. **Decompose into Subtasks**: Break down into atomic units:
   - Each subtask should be completable by one specialist
   - Identify dependencies between subtasks
   - Flag subtasks that can run in parallel

3. **Assign Specialists**: Map each subtask to the best agent:
   - python-developer: Python code, ETL scripts, APIs
   - sql-specialist: SQL queries, data modeling
   - snowflake-specialist: Snowflake-specific features
   - spark-specialist: PySpark, Spark SQL, streaming
   - airflow-specialist: DAGs, scheduling, orchestration
   - aws-specialist: AWS services, Terraform, infrastructure
   - sql-server-specialist: T-SQL, SQL Server features
   - container-specialist: Docker, images, compose
   - kubernetes-specialist: K8s manifests, Helm
   - git-commit-writer: Commit messages
   - documenter: Documentation, READMEs

4. **Create Execution Plan**: Output structured plan with:
   - Ordered task list
   - Agent assignments
   - Dependencies
   - Parallel execution opportunities

## Output Format

```markdown
# Execution Plan: [Task Name]

## Overview
[Brief description]

## Subtasks

### Phase 1: [Name]
| # | Task | Agent | Depends On | Parallel |
|---|------|-------|------------|----------|
| 1 | ... | agent-name | - | No |
| 2 | ... | agent-name | 1 | No |

### Phase 2: [Name]
| # | Task | Agent | Depends On | Parallel |
|---|------|-------|------------|----------|
| 3 | ... | agent-name | 2 | Yes |
| 4 | ... | agent-name | 2 | Yes |

## Execution Order
1. Phase 1: Sequential (1 → 2)
2. Phase 2: Parallel (3, 4)

## Estimated Complexity
[Low | Medium | High]
```

## Example

User: "Create a data pipeline to load CSV files from S3 into Snowflake with Airflow"

Plan:
1. aws-specialist: S3 bucket setup and IAM roles
2. snowflake-specialist: Target table and stage creation
3. python-developer: Python loading script
4. airflow-specialist: DAG for orchestration
5. documenter: Pipeline documentation
