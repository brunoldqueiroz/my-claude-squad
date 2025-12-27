# Agent Catalog

my-claude-squad includes 17 specialized AI agents organized across 4 domains.

## Overview

| Domain | Agent Count | Model Distribution |
|--------|-------------|-------------------|
| Data Engineering | 11 | 10 sonnet, 1 haiku |
| AI Engineering | 4 | 4 sonnet |
| Plugin Development | 1 | 1 sonnet |
| Orchestration | 1 | 1 opus |

**Model Tiers:**
- **Opus** (1 agent): Complex orchestration, task decomposition
- **Sonnet** (15 agents): Technical specialists, code implementation
- **Haiku** (1 agent): Simple utility tasks

## Orchestration

### squad-orchestrator

| Property | Value |
|----------|-------|
| Model | opus |
| Color | blue |

**Purpose:** Master orchestrator for complex, cross-domain tasks.

**Triggers:** `orchestrate`, `coordinate`, `complex task`, `multi-specialist`, `multiple agents`, `decompose task`, `task decomposition`, `cross-domain`

**Use When:**
- Task requires multiple specialists
- Complex multi-step implementations
- Cross-domain work (e.g., data + AI + infrastructure)
- Task decomposition needed

**Example:**
```
"Create a complete data pipeline from S3 to Snowflake with Airflow"
→ Decomposes into: aws-specialist + snowflake-specialist + airflow-specialist
```

## Data Engineering Agents

### python-developer

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | green |

**Purpose:** Python development for data engineering contexts.

**Triggers:** `python`, `pandas`, `polars`, `pytest`, `pydantic`, `fastapi`, `flask`, `sqlalchemy`, `boto3`, `async`, `asyncio`

**Expertise:**
- ETL scripts and data processing
- APIs with FastAPI/Flask
- Testing with pytest
- Type hints and dataclasses

### sql-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | cyan |

**Purpose:** General SQL expertise across databases.

**Triggers:** `sql`, `query`, `cte`, `window function`, `row_number`, `rank`, `lag`, `lead`, `partition by`, `execution plan`, `query optimization`, `index`, `star schema`, `data modeling`

**Expertise:**
- Complex queries with CTEs and window functions
- Query optimization and execution plans
- Data modeling (star schema, SCD)
- Index strategies

### spark-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | orange |

**Purpose:** Apache Spark and PySpark workloads.

**Triggers:** `spark`, `pyspark`, `spark sql`, `databricks`, `delta lake`, `structured streaming`, `rdd`, `dataframe api`, `spark catalyst`, `spark shuffle`

**Expertise:**
- PySpark transformations and actions
- Spark SQL optimization
- Delta Lake tables
- Structured streaming

### snowflake-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | blue |

**Purpose:** Snowflake platform expertise.

**Triggers:** `snowflake`, `snowflake stream`, `snowflake task`, `snowpipe`, `snowpark`, `warehouse`, `time travel`, `data sharing`, `dynamic table`, `micro-partition`, `clustering`

**Expertise:**
- Warehouse sizing and management
- Streams and tasks
- Data sharing and security
- Performance optimization

### airflow-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | yellow |

**Purpose:** Apache Airflow DAG development.

**Triggers:** `airflow`, `dag`, `operator`, `sensor`, `xcom`, `taskflow`, `task group`, `mwaa`, `cloud composer`, `celery executor`, `kubernetes executor`

**Expertise:**
- DAG development patterns
- Custom operators and sensors
- XCom and TaskFlow API
- MWAA and Cloud Composer

### aws-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | orange |

**Purpose:** AWS cloud architecture for data workloads.

**Triggers:** `aws`, `s3`, `lambda`, `glue`, `athena`, `redshift`, `ecs`, `eks`, `ec2`, `iam`, `vpc`, `terraform`, `cloudformation`, `cdk`, `step functions`, `kinesis`, `emr`, `sagemaker`, `lake formation`

**Expertise:**
- Data lake architecture
- Serverless data processing
- Infrastructure as Code
- Security and IAM

### sql-server-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | red |

**Purpose:** Microsoft SQL Server expertise.

**Triggers:** `sql server`, `mssql`, `t-sql`, `tsql`, `stored procedure`, `ssis`, `ssrs`, `ssas`, `always on`, `availability group`, `transactional replication`, `query store`, `columnstore`

**Expertise:**
- T-SQL development
- SSIS packages
- Performance tuning
- High availability

### container-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | purple |

**Purpose:** Docker and container optimization.

**Triggers:** `docker`, `dockerfile`, `container`, `docker compose`, `multi-stage build`, `docker image`, `containerize`, `podman`, `buildkit`, `distroless`, `alpine`

**Expertise:**
- Multi-stage Dockerfiles
- Image optimization
- Docker Compose
- Container security

### kubernetes-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | magenta |

**Purpose:** Kubernetes orchestration for data workloads.

