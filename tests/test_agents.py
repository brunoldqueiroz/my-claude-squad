"""Tests for agent prompt templates.

Validates:
- Frontmatter schema (required fields, valid values)
- Agent naming conventions
- Tool configurations
- Trigger definitions
- Cross-agent consistency
"""

import re
from pathlib import Path

import pytest
import yaml

# Schema definitions
REQUIRED_FIELDS = ["name", "description", "model", "color"]
VALID_MODELS = ["sonnet", "opus", "haiku"]
VALID_COLORS = [
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    "gray", "grey", "orange", "purple", "pink", "brown", "teal"
]
VALID_PERMISSION_MODES = ["default", "acceptEdits", "bypassPermissions", "plan", "dontAsk"]

# Core tools that should be available
CORE_TOOLS = ["Read", "Edit", "Write", "Bash", "Grep", "Glob"]

# MCP tools pattern
MCP_TOOL_PATTERN = re.compile(r"^mcp__[\w-]+$")


def parse_agent_frontmatter(agent_path: Path) -> tuple[dict, str]:
    """Parse agent markdown file and extract frontmatter + content."""
    content = agent_path.read_text()

    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        raise ValueError(f"No valid frontmatter found in {agent_path.name}")

    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2).strip()

    return frontmatter, body


def parse_tools_field(tools_value: str) -> list[str]:
    """Parse comma-separated tools field into list."""
    if not tools_value:
        return []
    return [t.strip() for t in tools_value.split(",")]


class TestAgentFrontmatter:
    """Test agent frontmatter schema validation."""

    def test_agents_directory_exists(self, agents_dir: Path):
        """Verify agents directory exists."""
        assert agents_dir.exists(), "agents/ directory not found"
        assert agents_dir.is_dir(), "agents/ is not a directory"

    def test_agents_exist(self, agent_files: list[Path]):
        """Verify at least one agent exists."""
        assert len(agent_files) > 0, "No agent files found"

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_valid_frontmatter(self, agent_file: Path):
        """Each agent must have valid YAML frontmatter."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        assert isinstance(frontmatter, dict), f"{agent_file.name}: frontmatter is not a dict"

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_required_fields(self, agent_file: Path):
        """Each agent must have all required fields."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)

        for field in REQUIRED_FIELDS:
            assert field in frontmatter, f"{agent_file.name}: missing required field '{field}'"

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_name_matches_filename(self, agent_file: Path):
        """Agent name field must match filename (without .md)."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        expected_name = agent_file.stem
        actual_name = frontmatter.get("name", "")

        assert actual_name == expected_name, (
            f"{agent_file.name}: name '{actual_name}' doesn't match filename '{expected_name}'"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_valid_model(self, agent_file: Path):
        """Agent model must be one of: sonnet, opus, haiku."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        model = frontmatter.get("model", "")

        assert model in VALID_MODELS, (
            f"{agent_file.name}: invalid model '{model}', must be one of {VALID_MODELS}"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_valid_color(self, agent_file: Path):
        """Agent color must be a valid terminal color."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        color = frontmatter.get("color", "").lower()

        assert color in VALID_COLORS, (
            f"{agent_file.name}: invalid color '{color}', must be one of {VALID_COLORS}"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_description(self, agent_file: Path):
        """Agent description must be non-empty."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        description = frontmatter.get("description", "")

        assert description and len(description.strip()) > 10, (
            f"{agent_file.name}: description is too short or empty"
        )


class TestAgentTools:
    """Test agent tool configurations."""

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_tools_field(self, agent_file: Path):
        """Each agent should have a tools field."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)

        assert "tools" in frontmatter, (
            f"{agent_file.name}: missing 'tools' field - agents need explicit tool access"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_permission_mode(self, agent_file: Path):
        """Each agent should have a permissionMode field."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)

        assert "permissionMode" in frontmatter, (
            f"{agent_file.name}: missing 'permissionMode' field"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_valid_permission_mode(self, agent_file: Path):
        """Agent permissionMode must be valid."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        mode = frontmatter.get("permissionMode", "")

        assert mode in VALID_PERMISSION_MODES, (
            f"{agent_file.name}: invalid permissionMode '{mode}', "
            f"must be one of {VALID_PERMISSION_MODES}"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_read_tool(self, agent_file: Path):
        """All agents should have at least Read tool."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        tools = parse_tools_field(frontmatter.get("tools", ""))

        assert "Read" in tools, f"{agent_file.name}: missing 'Read' tool"

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
        if f.stem != "git-commit-writer"  # Exclude read-only agent
    ])
    def test_writing_agent_has_edit_tool(self, agent_file: Path):
        """Agents that write code should have Edit tool."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        tools = parse_tools_field(frontmatter.get("tools", ""))

        assert "Edit" in tools, f"{agent_file.name}: missing 'Edit' tool for writing"

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_mcp_tools_format(self, agent_file: Path):
        """MCP tools should follow mcp__<server> format."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        tools = parse_tools_field(frontmatter.get("tools", ""))

        mcp_tools = [t for t in tools if t.startswith("mcp__")]

        for tool in mcp_tools:
            assert MCP_TOOL_PATTERN.match(tool), (
                f"{agent_file.name}: invalid MCP tool format '{tool}', "
                "should be 'mcp__<server-name>'"
            )


