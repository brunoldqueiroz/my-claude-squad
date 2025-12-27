"""Tests for orchestrator/agent_registry.py - AgentRegistry."""

from pathlib import Path

import pytest

from orchestrator.agent_registry import AgentRegistry
from orchestrator.types import AgentModel


class TestAgentRegistryParsing:
    """Tests for frontmatter parsing."""

    def test_parse_valid_frontmatter(self, temp_agents_dir):
        """Parses valid YAML frontmatter correctly."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("test-agent-1")

        assert agent is not None
        assert agent.name == "test-agent-1"
        assert "Python development" in agent.description

    def test_parse_missing_frontmatter(self, temp_agents_dir):
        """Files without frontmatter are skipped."""
        # Create file without frontmatter
        no_fm = temp_agents_dir / "no-frontmatter.md"
        no_fm.write_text("Just some content without frontmatter")

        registry = AgentRegistry(agents_dir=temp_agents_dir)

        assert registry.get_agent("no-frontmatter") is None

    def test_parse_missing_name_skipped(self, temp_agents_dir):
        """Files with frontmatter but no name are skipped."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        # invalid-agent.md exists but has no name
        assert registry.get_agent("invalid-agent") is None


class TestAgentRegistryModelParsing:
    """Tests for model field parsing."""

    def test_parse_sonnet_model(self, temp_agents_dir):
        """Parses sonnet model correctly."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("test-agent-1")
        assert agent.model == AgentModel.SONNET

    def test_parse_opus_model(self, temp_agents_dir):
        """Parses opus model correctly."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("test-agent-2")
        assert agent.model == AgentModel.OPUS

    def test_invalid_model_defaults_to_sonnet(self, temp_agents_dir):
        """Invalid model value defaults to sonnet."""
        bad_model = temp_agents_dir / "bad-model.md"
        bad_model.write_text("""---
name: bad-model
model: invalid-model
---
Content
""")
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("bad-model")
        assert agent is not None
        assert agent.model == AgentModel.SONNET


class TestAgentRegistryTriggers:
    """Tests for trigger extraction."""

    def test_extracts_triggers_from_examples(self, temp_agents_dir):
        """Extracts quoted strings from <example> tags."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("test-agent-1")
        assert "write a python script" in agent.triggers

    def test_extracts_tech_keywords(self, temp_agents_dir):
        """Extracts technology keywords from description."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("test-agent-1")
        assert "python" in agent.triggers


class TestAgentRegistryListing:
    """Tests for agent listing."""

    def test_list_agents_returns_all(self, temp_agents_dir):
        """list_agents returns all valid agents."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agents = registry.list_agents()

        names = [a.name for a in agents]
        assert "test-agent-1" in names
        assert "test-agent-2" in names
        # Invalid agent should not be in list
        assert "invalid-agent" not in names

    def test_list_agents_empty_dir(self, tmp_path):
        """list_agents returns empty list for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        registry = AgentRegistry(agents_dir=empty_dir)

        assert len(registry.list_agents()) == 0


class TestAgentRegistryLookup:
    """Tests for agent lookup."""

    def test_get_agent_exists(self, temp_agents_dir):
        """get_agent returns agent when exists."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("test-agent-1")

        assert agent is not None
        assert agent.name == "test-agent-1"

    def test_get_agent_not_exists(self, temp_agents_dir):
        """get_agent returns None for missing agent."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("nonexistent")

        assert agent is None


class TestAgentRegistrySearch:
    """Tests for agent search."""

    def test_find_by_trigger_keyword(self, temp_agents_dir):
        """find_agents_by_trigger matches triggers."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agents = registry.find_agents_by_trigger("python")

        names = [a.name for a in agents]
        assert "test-agent-1" in names

    def test_find_by_description(self, temp_agents_dir):
        """find_agents_by_trigger searches description."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agents = registry.find_agents_by_trigger("development")

        names = [a.name for a in agents]
        assert "test-agent-1" in names

    def test_find_by_name(self, temp_agents_dir):
        """find_agents_by_trigger matches agent name."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agents = registry.find_agents_by_trigger("agent-1")

        names = [a.name for a in agents]
        assert "test-agent-1" in names

    def test_find_case_insensitive(self, temp_agents_dir):
        """Search is case insensitive."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agents = registry.find_agents_by_trigger("PYTHON")

        names = [a.name for a in agents]
        assert "test-agent-1" in names

    def test_find_no_matches(self, temp_agents_dir):
        """Returns empty list when no matches."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agents = registry.find_agents_by_trigger("xyznonexistent")

        assert len(agents) == 0


class TestAgentRegistryReload:
    """Tests for registry reload."""

    def test_reload_picks_up_new_agents(self, temp_agents_dir):
        """reload() discovers newly added agents."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        # Initially just test agents
        initial_count = len(registry.list_agents())

        # Add new agent file
        new_agent = temp_agents_dir / "new-agent.md"
        new_agent.write_text("""---
name: new-agent
description: A brand new agent
---
New agent content
""")

        registry.reload()

        assert len(registry.list_agents()) == initial_count + 1
        assert registry.get_agent("new-agent") is not None

    def test_reload_removes_deleted_agents(self, temp_agents_dir):
        """reload() removes agents whose files were deleted."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        # Verify agent exists
        assert registry.get_agent("test-agent-1") is not None

        # Delete the agent file
        (temp_agents_dir / "test-agent-1.md").unlink()

        registry.reload()

        assert registry.get_agent("test-agent-1") is None


class TestAgentRegistryFilePath:
    """Tests for file path tracking."""

    def test_agent_has_file_path(self, temp_agents_dir):
        """Agent includes its source file path."""
        registry = AgentRegistry(agents_dir=temp_agents_dir)

        agent = registry.get_agent("test-agent-1")

        assert agent.file_path is not None
        assert "test-agent-1.md" in agent.file_path


class TestAgentRegistryNonexistentDir:
    """Tests for handling missing directory."""

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        """Registry handles nonexistent directory gracefully."""
        nonexistent = tmp_path / "does_not_exist"

        registry = AgentRegistry(agents_dir=nonexistent)

        assert len(registry.list_agents()) == 0
