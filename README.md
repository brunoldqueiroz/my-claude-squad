# My Claude Squad

A comprehensive Claude Code plugin containing 19 specialized AI agents for Data Engineering, AI Engineering, and Plugin Development workflows.

## Overview

This plugin provides a team of AI specialists that work together to help with data engineering tasks. The **Planner Orchestrator** can decompose complex tasks and coordinate multiple agents to work in parallel.

## Key Features

### Research-First Protocol
All agents verify their knowledge before acting:
- Use **Context7** for up-to-date library documentation
- Use **Exa** for code examples and best practices
- Declare uncertainty and ask when critical decisions are needed
- Validate syntax against current documentation

### Context Resilience
Agents maintain effectiveness after context compaction:
- Structured output with file paths and summaries
- Checkpoint patterns for multi-phase work
- Recovery protocols for resuming after context loss
- File-based artifacts instead of conversation-only state

### Memory Integration
Agents leverage multiple memory tiers:
- **Session Memory**: TodoWrite for task tracking
- **Project Memory**: CLAUDE.md and codebase patterns
- **Skills Memory**: Reference established patterns
- **External Knowledge**: Context7 and Exa for current docs

## Agents

### Data Engineering Agents
| Agent | Specialty | Color |
|-------|-----------|-------|
| `planner-orchestrator` | Task decomposition & parallel management | blue |
| `python-developer` | Python for data engineering | green |
| `sql-specialist` | General SQL expertise | cyan |
| `snowflake-specialist` | Snowflake platform | blue |
| `spark-specialist` | Apache Spark/PySpark | orange |
| `airflow-specialist` | Apache Airflow DAGs | yellow |
| `aws-specialist` | AWS cloud architecture | orange |
| `sql-server-specialist` | Microsoft SQL Server | red |
| `container-specialist` | Docker/containers | purple |
| `kubernetes-specialist` | Kubernetes orchestration | magenta |
| `git-commit-writer` | Conventional commits | gray |
| `documenter` | Technical documentation | cyan |

### AI Engineering Agents
| Agent | Specialty | Color |
|-------|-----------|-------|
| `ai-orchestrator` | AI project coordination & planning | magenta |
| `rag-specialist` | RAG, vector databases, embeddings | purple |
| `agent-framework-specialist` | LangGraph, CrewAI, AutoGen | orange |
| `llm-specialist` | LLM integration, Ollama, prompts | green |
| `automation-specialist` | n8n, Dify, MCP servers, chatbots | yellow |

### Plugin Development Agents
| Agent | Specialty | Color |
|-------|-----------|-------|
| `plugin-architect` | Plugin extension design & domain planning | pink |
| `plugin-developer` | Agent/skill/command creation | white |

## Commands

### Orchestration
- `/plan-task` - Analyze a task and create execution plan with agent assignments
- `/execute-squad` - Execute the planned task using assigned agents
- `/status` - Show current task status and agent progress

### Data Engineering
- `/create-pipeline` - Generate data pipeline boilerplate (ETL/ELT)
- `/optimize-query` - Analyze and optimize SQL query
- `/analyze-data` - Profile and analyze dataset

### DevOps
- `/deploy` - Generate deployment configuration
- `/containerize` - Create Dockerfile for project
- `/k8s-manifest` - Generate Kubernetes manifests

### Documentation
- `/doc-pipeline` - Document a data pipeline
- `/doc-api` - Generate API documentation
- `/commit` - Generate conventional commit message

### Research
- `/lookup-docs` - Look up documentation for any library using Context7 and Exa

### AI Engineering
- `/create-rag` - Generate RAG application boilerplate
- `/create-agent` - Generate multi-agent system structure
- `/create-chatbot` - Generate chatbot application
- `/create-mcp-server` - Generate MCP server template
- `/optimize-rag` - Analyze and optimize RAG pipeline

### Plugin Development
- `/new-agent` - Create a new specialist agent
- `/new-skill` - Create a new SKILL.md reference
- `/new-command` - Create a new slash command
- `/list-agents` - List all agents with models and descriptions
- `/list-commands` - List all commands by category
- `/validate-plugin` - Validate plugin structure and files
- `/update-readme` - Regenerate README from current state
- `/plugin-status` - Show plugin statistics and health

