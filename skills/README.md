# Skills Directory

Skills are reusable knowledge patterns that agents reference during task execution.

## Progressive Disclosure Structure

Each skill follows a layered structure for efficient context loading:

```
skills/
└── skill-name/
    ├── SKILL.md          # Quick reference (always loaded)
    ├── references/       # Detailed documentation (loaded on demand)
    │   ├── topic-1.md
    │   └── topic-2.md
    └── examples/         # Code examples (loaded on demand)
        ├── example-1.py
        └── example-2.sql
```

### Layer 1: SKILL.md (Quick Reference)
- Overview and key concepts
- Comparison tables
- Decision frameworks
- Anti-patterns summary
- Research tools

**When loaded**: Always available to agents for quick decisions.

### Layer 2: references/ (Detailed Docs)
- Deep-dive into specific topics
- Implementation patterns
- Configuration guides
- Troubleshooting guides

**When loaded**: On demand when agent needs detailed information.

### Layer 3: examples/ (Code Examples)
- Complete, runnable code
- Multiple language/framework variants
- Test cases
- Configuration files

**When loaded**: On demand when agent needs to write similar code.

## Available Skills

| Skill | Domain | Topics |
|-------|--------|--------|
| [data-pipeline-patterns](data-pipeline-patterns/) | Data Engineering | ETL/ELT, batch/streaming, idempotency |
| [sql-optimization](sql-optimization/) | Data Engineering | Execution plans, indexing, query tuning |
| [cloud-architecture](cloud-architecture/) | DevOps | Data lakes, lakehouses, cost optimization |
| [testing-strategies](testing-strategies/) | Quality | Unit tests, integration tests, data quality |
| [documentation-templates](documentation-templates/) | Documentation | READMEs, ADRs, data dictionaries, runbooks |
| [code-review-standards](code-review-standards/) | Quality | Python, SQL, infra, security checklists |
| [research-patterns](research-patterns/) | All | Research-first protocols, uncertainty handling |
| [ai-engineering-patterns](ai-engineering-patterns/) | AI Engineering | RAG, agents, LLM patterns |
| [plugin-development-patterns](plugin-development-patterns/) | Plugin | Agent, skill, command creation |
| [self-improvement-patterns](self-improvement-patterns/) | Plugin | Audit, analysis, improvement |

## Usage by Agents

Agents reference skills in their prompts:

```markdown
## MEMORY INTEGRATION

### Before Implementation
1. **Plugin Patterns First**
   Read: skills/plugin-development-patterns/SKILL.md

2. **Detailed Reference** (if needed)
   Read: skills/plugin-development-patterns/references/agent-creation.md

3. **Code Examples** (if needed)
   Read: skills/plugin-development-patterns/examples/agent-template.md
```

## Creating New Skills

Use the `/new-skill` command or reference `skills/plugin-development-patterns/SKILL.md`.
