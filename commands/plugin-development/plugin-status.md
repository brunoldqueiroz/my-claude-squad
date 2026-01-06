---
name: plugin-status
description: Show plugin statistics and health
agent: plugin-developer
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
| opus | 1 | squad-orchestrator |
| sonnet | 15 | python-developer, sql-specialist, ... |
| haiku | 1 | git-commit-writer |

**Total**: 17 agents

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
| All agents valid | ✅ 17/17 |
| All commands valid | ✅ 30/30 |
| All skills valid | ✅ 10/10 |

## Domains

| Domain | Orchestrator | Specialists | Commands | Skills |
|--------|--------------|-------------|----------|--------|
| Data Engineering | squad-orchestrator | 11 | 9 | 6 |
| AI Engineering | squad-orchestrator | 4 | 5 | 1 |
| Plugin Development | squad-orchestrator | 1 | 12 | 2 |
| Self-Improvement | squad-orchestrator | - | 4 | 1 |
```

## Example Output

```markdown
# Plugin Status

## Overview
- **Name**: my-claude-squad
- **Version**: 1.0.0
- **Total Components**: 57

## Agents

| Model | Count | Agents |
|-------|-------|--------|
| opus | 1 | squad-orchestrator |
| sonnet | 15 | python-developer, sql-specialist, snowflake-specialist, spark-specialist, airflow-specialist, aws-specialist, sql-server-specialist, container-specialist, kubernetes-specialist, documenter, rag-specialist, agent-framework-specialist, llm-specialist, automation-specialist, plugin-developer |
| haiku | 1 | git-commit-writer |

**Total**: 17 agents

## Commands

| Category | Count |
|----------|-------|
| orchestration | 3 |
| data-engineering | 3 |
| devops | 3 |
| documentation | 3 |
| research | 1 |
| ai-engineering | 5 |
| plugin-development | 12 |

**Total**: 30 commands

## Skills

**Total**: 10 skills

## Health

| Check | Status |
|-------|--------|
| plugin.json | ✅ Valid |
| README.md | ✅ Up to date |
| CLAUDE.md | ✅ Present |
| All agents valid | ✅ 17/17 |
| All commands valid | ✅ 30/30 |
| All skills valid | ✅ 10/10 |

**Overall Status**: ✅ Healthy
```

## See Also

- `/list-agents` - Detailed agent list
- `/list-commands` - Detailed command list
- `/validate-plugin` - Full validation report
