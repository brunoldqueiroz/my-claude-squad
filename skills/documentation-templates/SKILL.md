---
name: documentation-templates
description: Templates for common documentation needs including READMEs, data dictionaries, ADRs, and runbooks.
---

# Documentation Templates

## Overview

This skill provides ready-to-use templates for data engineering documentation.

## README Template

```markdown
# Project Name

[![Build Status](badge-url)](link)
[![Coverage](badge-url)](link)

Brief description of what this project does.

## Quick Start

\`\`\`bash
# Clone and setup
git clone <repo-url>
cd project
make setup

# Run locally
make run
\`\`\`

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

### Purpose
[Explain why this project exists]

### Key Features
- Feature 1
- Feature 2
- Feature 3

### Technology Stack
| Component | Technology |
|-----------|------------|
| Language | Python 3.11 |
| Database | Snowflake |
| Orchestration | Apache Airflow |
| Infrastructure | Terraform |

## Architecture

\`\`\`mermaid
graph LR
    A[Source] --> B[Extract]
    B --> C[Transform]
    C --> D[Load]
    D --> E[Warehouse]
\`\`\`

### Components
- **Component A**: Description
- **Component B**: Description

## Installation

### Prerequisites
- Python 3.11+
- Docker
- AWS CLI

### Setup
\`\`\`bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
\`\`\`

## Configuration

### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | Database connection string |
| `LOG_LEVEL` | No | INFO | Logging level |

### Configuration File
\`\`\`yaml
# config.yaml
database:
  host: localhost
  port: 5432
\`\`\`

## Usage

### Basic Usage
\`\`\`bash
python -m app.main --date 2024-01-01
\`\`\`

### Advanced Options
\`\`\`bash
python -m app.main --date 2024-01-01 --full-refresh
\`\`\`

## Development

### Running Tests
\`\`\`bash
pytest tests/ -v --cov=src
\`\`\`

### Code Quality
\`\`\`bash
make lint
make format
\`\`\`

## Deployment

See [Deployment Guide](docs/deployment.md)

## Troubleshooting

### Common Issues

**Issue**: Connection timeout
**Solution**: Check network connectivity and firewall rules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit PR

## License

MIT License
```

## Data Dictionary Template

```markdown
# Data Dictionary: [Domain Name]

## Document Information
| | |
|---|---|
| **Version** | 1.0 |
| **Last Updated** | YYYY-MM-DD |
| **Owner** | Team Name |

## Overview

[Brief description of the data domain]

## Entity Relationship Diagram

\`\`\`mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_LINE : contains
\`\`\`

## Tables

### Table: orders

**Description**: Customer order transactions
**Location**: database.schema.orders
**Grain**: One row per order
**Update Frequency**: Real-time
**Retention**: 7 years

#### Columns

| Column | Type | Nullable | Description | Example | Source |
|--------|------|----------|-------------|---------|--------|
| order_id | VARCHAR(36) | No | Unique order identifier | `abc-123` | Generated |
| customer_id | INT | No | FK to customers | `12345` | source.orders |
| order_date | TIMESTAMP | No | Order creation time | `2024-01-15 14:30:00` | source.orders |
| total_amount | DECIMAL(12,2) | No | Total order value | `299.99` | Calculated |
| status | VARCHAR(20) | No | Order status | `completed` | source.orders |

#### Valid Values

| Column | Valid Values |
|--------|--------------|
| status | `pending`, `processing`, `completed`, `cancelled` |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| pk_orders | order_id | Primary Key |
| idx_orders_customer | customer_id | Non-clustered |
| idx_orders_date | order_date | Non-clustered |

#### Data Quality Rules

| Rule ID | Column | Rule | Threshold |
|---------|--------|------|-----------|
| DQ001 | order_id | Not null | 0% |
| DQ002 | order_id | Unique | 0% |
| DQ003 | total_amount | >= 0 | 0% |

## Lineage

\`\`\`
source.orders → stg_orders → fact_orders
                              ↑
source.customers → stg_customers → dim_customer
\`\`\`

## Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2024-01-15 | 1.0 | Initial version | Name |
```

## Architecture Decision Record (ADR) Template

```markdown
# ADR-[NUMBER]: [TITLE]

## Status

[Proposed | Accepted | Deprecated | Superseded]

## Date

YYYY-MM-DD

## Context

[Describe the issue motivating this decision. What is the problem?]

## Decision

[Describe our response to these forces. State the decision.]

## Alternatives Considered

### Alternative 1: [Name]

**Pros:**
- Pro 1
- Pro 2

**Cons:**
- Con 1
- Con 2

### Alternative 2: [Name]

**Pros:**
- Pro 1

**Cons:**
- Con 1

## Consequences

### Positive
- Positive consequence 1
- Positive consequence 2

### Negative
- Negative consequence 1
- Negative consequence 2

### Risks
- Risk 1 (mitigation: ...)
- Risk 2 (mitigation: ...)

## Implementation Notes

[Any relevant implementation details]

## References

- [Link 1](url)
- [Link 2](url)
```

## Runbook Template