class TestAgentTriggers:
    """Test agent trigger configurations."""

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_triggers(self, agent_file: Path):
        """Each agent should have triggers for invocation."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        triggers = frontmatter.get("triggers", [])

        assert triggers and len(triggers) > 0, (
            f"{agent_file.name}: missing 'triggers' - agents need keywords for invocation"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_triggers_are_lowercase(self, agent_file: Path):
        """Triggers should be lowercase for consistent matching."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        triggers = frontmatter.get("triggers", [])

        for trigger in triggers:
            assert trigger == trigger.lower(), (
                f"{agent_file.name}: trigger '{trigger}' should be lowercase"
            )


class TestAgentContent:
    """Test agent prompt content."""

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_content(self, agent_file: Path):
        """Each agent must have prompt content after frontmatter."""
        _, body = parse_agent_frontmatter(agent_file)

        assert body and len(body) > 100, (
            f"{agent_file.name}: agent body is too short (< 100 chars)"
        )

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_role_definition(self, agent_file: Path):
        """Agent should define its role/persona."""
        _, body = parse_agent_frontmatter(agent_file)

        # Check for common role indicators
        has_role = any([
            "You are" in body,
            "## Role" in body,
            "## Your Role" in body,
            "**Expert**" in body,
            "**Specialist**" in body,
        ])

        assert has_role, f"{agent_file.name}: missing role/persona definition"

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_agent_has_expertise_section(self, agent_file: Path):
        """Agent should document its expertise areas."""
        _, body = parse_agent_frontmatter(agent_file)

        has_expertise = any([
            "## Core Expertise" in body,
            "## Expertise" in body,
            "## Capabilities" in body,
            "## Skills" in body,
        ])

        assert has_expertise, f"{agent_file.name}: missing expertise/capabilities section"


class TestAgentConsistency:
    """Test cross-agent consistency."""

    def test_no_duplicate_agent_names(self, agent_files: list[Path]):
        """Each agent must have a unique name."""
        names = []
        for agent_file in agent_files:
            frontmatter, _ = parse_agent_frontmatter(agent_file)
            names.append(frontmatter.get("name", ""))

        duplicates = [n for n in names if names.count(n) > 1]
        assert not duplicates, f"Duplicate agent names found: {set(duplicates)}"

    def test_no_duplicate_triggers(self, agent_files: list[Path]):
        """Warn about overlapping triggers between agents."""
        all_triggers: dict[str, list[str]] = {}

        for agent_file in agent_files:
            frontmatter, _ = parse_agent_frontmatter(agent_file)
            agent_name = frontmatter.get("name", agent_file.stem)
            triggers = frontmatter.get("triggers", [])

            for trigger in triggers:
                if trigger not in all_triggers:
                    all_triggers[trigger] = []
                all_triggers[trigger].append(agent_name)

        # Find triggers used by multiple agents
        overlapping = {k: v for k, v in all_triggers.items() if len(v) > 1}

        # This is a warning, not a hard failure (some overlap may be intentional)
        if overlapping:
            import warnings
            warnings.warn(
                f"Overlapping triggers found: {overlapping}",
                UserWarning
            )

    def test_all_agents_have_consistent_structure(self, agent_files: list[Path]):
        """All agents should follow the same structural pattern."""
        for agent_file in agent_files:
            frontmatter, _ = parse_agent_frontmatter(agent_file)

            # Check all have the same base fields
            assert "name" in frontmatter
            assert "description" in frontmatter
            assert "model" in frontmatter
            assert "color" in frontmatter
            assert "tools" in frontmatter
            assert "permissionMode" in frontmatter


class TestAgentExamples:
    """Test agent example documentation."""

    @pytest.mark.parametrize("agent_file", [
        pytest.param(f, id=f.stem)
        for f in sorted(Path(__file__).parent.parent.glob("agents/*.md"))
    ])
    def test_description_has_examples(self, agent_file: Path):
        """Agent descriptions should include usage examples."""
        frontmatter, _ = parse_agent_frontmatter(agent_file)
        description = frontmatter.get("description", "")

        has_examples = "<example>" in description and "</example>" in description

        assert has_examples, (
            f"{agent_file.name}: description should include <example> tags for usage examples"
        )
