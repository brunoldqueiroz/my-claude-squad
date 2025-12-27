---
name: cloud-architecture
description: Cloud architecture patterns for data platforms including data lakes, lakehouses, and cost optimization.
---

# Cloud Architecture Patterns

## Overview

This skill provides patterns for building scalable, cost-effective data platforms on cloud infrastructure.

## Data Lake Architecture

### Medallion Architecture (Bronze/Silver/Gold)

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA LAKE                             │
├──────────────┬──────────────────┬──────────────────────────┤
│    BRONZE    │      SILVER      │          GOLD            │
│   (Raw)      │   (Validated)    │       (Business)         │
├──────────────┼──────────────────┼──────────────────────────┤
│ • Raw files  │ • Cleaned data   │ • Aggregates            │
│ • All data   │ • Typed schemas  │ • Business entities     │
│ • Immutable  │ • Deduplicated   │ • Ready for consumption │
│ • Append-only│ • Standardized   │ • Optimized for queries │
└──────────────┴──────────────────┴──────────────────────────┘
```

### S3 Bucket Structure
```
s3://data-lake/
├── bronze/
│   ├── source_system_1/
│   │   └── table_name/
│   │       └── year=2024/month=01/day=15/
│   └── source_system_2/
├── silver/
│   ├── domain_1/
│   │   └── entity/
│   └── domain_2/
└── gold/
    ├── reports/
    └── ml_features/
```

## Lakehouse Architecture

### Key Components
- **Open Table Formats**: Delta Lake, Apache Iceberg, Apache Hudi
- **Unified Processing**: Spark, Flink, Presto/Trino
- **Governance**: Unity Catalog, Lake Formation
- **Query Engines**: Athena, Presto, Spark SQL

### Benefits
- ACID transactions on data lake
- Schema enforcement and evolution
- Time travel capabilities
- Unified batch and streaming

## Serverless Data Platform

```
┌─────────────────────────────────────────────────────────────┐
│                     INGESTION                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐                 │
│  │ Kinesis │  │  MSK    │  │ API Gateway │                 │
│  │ Firehose│  │(Kafka)  │  │  + Lambda   │                 │
│  └────┬────┘  └────┬────┘  └──────┬──────┘                 │
└───────┼────────────┼──────────────┼─────────────────────────┘
        └────────────┼──────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                     STORAGE                                  │
│                  ┌───────────┐                               │
│                  │    S3     │                               │
│                  │ Data Lake │                               │
│                  └─────┬─────┘                               │
└────────────────────────┼────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   PROCESSING                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Glue    │  │  EMR     │  │  Lambda  │                  │
│  │  ETL     │  │Serverless│  │ Functions│                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    SERVING                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Athena  │  │ Redshift │  │   APIs   │                  │
│  │          │  │Serverless│  │          │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Multi-Cloud Strategy

### Considerations
- **Data Gravity**: Process data where it lives
- **Egress Costs**: Minimize cross-cloud transfers
- **Portability**: Use open formats and standards
- **Governance**: Unified catalog across clouds

### Tools for Multi-Cloud
- Apache Iceberg (open table format)
- dbt (transformation layer)
- Airbyte/Fivetran (ingestion)
- Terraform (infrastructure)

## Cost Optimization

### Storage Optimization
| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Lifecycle policies | 30-60% | Move to IA/Glacier |
| Compression | 50-80% | Parquet with Snappy/ZSTD |
| Partitioning | 80-90%+ | Reduce data scanned |
| Intelligent Tiering | 20-40% | Automatic tier selection |

### Compute Optimization
| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Spot instances | 60-90% | Fault-tolerant workloads |
| Auto-scaling | 30-50% | Scale with demand |
| Reserved capacity | 30-60% | Predictable workloads |
| Right-sizing | 20-40% | Match resources to need |

### Query Optimization
| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Columnar formats | 80-90% | Parquet/ORC |
| Partition pruning | 50-90% | Filter on partition keys |
| Result caching | 90%+ | Athena/Snowflake caching |
| Aggregation tables | 70-90% | Pre-compute summaries |