```markdown
# Runbook: [Pipeline/System Name]

## Overview

**Purpose**: [What this pipeline does]
**Owner**: [Team/Person]
**On-Call**: [Contact info]

## Schedule

| Attribute | Value |
|-----------|-------|
| Frequency | Daily at 06:00 UTC |
| Duration | ~45 minutes |
| SLA | Complete by 08:00 UTC |

## Architecture

\`\`\`mermaid
graph LR
    A[Source] --> B[Extract]
    B --> C[Transform]
    C --> D[Load]
\`\`\`

## Prerequisites

- [ ] Source system available
- [ ] Target database accessible
- [ ] Required credentials configured

## Normal Operation

### Step 1: Monitor Start
\`\`\`bash
# Check DAG triggered
airflow dags list-runs -d pipeline_name
\`\`\`

### Step 2: Verify Completion
[Steps to verify successful completion]

## Monitoring

### Dashboards
- [Grafana Dashboard](url)
- [Airflow UI](url)

### Key Metrics
| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| Duration | 40-50 min | > 60 min |
| Rows | 100k-150k | < 50k or > 200k |

## Troubleshooting

### Issue: Pipeline Failed to Start

**Symptoms**: No tasks running at scheduled time

**Diagnosis**:
\`\`\`bash
# Check scheduler
airflow scheduler status

# Check DAG
airflow dags show pipeline_name
\`\`\`

**Resolution**:
1. Restart scheduler if down
2. Unpause DAG if paused
3. Check for dependency issues

### Issue: Extract Task Failed

**Symptoms**: Extract task shows failed

**Diagnosis**:
\`\`\`bash
# View logs
airflow tasks logs pipeline_name extract 2024-01-15
\`\`\`

**Resolution**:
1. Check source connectivity
2. Verify credentials
3. Check for schema changes

## Recovery Procedures

### Full Rerun
\`\`\`bash
airflow dags trigger pipeline_name --conf '{"date": "2024-01-15"}'
\`\`\`

### Partial Rerun
\`\`\`bash
airflow tasks clear pipeline_name -t transform -s 2024-01-15
\`\`\`

## Escalation

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call | Initial response |
| L2 | Team lead | > 30 min unresolved |
| L3 | Platform team | Infrastructure issues |

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2024-01-15 | Created | Name |
```

## API Documentation Template

```markdown
# API Documentation: [API Name]

## Overview

[Brief description of the API]

**Base URL**: `https://api.example.com/v1`
**Authentication**: Bearer token

## Endpoints

### Get Orders

Retrieve a list of orders.

**Endpoint**: `GET /orders`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| start_date | date | No | Filter from date |
| end_date | date | No | Filter to date |
| status | string | No | Filter by status |
| limit | int | No | Max results (default: 100) |

**Request**:
\`\`\`bash
curl -X GET "https://api.example.com/v1/orders?status=completed" \
  -H "Authorization: Bearer <token>"
\`\`\`

**Response**:
\`\`\`json
{
  "orders": [
    {
      "order_id": "abc-123",
      "customer_id": 12345,
      "amount": 299.99,
      "status": "completed"
    }
  ],
  "total": 1,
  "page": 1
}
\`\`\`

**Status Codes**:
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid parameters |
| 401 | Unauthorized |
| 500 | Server error |

### Create Order

Create a new order.

**Endpoint**: `POST /orders`

**Request Body**:
\`\`\`json
{
  "customer_id": 12345,
  "items": [
    {"product_id": "prod-1", "quantity": 2}
  ]
}
\`\`\`

**Response**:
\`\`\`json
{
  "order_id": "abc-123",
  "status": "pending"
}
\`\`\`

## Error Responses

All errors follow this format:
\`\`\`json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Description of the error"
  }
}
\`\`\`

## Rate Limits

| Tier | Requests/min |
|------|--------------|
| Free | 60 |
| Pro | 600 |

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-15 | Initial release |
```

## Anti-Patterns

### 1. Documentation Sprawl
- **What it is**: Documentation scattered across wikis, READMEs, Confluence, emails
- **Why it's wrong**: Information is hard to find; duplicates become inconsistent
- **Correct approach**: Single source of truth; docs-as-code in the same repo

### 2. Write-Once Documentation
- **What it is**: Documentation written at project start, never updated
- **Why it's wrong**: Becomes outdated and misleading; worse than no docs
- **Correct approach**: Update docs as part of PR process; review regularly

### 3. No Examples
- **What it is**: Documentation that describes but doesn't show
- **Why it's wrong**: Users can't copy-paste; concepts remain abstract
- **Correct approach**: Include runnable examples for every feature

### 4. Assuming Context
- **What it is**: Documentation that assumes reader knows the background
- **Why it's wrong**: Onboarding is difficult; knowledge silos form
- **Correct approach**: Write for newcomers; explain "why" not just "what"

### 5. Missing Runbooks
- **What it is**: No operational documentation for incidents
- **Why it's wrong**: On-call struggles; incidents take longer to resolve
- **Correct approach**: Document common issues, diagnosis steps, and fixes

---

## Best Practices

1. **Keep documentation close to code** - In the same repo
2. **Update with changes** - Part of PR process
3. **Use consistent templates** - Easy to navigate
4. **Include examples** - Copy-paste ready
5. **Version documentation** - Track changes
6. **Link related docs** - Easy navigation
7. **Review regularly** - Keep accurate
