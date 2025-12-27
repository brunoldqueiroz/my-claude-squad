"""Sample test data constants."""

# Sample task descriptions for routing tests
ROUTING_TASKS = {
    "snowflake": "Build a Snowflake data warehouse",
    "sql_server": "Optimize SQL Server queries",
    "python": "Write a Python ETL script",
    "spark": "Create a Spark data pipeline",
    "airflow": "Set up an Airflow DAG",
    "aws": "Configure AWS S3 buckets",
    "docker": "Build a Docker container",
    "kubernetes": "Deploy to Kubernetes",
    "rag": "Build a RAG chatbot",
    "langchain": "Create a LangChain agent",
    "plugin": "Develop a plugin for Claude Code",
}

# Sample decomposable tasks
DECOMPOSABLE_TASKS = [
    "Build a data pipeline and deploy to production",
    "Create a Python script, then test it, and document it",
    "Set up AWS infrastructure and configure monitoring",
]

# Sample agent markdown content
VALID_AGENT_MD = """---
name: sample-agent
description: |
  A sample agent for testing.
  <example>
  user: "sample query"
  </example>
model: sonnet
color: white
---

Sample agent content.
"""

INVALID_AGENT_MD = """---
description: No name field
---

Invalid content.
"""

NO_FRONTMATTER_MD = """
Just plain content without frontmatter.
"""