**Triggers:** `kubernetes`, `k8s`, `kubectl`, `helm`, `deployment`, `statefulset`, `daemonset`, `pod`, `service`, `ingress`, `configmap`, `secret`, `hpa`, `eks`, `gke`, `aks`, `kustomize`, `argocd`

**Expertise:**
- Kubernetes manifests
- Helm charts
- Horizontal pod autoscaling
- GitOps with ArgoCD

### documenter

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | cyan |

**Purpose:** Technical documentation.

**Triggers:** `readme`, `documentation`, `document`, `adr`, `architecture decision record`, `data dictionary`, `runbook`, `playbook`, `technical spec`, `docstring`, `mkdocs`, `openapi`, `mermaid diagram`

**Expertise:**
- README files
- Architecture Decision Records
- Data dictionaries
- API documentation

### git-commit-writer

| Property | Value |
|----------|-------|
| Model | haiku |
| Color | gray |

**Purpose:** Conventional commit messages.

**Triggers:** `commit`, `git commit`, `commit message`, `conventional commit`, `semantic commit`

**CRITICAL:** Never includes AI attribution, "Generated by Claude", or Co-Authored-By headers.

## AI Engineering Agents

### rag-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | purple |

**Purpose:** RAG systems and vector databases.

**Triggers:** `rag`, `retrieval augmented generation`, `vector database`, `vectordb`, `chromadb`, `qdrant`, `weaviate`, `pinecone`, `pgvector`, `milvus`, `faiss`, `embedding`, `semantic search`, `llamaindex`, `langchain retriever`, `chunking`, `reranking`

**Expertise:**
- Vector database selection and setup
- Embedding models
- Chunking strategies
- Hybrid search and reranking

### agent-framework-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | orange |

**Purpose:** Multi-agent systems and frameworks.

**Triggers:** `multi-agent`, `langgraph`, `crewai`, `autogen`, `openai swarm`, `agent framework`, `agent workflow`, `agent tools`, `agent memory`, `agent orchestration`, `tool calling`, `function calling`

**Expertise:**
- LangGraph workflows
- CrewAI crews
- AutoGen agents
- Tool and function calling

### llm-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | green |

**Purpose:** LLM integration and prompt engineering.

**Triggers:** `llm`, `large language model`, `openai api`, `anthropic api`, `claude api`, `gpt`, `ollama`, `local llm`, `litellm`, `prompt engineering`, `structured output`, `json mode`, `streaming`, `langfuse`, `token counting`

**Expertise:**
- API integration (OpenAI, Anthropic, Ollama)
- Structured outputs
- Prompt engineering
- Observability (Langfuse, LangSmith)

### automation-specialist

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | yellow |

**Purpose:** AI workflow automation.

**Triggers:** `n8n`, `dify`, `mcp server`, `mcp`, `model context protocol`, `chatbot`, `webhook`, `automation`, `workflow automation`, `zapier`, `make`, `fastapi chatbot`, `websocket chat`, `ai workflow`

**Expertise:**
- n8n and Dify workflows
- MCP server development
- Chatbot implementation
- Webhook integration

## Plugin Development

### plugin-developer

| Property | Value |
|----------|-------|
| Model | sonnet |
| Color | white |

**Purpose:** Create and maintain plugin components.

**Triggers:** `plugin`, `create agent`, `new agent`, `create skill`, `new skill`, `create command`, `new command`, `plugin component`, `plugin validation`, `list agents`, `validate plugin`

**Expertise:**
- Agent file structure
- Skill documentation
- Command templates
- Plugin validation

## Agent Selection Matrix

| Task Type | Primary Agent | Secondary Agents |
|-----------|---------------|------------------|
| Data pipeline development | python-developer | sql-specialist, airflow-specialist |
| Cloud data lake | aws-specialist | spark-specialist |
| Data warehouse | snowflake-specialist | sql-specialist |
| Containerized workloads | container-specialist | kubernetes-specialist |
| RAG application | rag-specialist | llm-specialist |
| Multi-agent system | agent-framework-specialist | llm-specialist |
| Documentation | documenter | (domain-specific agent) |
| Complex cross-domain | squad-orchestrator | (multiple specialists) |

## Agent File Structure

Each agent follows this template:

```markdown
---
name: agent-name
description: |
  When to use this agent.

  Examples:
  <example>
  Context: [Situation]
  user: "[Request]"
  assistant: "[Response]"
  </example>
model: sonnet
color: cyan
---

## Your Role
Responsibility statement.

## Core Expertise
Technology tables and capabilities.

## Implementation Patterns
Code examples.

## Best Practices
Do's and Don'ts.

## RESEARCH-FIRST PROTOCOL
Libraries to verify, research workflow.

## CONTEXT RESILIENCE
Checkpoint format, recovery protocol.

## MEMORY INTEGRATION
Before implementing checklist.
```

## Routing Mechanism

Agents are matched via:

1. **Keyword rules** in coordinator.py (80+ rules)
2. **Trigger extraction** from agent descriptions
3. **Fallback** to squad-orchestrator

The `route_task` tool returns the best-matching agent with confidence level.
