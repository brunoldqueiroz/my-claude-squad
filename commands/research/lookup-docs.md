---
description: Look up documentation for any library, framework, or tool using Context7 and Exa
argument-hint: <library or topic>
---

# Lookup Docs

Quickly retrieve up-to-date documentation for any library, framework, or tool.

## Usage

```
/lookup-docs <library or topic>
```

## Examples

```
/lookup-docs pandas merge
/lookup-docs fastapi dependency injection
/lookup-docs snowflake streams
/lookup-docs kubernetes ingress
/lookup-docs airflow taskflow api
```

## Process

### Step 1: Identify the Library

Determine the library or tool being researched:

```
mcp__upstash-context7-mcp__resolve-library-id
Input: { "libraryName": "<library name>" }
```

### Step 2: Fetch Documentation

Get specific documentation on the topic:

```
mcp__upstash-context7-mcp__get-library-docs
Input: {
  "context7CompatibleLibraryID": "<resolved ID>",
  "topic": "<specific topic>",
  "tokens": 8000
}
```

### Step 3: Get Code Examples (Optional)

If more examples are needed:

```
mcp__exa__get_code_context_exa
Input: {
  "query": "<library> <topic> example code",
  "tokensNum": 5000
}
```

### Step 4: Web Search (Fallback)

For topics not in Context7:

```
WebSearch
Input: { "query": "<library> <topic> documentation 2025" }
```

## Output Format

```markdown
# Documentation: [Library] - [Topic]

## Overview
[Brief summary of the topic]

## Current API/Syntax
[Code examples from documentation]

## Best Practices
[Recommendations from docs]

## Common Patterns
[Usage patterns and examples]

## Version Notes
[Any version-specific information]

## Sources
- [Source 1](url)
- [Source 2](url)
```

## Supported Library Types

| Category | Examples |
|----------|----------|
| Python | pandas, pydantic, fastapi, sqlalchemy, polars |
| Data | spark, airflow, dbt, great_expectations |
| Cloud | boto3, snowflake-connector, azure-sdk |
| Databases | postgresql, mysql, mongodb |
| DevOps | kubernetes, docker, terraform, helm |
| Web | react, next.js, vue, express |

## Tips

1. **Be Specific**: Include the specific topic, not just the library name
   - Good: `/lookup-docs pandas groupby aggregate`
   - Less good: `/lookup-docs pandas`

2. **Check Version**: Documentation includes version info when available

3. **Multiple Sources**: Uses Context7 + Exa for comprehensive coverage

4. **Code Examples**: Request includes practical code examples

5. **Current Info**: Always gets latest documentation, not cached training data
