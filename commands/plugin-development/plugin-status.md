---
name: plugin-status
description: Show plugin statistics and health
arguments: []
---

# Plugin Status

Display comprehensive plugin statistics and health information.

## Usage

```
/plugin-status
```

## Agent Assignment

This command uses the **plugin-developer** agent.

## Output Format

```markdown
# Plugin Status

## Overview
- **Name**: my-claude-squad
- **Version**: 1.0.0
- **Total Components**: [count]

## Agents

| Model | Count | Agents |
|-------|-------|--------|
| opus | 3 | planner-orchestrator, ai-orchestrator, plugin-architect |
| sonnet | 15 | python-developer, sql-specialist, ... |
| haiku | 1 | git-commit-writer |

**Total**: 19 agents

## Commands

| Category | Count |
|----------|-------|
| orchestration | 3 |
| data-engineering | 3 |
| devops | 3 |
| documentation | 3 |
| research | 1 |
| ai-engineering | 5 |
| plugin-development | 8 |

**Total**: 26 commands

## Skills

| Skill | Patterns |
|-------|----------|
| research-patterns | Research protocols, uncertainty handling |
| data-pipeline-patterns | ETL/ELT, batch/streaming |
| sql-optimization | Query optimization, indexing |
| cloud-architecture | Data lake, serverless |
| testing-strategies | Unit testing, data quality |
| documentation-templates | Pipeline docs, ADRs |
| code-review-standards | Python, SQL checklists |
| ai-engineering-patterns | RAG, agents, LLM |
| plugin-development-patterns | Agent/skill/command templates |

**Total**: 9 skills

## Health

| Check | Status |
|-------|--------|
| plugin.json | ✅ Valid |
| README.md | ✅ Up to date |
| CLAUDE.md | ✅ Present |
| All agents valid | ✅ 19/19 |
| All commands valid | ✅ 26/26 |
| All skills valid | ✅ 9/9 |

## Domains

| Domain | Orchestrator | Specialists | Commands | Skills |
|--------|--------------|-------------|----------|--------|
| Data Engineering | planner-orchestrator | 10 | 9 | 6 |
| AI Engineering | ai-orchestrator | 4 | 5 | 1 |
| Plugin Development | plugin-architect | 1 | 8 | 1 |
```

## Example Output

```markdown
# Plugin Status

## Overview
- **Name**: my-claude-squad
- **Version**: 1.0.0
- **Total Components**: 54

## Agents

| Model | Count | Agents |
|-------|-------|--------|
| opus | 3 | planner-orchestrator, ai-orchestrator, plugin-architect |
| sonnet | 15 | python-developer, sql-specialist, snowflake-specialist, spark-specialist, airflow-specialist, aws-specialist, sql-server-specialist, container-specialist, kubernetes-specialist, documenter, rag-specialist, agent-framework-specialist, llm-specialist, automation-specialist, plugin-developer |
| haiku | 1 | git-commit-writer |

**Total**: 19 agents

## Commands

| Category | Count |
|----------|-------|
| orchestration | 3 |
| data-engineering | 3 |
| devops | 3 |
| documentation | 3 |
| research | 1 |
| ai-engineering | 5 |
| plugin-development | 8 |

**Total**: 26 commands

## Skills

**Total**: 9 skills

## Health

| Check | Status |
|-------|--------|
| plugin.json | ✅ Valid |
| README.md | ✅ Up to date |
| CLAUDE.md | ✅ Present |
| All agents valid | ✅ 19/19 |
| All commands valid | ✅ 26/26 |
| All skills valid | ✅ 9/9 |

**Overall Status**: ✅ Healthy
```

## See Also

- `/list-agents` - Detailed agent list
- `/list-commands` - Detailed command list
- `/validate-plugin` - Full validation report
