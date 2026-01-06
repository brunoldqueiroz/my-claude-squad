---
description: Generate comprehensive documentation for a data pipeline
argument-hint: [pipeline path or name]
agent: documenter
---

# Document Pipeline

Generate comprehensive documentation for a data pipeline.

## Usage

```
/doc-pipeline [pipeline path or name]
```

If no path provided, analyzes current directory for pipeline components.

## Analysis

1. **Discover Components**:
   - Source connections
   - Transformation logic
   - Target destinations
   - Orchestration (Airflow DAGs)

2. **Extract Metadata**:
   - Column mappings
   - Business logic
   - Dependencies
   - Schedules

3. **Generate Documentation**:
   - README with overview
   - Data flow diagrams
   - Data dictionary
   - Runbook

## Generated Documentation

```
docs/
├── README.md           # Pipeline overview
├── architecture.md     # Architecture details
├── data-dictionary.md  # Column definitions
├── runbook.md         # Operations guide
└── diagrams/
    ├── data-flow.mmd   # Mermaid diagram
    └── architecture.mmd
```

## README Structure

```markdown
# Pipeline: [Name]

## Overview
[Auto-generated description]

## Data Flow
[Mermaid diagram]

## Schedule
- Frequency: [detected schedule]
- SLA: [if specified]

## Sources
| Source | Type | Description |
|--------|------|-------------|
| ... | ... | ... |

## Targets
| Target | Type | Description |
|--------|------|-------------|
| ... | ... | ... |

## Dependencies
- Upstream: [pipelines this depends on]
- Downstream: [pipelines that depend on this]

## Configuration
[Key configuration options]

## Monitoring
- Dashboard: [link]
- Alerts: [channels]

## Contacts
- Owner: [team/person]
- On-call: [rotation]
```

## Data Dictionary

Auto-generates column documentation from:
- SQL table definitions
- DataFrame schemas
- dbt schema.yml files

## Runbook

Creates operational documentation:
- Normal operation steps
- Common issues and fixes
- Recovery procedures
- Escalation paths
