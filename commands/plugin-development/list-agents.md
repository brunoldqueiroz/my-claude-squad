---
name: list-agents
description: List all agents in the plugin with descriptions and models
agent: plugin-developer
arguments: []
---

# List Agents

Display all agents in the plugin with their models, colors, and descriptions.

## Usage

```
/list-agents
```

## Agent Assignment

This command uses the **plugin-developer** agent.

## Output Format

```markdown
# Plugin Agents

## Summary
- Total: [count] agents
- Opus: [count] (orchestrators)
- Sonnet: [count] (specialists)
- Haiku: [count] (utilities)

## Orchestrator

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| squad-orchestrator | opus | blue | Master orchestrator for all domains |

## Data Engineering Agents

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| python-developer | sonnet | green | Python, ETL, APIs |
| sql-specialist | sonnet | cyan | SQL queries & optimization |
| ... | ... | ... | ... |

## AI Engineering Agents

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| rag-specialist | sonnet | purple | RAG, vector databases |
| ... | ... | ... | ... |

## Plugin Development Agents

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| plugin-developer | sonnet | white | Component creation |
```

## What Gets Analyzed

The command reads:
- All files in `agents/` directory
- YAML frontmatter from each file
- First line of description for summary

## Example Output

```markdown
# Plugin Agents

## Summary
- Total: 17 agents
- Opus: 1 (orchestrator)
- Sonnet: 15 (specialists)
- Haiku: 1 (utilities)

## Orchestrator

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| squad-orchestrator | opus | blue | Master orchestrator for all domains |

## Data Engineering Agents

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| python-developer | sonnet | green | Python for data engineering |
| sql-specialist | sonnet | cyan | General SQL expertise |
| snowflake-specialist | sonnet | blue | Snowflake platform |
| spark-specialist | sonnet | orange | Apache Spark/PySpark |
| airflow-specialist | sonnet | yellow | Apache Airflow DAGs |
| aws-specialist | sonnet | orange | AWS cloud architecture |
| sql-server-specialist | sonnet | red | Microsoft SQL Server |
| container-specialist | sonnet | purple | Docker/containers |
| kubernetes-specialist | sonnet | magenta | Kubernetes orchestration |
| git-commit-writer | haiku | gray | Conventional commits |
| documenter | sonnet | cyan | Technical documentation |

## AI Engineering Agents

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| rag-specialist | sonnet | purple | RAG, vector databases, embeddings |
| agent-framework-specialist | sonnet | orange | LangGraph, CrewAI, AutoGen |
| llm-specialist | sonnet | green | LLM integration, Ollama, prompts |
| automation-specialist | sonnet | yellow | n8n, Dify, MCP servers |

## Plugin Development Agents

| Agent | Model | Color | Description |
|-------|-------|-------|-------------|
| plugin-developer | sonnet | white | Component creation |
```

## See Also

- `/list-commands` - List all commands
- `/plugin-status` - Show full statistics
- `/validate-plugin` - Validate plugin structure