## Skills

The plugin includes reference skills for agents:

- **research-patterns/** - Research-first protocols, uncertainty handling, Context7/Exa usage
- **data-pipeline-patterns/** - ETL/ELT patterns, batch vs streaming, idempotency
- **sql-optimization/** - Query optimization, index strategies, anti-patterns
- **cloud-architecture/** - Data lake, lakehouse, serverless patterns
- **testing-strategies/** - Unit testing, integration testing, data quality
- **documentation-templates/** - Pipeline docs, data dictionaries, ADRs
- **code-review-standards/** - Python, SQL, infrastructure checklists
- **ai-engineering-patterns/** - RAG, multi-agent, LLM integration, MCP patterns
- **plugin-development-patterns/** - Agent/skill/command templates, plugin conventions

## Installation

### Option 1: Install from Local Path
```bash
claude --plugin-dir /path/to/my-claude-squad
```

### Option 2: Copy to Claude Plugins Directory
```bash
cp -r my-claude-squad ~/.claude/plugins/
```

## Testing

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests (344 tests)
uv run pytest

# Run with coverage report
uv run pytest --cov=orchestrator --cov-report=html

# Run unit tests only
uv run pytest tests/unit/
```

**Test Coverage:** 93% overall (344 tests across 12 test modules)

## Usage Examples

### Using the Planner for Complex Tasks
```
"Create a complete data pipeline from Snowflake to SQL Server with Airflow scheduling"
```

The planner will:
1. Break down the task into subtasks
2. Assign appropriate specialists
3. Coordinate parallel execution
4. Consolidate results

### Using Individual Agents
```
"Write a PySpark job to transform customer data"
→ Triggers spark-specialist

"Create an Airflow DAG for daily ETL"
→ Triggers airflow-specialist

"Optimize this SQL query for Snowflake"
→ Triggers snowflake-specialist
```

### Using Commands
```
/create-pipeline snowflake-to-sqlserver
/optimize-query src/queries/customer_report.sql
/commit
```

### Using AI Engineering Agents
```
"Build a RAG chatbot with Qdrant and LangChain"
→ Triggers ai-orchestrator to coordinate rag-specialist and automation-specialist

"Create a LangGraph workflow with research and writing agents"
→ Triggers agent-framework-specialist

"Set up Ollama with structured outputs for data extraction"
→ Triggers llm-specialist

"Build an MCP server to expose our database to Claude"
→ Triggers automation-specialist
```

### Using Plugin Development Agents
```
"Add ML Ops agents for model training and deployment"
→ Triggers plugin-architect to design the domain

"Create a dbt-specialist agent"
→ Triggers plugin-developer

/new-agent terraform-specialist --domain devops
/list-agents
/plugin-status
```

## Tech Stack Coverage

### Data Engineering
- **Languages**: Python, SQL, T-SQL
- **Data Platforms**: Snowflake, SQL Server, Delta Lake
- **Processing**: Apache Spark, pandas, polars
- **Orchestration**: Apache Airflow, MWAA
- **Cloud**: AWS (S3, Glue, Athena, Redshift, Lambda, ECS, EKS)
- **Containers**: Docker, Kubernetes, Helm
- **IaC**: Terraform, CloudFormation, CDK
- **Tools**: dbt, Great Expectations, pytest

### AI Engineering
- **LLM Providers**: OpenAI, Anthropic, Ollama, LiteLLM
- **Agent Frameworks**: LangGraph, LangChain, CrewAI, AutoGen
- **Vector Databases**: Qdrant, Weaviate, ChromaDB, Pinecone, pgvector
- **RAG Frameworks**: LlamaIndex, LangChain
- **Automation**: n8n, Dify, MCP servers
- **Observability**: Langfuse, LangSmith
- **Evaluation**: RAGAS, DeepEval

## MCP Orchestrator

This plugin includes a custom Python MCP server that coordinates all 19 agents with persistent memory.

### Architecture

```
orchestrator/
├── server.py           # FastMCP entry point, 21 MCP tools, singleton getters
├── coordinator.py      # Task routing (80+ keyword rules), decomposition
├── agent_registry.py   # Loads agents/*.md, extracts triggers
├── memory.py           # DuckDB storage - 5 tables
├── scheduler.py        # TaskScheduler with dependencies, CircuitBreaker
├── agent_state.py      # AgentStateManager - health tracking, heartbeats
├── events.py           # EventBus with sync/async handlers
├── metrics.py          # MetricsCollector - counters, gauges, histograms
├── retry.py            # Exponential backoff with jitter
├── config.py           # Environment config loading
├── tracing.py          # Langfuse observability
└── types.py            # Pydantic models
```

### Installation

```bash
# Install dependencies
cd /path/to/my-claude-squad
uv sync

# Register MCP server with Claude Code
claude mcp add squad uv run squad-mcp
```

### MCP Tools (21 total)

**Agent Tools:**
| Tool | Description |
|------|-------------|
| `list_agents` | List all 19 agents with specialties |
| `route_task` | Auto-select best agent for task |
| `spawn_agent` | Spawn agent by name with task |
| `decompose_task` | Break complex task into subtasks |

**Memory Tools:**
| Tool | Description |
|------|-------------|
| `memory_store` | Store key-value in DuckDB with namespace |
| `memory_query` | Query memory by pattern |

**Task Scheduling:**
| Tool | Description |
|------|-------------|
| `create_dependent_task` | Create task with dependencies |
| `get_task_graph` | Get DAG of scheduled tasks |
| `get_ready_tasks` | Get tasks with satisfied dependencies |
| `complete_scheduled_task` | Mark task complete, unlock dependents |
| `execute_workflow` | Create multiple tasks with dependencies |
| `clear_workflow` | Clear all scheduled tasks |

**Agent Health:**
| Tool | Description |
|------|-------------|
| `get_agent_health` | Get health status for one/all agents |
| `set_agent_status` | Set agent status (idle, busy, paused, error, offline) |

**Status/Metrics:**
| Tool | Description |
|------|-------------|
| `swarm_status` | Show active agents and stats |
| `complete_run` | Mark task as completed |
| `get_health` | System health check |
| `get_metrics` | Get counters, gauges, histograms |

**Events:**
| Tool | Description |
|------|-------------|
| `get_events` | Get recent events with filtering |
| `emit_event` | Emit custom event to event bus |

### Usage

Once registered, Claude Code can use the orchestrator tools:

```
You: "What agents are available?"
→ Claude uses list_agents tool

You: "Route this task to the best agent: optimize Snowflake query"
→ Claude uses route_task tool → recommends snowflake-specialist

You: "Create a data pipeline from S3 to Snowflake with Airflow"
→ Claude uses decompose_task tool → breaks into subtasks with agent assignments
```

### Persistent Memory

The orchestrator stores state in `.swarm/memory.duckdb` (5 tables):

- **memories**: Key-value storage with namespaces and metadata
- **agent_runs**: History of all agent executions with tokens/results
- **task_log**: Task status and results
- **agent_health**: Runtime health state (status, health_score, success/error counts)
- **agent_events**: Event log (heartbeats, status changes, errors)

```
You: "Store this pattern for later: use incremental loads for fact tables"
→ Claude uses memory_store tool

You: "What patterns do we have for data loading?"
→ Claude uses memory_query with pattern "load"
```

### Features

- **Keyword Routing**: Matches tasks to agents by keywords and descriptions
- **Task Decomposition**: Splits complex tasks into agent-assigned subtasks
- **Task Dependencies**: DAG-based workflow execution with topological sorting
- **CircuitBreaker**: Fault tolerance with automatic recovery (CLOSED → OPEN → HALF_OPEN)
- **Agent Health**: Health scores, heartbeats, stale detection
- **EventBus**: Sync/async event handlers with history and filtering
- **MetricsCollector**: Counters, gauges, histograms, timers
- **DuckDB Memory**: Fast analytical queries on run history (5 tables)
- **Agent Registry**: Auto-discovers agents from `agents/*.md` files
- **Run Tracking**: Logs all agent executions with status and tokens
- **Langfuse Tracing**: Optional observability integration

## License

MIT
