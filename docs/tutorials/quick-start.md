# Quick Start Tutorial

This tutorial walks you through common use cases for my-claude-squad.

## Prerequisites

Ensure you have installed and registered the MCP server:

```bash
uv sync
claude mcp add squad uv run squad-mcp
```

## Tutorial 1: Routing Tasks to Agents

The simplest way to use the squad is to let it automatically route tasks to the best agent.

### Step 1: List Available Agents

```
You: What agents are available?
```

Claude will use `mcp__squad__list_agents` and show all 17 agents with their specialties.

### Step 2: Route a Task

```
You: I need to optimize a slow Snowflake query
```

Claude will use `mcp__squad__route_task` to identify `snowflake-specialist` as the best match.

### Step 3: Spawn the Agent

```
You: Yes, use the snowflake-specialist to help me
```

Claude will use `mcp__squad__spawn_agent` to create a task for the agent.

## Tutorial 2: Decomposing Complex Tasks

For tasks that require multiple specialists, use task decomposition.

### Step 1: Request Decomposition

```
You: Create a data pipeline from S3 to Snowflake with Airflow orchestration
```

Claude will use `mcp__squad__decompose_task` to analyze the task.

### Step 2: Review the Plan

Claude will present a breakdown like:

1. **Extract from S3** → aws-specialist
2. **Transform data** → spark-specialist
3. **Load to Snowflake** → snowflake-specialist
4. **Create Airflow DAG** → airflow-specialist

### Step 3: Execute the Workflow

```
You: Proceed with the plan
```

Claude will use `mcp__squad__submit_decomposition` to create the workflow.

### Step 4: Track Progress

```
You: What tasks are ready to execute?
```

Claude will use `mcp__squad__get_ready_tasks` to show available tasks.

## Tutorial 3: Creating a Swarm

Swarms coordinate multiple agents with specific communication patterns.

### Step 1: Create a Ring Pipeline

```
You: Create a ring swarm called "ETL Pipeline" with aws-specialist, spark-specialist, and snowflake-specialist
```

Claude will use `mcp__squad__create_swarm` with `topology="ring"`.

### Step 2: Create Workflow from Swarm

```
You: Create a workflow for this swarm to process daily transactions
```

Claude will use `mcp__squad__create_swarm_workflow` to generate sequential tasks.

### Step 3: Check Delegation

```
You: If aws-specialist needs to delegate, where does the task go?
```

Claude will use `mcp__squad__get_swarm_delegation` to show the ring routing (aws → spark → snowflake).

## Tutorial 4: Managing Sessions

Sessions provide persistent, resumable workflows.

### Step 1: Create a Session

```
You: Create a session called "Q4 Data Migration" with three tasks:
1. Audit current data (documenter)
2. Create migration scripts (python-developer)
3. Update documentation (documenter)
```

Claude will use `mcp__squad__create_session`.

### Step 2: Start a Task

```
You: Start the first task
```

Claude will use `mcp__squad__start_session_task`.

### Step 3: Complete the Task

```
You: The audit is complete, here are the findings: [...]
```

Claude will use `mcp__squad__complete_session_task`.

### Step 4: Check Progress

```
You: How is the session progressing?
```

Claude will use `mcp__squad__get_session_progress` to show completion percentage.

### Step 5: Pause and Resume

```
You: I need to pause this work for now
```

Claude will use `mcp__squad__pause_session`. Later:

```
You: Resume the Q4 Data Migration session
```

Claude will use `mcp__squad__resume_session` to continue from where you left off.

## Tutorial 5: Using Semantic Memory

Store knowledge for later retrieval by meaning.

### Step 1: Store Patterns

```
You: Remember this pattern: "Always use incremental loads for fact tables to reduce processing time"
```

Claude will use `mcp__squad__semantic_store`.

### Step 2: Store More Knowledge

```
You: Also remember: "Use SCD Type 2 for dimension tables that need history tracking"
```

### Step 3: Search by Meaning

```
You: What do we know about efficient data loading strategies?
```

Claude will use `mcp__squad__semantic_search` to find relevant memories, even without exact keyword matches.

### Step 4: Check Statistics

```
You: How much is stored in semantic memory?
```

Claude will use `mcp__squad__semantic_stats` to show counts and namespaces.

## Tutorial 6: Using Command Tools

The squad includes utility tools for common tasks.

### Generate a Dockerfile

```
You: Create an optimized Dockerfile for a Python 3.11 project
```

Claude will use `mcp__squad__create_dockerfile`.

### Generate Kubernetes Manifests

```
You: Create K8s manifests for an app called "data-processor" with 3 replicas
```

Claude will use `mcp__squad__create_k8s_manifest`.

### Scaffold a RAG Application

```
You: Create a RAG application structure using Qdrant and LangChain
```

Claude will use `mcp__squad__scaffold_rag`.

### Analyze SQL Query

```
You: Analyze this SQL for optimization issues:
SELECT * FROM orders WHERE created_at > '2024-01-01'
```

Claude will use `mcp__squad__analyze_query` to identify issues (SELECT *, missing index, etc.).

## Tutorial 7: Monitoring and Health

Track system and agent health.

### Check System Health

```
You: What's the health status of the squad?
```

Claude will use `mcp__squad__get_health`.

### Check Agent Health

```
You: How is the python-developer agent performing?
```

Claude will use `mcp__squad__get_agent_health` to show success rate, health score, and execution times.

### View Recent Events

```
You: Show me recent task completions
```

Claude will use `mcp__squad__get_events` with `event_type="task_complete"`.

### Check Storage

```
You: How big is the squad database?
```

Claude will use `mcp__squad__get_storage_stats` to show table sizes.

## Next Steps

- Read the [Architecture](../architecture.md) to understand the system design
- Check the [API Reference](../api-reference.md) for all 64 tools
- See the [Agent Catalog](../agents.md) for all 17 agents
- Read the [Developer Guide](../developer-guide.md) to add new agents