## Security Patterns

### Defense in Depth
```
┌─────────────────────────────────────────┐
│            Network Security              │
│  ┌───────────────────────────────────┐  │
│  │         Identity (IAM)            │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │     Encryption at Rest      │  │  │
│  │  │  ┌───────────────────────┐  │  │  │
│  │  │  │ Encryption in Transit │  │  │  │
│  │  │  │  ┌─────────────────┐  │  │  │  │
│  │  │  │  │   DATA          │  │  │  │  │
│  │  │  │  └─────────────────┘  │  │  │  │
│  │  │  └───────────────────────┘  │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Key Practices
- **Least Privilege**: Minimal required permissions
- **VPC Endpoints**: Private connectivity
- **KMS**: Customer-managed encryption keys
- **Audit Logging**: CloudTrail, VPC Flow Logs
- **Secrets Management**: Secrets Manager, Vault

## High Availability

### Multi-AZ Architecture
```
┌────────────────────────────────────────┐
│              Region (us-east-1)         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  AZ-1a  │ │  AZ-1b  │ │  AZ-1c  │  │
│  │ Compute │ │ Compute │ │ Compute │  │
│  │   ↓     │ │   ↓     │ │   ↓     │  │
│  │ Storage │ │ Storage │ │ Storage │  │
│  └────┬────┘ └────┬────┘ └────┬────┘  │
│       └──────────┬┴───────────┘        │
│                  ↓                      │
│            Cross-AZ Replication         │
└────────────────────────────────────────┘
```

### Recovery Patterns
| Pattern | RTO | RPO | Cost |
|---------|-----|-----|------|
| Backup & Restore | Hours | Hours | $ |
| Pilot Light | 10-30 min | Minutes | $$ |
| Warm Standby | Minutes | Seconds | $$$ |
| Active-Active | Near-zero | Near-zero | $$$$ |

## Observability

### Three Pillars
1. **Metrics**: CloudWatch, Prometheus, Datadog
2. **Logs**: CloudWatch Logs, ELK, Splunk
3. **Traces**: X-Ray, Jaeger, Zipkin

### Data Pipeline Monitoring
- Job success/failure rates
- Processing latency (end-to-end)
- Data freshness (staleness)
- Data quality scores
- Resource utilization
- Cost tracking

## Anti-Patterns

### 1. Lift-and-Shift Without Optimization
- **What it is**: Moving on-prem workloads to cloud without redesigning for cloud-native
- **Why it's wrong**: Misses cost savings and scalability benefits; often costs more
- **Correct approach**: Evaluate and refactor for managed services, serverless, auto-scaling

### 2. Single Region Without DR
- **What it is**: Running all infrastructure in one region with no disaster recovery
- **Why it's wrong**: Region outages cause complete service unavailability
- **Correct approach**: Multi-AZ at minimum; multi-region for critical workloads

### 3. Over-Provisioning Resources
- **What it is**: Running large instances 24/7 regardless of actual usage
- **Why it's wrong**: Wastes money; typical utilization is 20-30%
- **Correct approach**: Right-size instances; use auto-scaling; leverage spot/preemptible

### 4. Data Egress Ignorance
- **What it is**: Designing without considering cross-region/cross-cloud data transfer costs
- **Why it's wrong**: Data egress costs can dominate cloud bills
- **Correct approach**: Process data where it lives; use VPC endpoints; cache strategically

### 5. No Cost Allocation Tags
- **What it is**: Resources without proper tagging for cost attribution
- **Why it's wrong**: Cannot identify cost drivers; no accountability
- **Correct approach**: Enforce tagging policies; automate tag compliance

---

## Best Practices

1. **Design for failure** - Assume components will fail
2. **Automate everything** - Infrastructure as Code
3. **Monitor costs** - Set budgets and alerts
4. **Use managed services** - Reduce operational burden
5. **Implement governance** - Catalog, lineage, access control
6. **Plan for scale** - Design for 10x growth
7. **Document architecture** - Diagrams and decision records
