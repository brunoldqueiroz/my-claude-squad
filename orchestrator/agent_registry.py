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

    def _extract_triggers(self, description: str) -> list[str]:
        """Extract trigger keywords from agent description.

        Args:
            description: Agent description text

        Returns:
            List of trigger keywords
        """
        triggers = []

        # Look for <example> tags in description
        example_pattern = r"<example>(.*?)</example>"
        examples = re.findall(example_pattern, description, re.DOTALL | re.IGNORECASE)

        for example in examples:
            # Extract quoted strings as potential triggers
            quoted = re.findall(r'"([^"]+)"', example)
            triggers.extend(quoted)

        # Also extract key technology words
        tech_words = [
            "python",
            "sql",
            "snowflake",
            "spark",
            "airflow",
            "aws",
            "docker",
            "kubernetes",
            "rag",
            "llm",
            "langchain",
            "langgraph",
            "mcp",
            "n8n",
            "dify",
            "ollama",
        ]

        desc_lower = description.lower()
        for word in tech_words:
            if word in desc_lower:
                triggers.append(word)

        return list(set(triggers))

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

                # Build agent
                agent = Agent(
                    name=frontmatter["name"],
                    description=frontmatter.get("description", ""),
                    model=model,
                    color=frontmatter.get("color", "white"),
                    triggers=self._extract_triggers(frontmatter.get("description", "")),
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
