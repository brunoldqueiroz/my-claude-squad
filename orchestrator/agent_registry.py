"""Agent registry - reads and manages agent definitions from agents/*.md files."""

import re
from pathlib import Path

import yaml

from .types import Agent, AgentModel


class AgentRegistry:
    """Registry of all available agents parsed from markdown files."""

    def __init__(self, agents_dir: Path | None = None):
        """Initialize the registry.

        Args:
            agents_dir: Path to the agents directory. Defaults to ./agents/
        """
        self.agents_dir = agents_dir or Path(__file__).parent.parent / "agents"
        self._agents: dict[str, Agent] = {}
        self._load_agents()

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Full markdown file content

        Returns:
            Tuple of (frontmatter dict, body content)
        """
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if match:
            frontmatter = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
            return frontmatter, body

        return {}, content

    def _extract_triggers(self, description: str, body: str = "") -> list[str]:
        """Extract trigger keywords from agent description and body.

        Extracts triggers from multiple sources:
        - <example> tags: user quotes and commentary
        - Bold text (**word**): key technologies
        - Headings (## and ###): topic areas
        - Table cells: product/tool names
        - Python imports: library names
        - Known technology patterns

        Args:
            description: Agent description text (from frontmatter)
            body: Agent body content (markdown after frontmatter)

        Returns:
            List of trigger keywords (deduplicated, lowercased)
        """
        triggers = set()
        full_text = f"{description}\n{body}"

        # 1. Extract from <example> tags
        example_pattern = r"<example>(.*?)</example>"
        examples = re.findall(example_pattern, description, re.DOTALL | re.IGNORECASE)

        for example in examples:
            # Extract user quotes (what users might say)
            user_quotes = re.findall(r'user:\s*"([^"]+)"', example, re.IGNORECASE)
            for quote in user_quotes:
                # Extract key phrases from user requests
                triggers.update(self._extract_key_phrases(quote))

            # Extract from <commentary> tags (task type descriptions)
            commentary = re.findall(r"<commentary>(.*?)</commentary>", example, re.IGNORECASE)
            for comment in commentary:
                triggers.update(self._extract_key_phrases(comment))

        # 2. Extract bold text (**word** or **multi word**)
        bold_pattern = r"\*\*([^*]+)\*\*"
        bold_matches = re.findall(bold_pattern, full_text)
        for match in bold_matches:
            # Skip very long phrases (likely sentences, not keywords)
            if len(match.split()) <= 4:
                triggers.add(match.lower().strip())

        # 3. Extract from headings (## and ###)
        heading_pattern = r"^#{2,3}\s+(.+)$"
        headings = re.findall(heading_pattern, full_text, re.MULTILINE)
        for heading in headings:
            # Clean heading and add if it's a meaningful keyword
            cleaned = heading.strip().lower()
            # Skip generic headings
            if cleaned not in {"core expertise", "overview", "usage", "examples", "notes",
                               "research-first protocol", "context resilience", "memory integration"}:
                triggers.add(cleaned)

        # 4. Extract from table first columns (usually tool/product names)
        table_row_pattern = r"^\|\s*\*?\*?([^|*]+)\*?\*?\s*\|"
        table_matches = re.findall(table_row_pattern, full_text, re.MULTILINE)
        for match in table_matches:
            cleaned = match.strip().lower()
            # Skip table headers and empty cells
            if cleaned and cleaned not in {"database", "platform", "model", "feature",
                                            "tool", "framework", "provider", "versions"}:
                triggers.add(cleaned)

        # 5. Extract Python import statements
        import_pattern = r"(?:from|import)\s+(\w+)"
        imports = re.findall(import_pattern, body)
        for imp in imports:
            # Skip standard library and generic imports
            if imp not in {"os", "sys", "re", "json", "typing", "datetime", "pathlib",
                           "dataclasses", "functools", "collections", "itertools", "abc"}:
                triggers.add(imp.lower())

        # 6. Extract technology patterns (compound names)
        tech_patterns = [
            r"\b(py\w+)\b",  # PySpark, PyTorch, etc.
            r"\b(spark\s+\w+)\b",  # Spark SQL, Spark Structured Streaming
            r"\b(delta\s+lake)\b",
            r"\b(apache\s+\w+)\b",  # Apache Kafka, Apache Airflow
            r"\b(\w+db)\b",  # ChromaDB, DuckDB, etc.
            r"\b(\w+sql)\b",  # MySQL, PostgreSQL, T-SQL
            r"\b(aws\s+\w+)\b",  # AWS Lambda, AWS Glue
            r"\b(s3|ec2|ecs|eks|rds|sqs|sns)\b",  # AWS services
            r"\b(gcp|azure)\b",  # Cloud providers
            r"\b(k8s|kubectl|helm)\b",  # Kubernetes
            r"\b(ci/cd|github\s+actions?|gitlab\s+ci)\b",  # CI/CD
        ]

        text_lower = full_text.lower()
        for pattern in tech_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            triggers.update(match.strip() for match in matches)

        # 7. Known technology keywords (catch-all)
        known_tech = {
            "python", "sql", "snowflake", "spark", "pyspark", "airflow", "mwaa",
            "aws", "lambda", "glue", "redshift", "athena", "s3", "sagemaker",
            "docker", "dockerfile", "container", "podman", "buildkit",
            "kubernetes", "k8s", "helm", "kubectl", "argocd", "ingress",
            "rag", "retrieval", "vector", "embedding", "chromadb", "qdrant",
            "pinecone", "weaviate", "pgvector", "milvus",
            "llm", "langchain", "langgraph", "llamaindex", "openai", "anthropic",
            "ollama", "gemini", "mistral", "groq", "litellm",
            "mcp", "n8n", "dify", "zapier", "make", "webhook", "chatbot",
            "fastapi", "flask", "django", "pytest", "poetry", "uv",
            "git", "commit", "branch", "merge", "rebase",
            "documentation", "readme", "changelog", "adr", "docstring",
            "etl", "elt", "pipeline", "streaming", "batch", "cdc",
            "delta", "iceberg", "parquet", "avro", "kafka",
            "crewai", "autogen", "pydantic-ai", "smolagents", "agent",
            "sql server", "mssql", "t-sql", "tsql", "ssis", "ssrs", "ssas",
            "stored procedure", "cte", "window function",
        }

        for word in known_tech:
            if word in text_lower:
                triggers.add(word)

        # Clean up triggers
        cleaned_triggers = set()
        for trigger in triggers:
            # Remove empty or very short triggers
            if len(trigger) >= 2:
                cleaned_triggers.add(trigger.lower().strip())

        return list(cleaned_triggers)

    def _extract_key_phrases(self, text: str) -> set[str]:
        """Extract key phrases from text (user quotes, commentary).

        Args:
            text: Text to extract phrases from

        Returns:
            Set of key phrases
        """
        phrases = set()

        # Extract technology-related words and short phrases
        # Split on common delimiters
        words = re.split(r"[\s,;:]+", text.lower())

        for word in words:
            # Clean punctuation
            cleaned = re.sub(r"[^\w\-]", "", word)
            if len(cleaned) >= 3:
                phrases.add(cleaned)

        # Also extract quoted substrings
        quoted = re.findall(r'"([^"]+)"', text)
        for q in quoted:
            if len(q.split()) <= 4:
                phrases.add(q.lower())

        return phrases

    def _load_agents(self) -> None:
        """Load all agent definitions from the agents directory."""
        if not self.agents_dir.exists():
            return

        for md_file in self.agents_dir.glob("*.md"):
            try:
                content = md_file.read_text()
                frontmatter, body = self._parse_frontmatter(content)

                if not frontmatter.get("name"):
                    continue

                # Parse model
                model_str = frontmatter.get("model", "sonnet").lower()
                model = AgentModel(model_str) if model_str in [m.value for m in AgentModel] else AgentModel.SONNET

                # Get triggers: prefer explicit frontmatter, fall back to auto-extraction
                explicit_triggers = frontmatter.get("triggers", [])
                if explicit_triggers:
                    # Use author-defined triggers (normalize to lowercase)
                    triggers = [t.lower().strip() for t in explicit_triggers if t]
                else:
                    # Fall back to auto-extraction for backwards compatibility
                    triggers = self._extract_triggers(frontmatter.get("description", ""), body)

                # Build agent
                agent = Agent(
                    name=frontmatter["name"],
                    description=frontmatter.get("description", ""),
                    model=model,
                    color=frontmatter.get("color", "white"),
                    triggers=triggers,
                    file_path=str(md_file),
                )

                self._agents[agent.name] = agent

            except Exception as e:
                print(f"Error loading agent from {md_file}: {e}")

    def get_agent(self, name: str) -> Agent | None:
        """Get an agent by name.

        Args:
            name: Agent name

        Returns:
            Agent if found, None otherwise
        """
        return self._agents.get(name)

    def list_agents(self) -> list[Agent]:
        """List all registered agents.

        Returns:
            List of all agents
        """
        return list(self._agents.values())

    def find_agents_by_trigger(self, keyword: str) -> list[Agent]:
        """Find agents that match a trigger keyword.

        Args:
            keyword: Keyword to match

        Returns:
            List of matching agents
        """
        keyword_lower = keyword.lower()
        matches = []

        for agent in self._agents.values():
            # Check triggers
            if any(keyword_lower in trigger.lower() for trigger in agent.triggers):
                matches.append(agent)
                continue

            # Check description
            if keyword_lower in agent.description.lower():
                matches.append(agent)
                continue

            # Check name
            if keyword_lower in agent.name.lower():
                matches.append(agent)

        return matches

    def reload(self) -> None:
        """Reload all agent definitions."""
        self._agents.clear()
        self._load_agents()
