"""Tests for ergonomics tools - aliases, intents, shortcuts."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from orchestrator.aliases import (
    AliasResolver,
    Alias,
    ALIASES,
    TOOL_TO_ALIAS,
    get_alias_resolver,
)
from orchestrator.intents import (
    IntentDetector,
    IntentCategory,
    Intent,
    INTENT_PATTERNS,
    ACTION_TO_TOOL,
    get_intent_detector,
)
from orchestrator.shortcuts import (
    ShortcutExecutor,
    Shortcut,
    ShortcutStep,
    SHORTCUTS,
    PROJECT_PATTERNS,
    PROJECT_AGENTS,
    list_shortcuts,
    get_shortcut_categories,
    get_shortcut_executor,
)


# === Alias Tests ===


class TestAliasRegistry:
    """Tests for the alias registry."""

    def test_aliases_defined(self):
        """All expected alias categories exist."""
        categories = set(a.category for a in ALIASES.values())
        expected = {"status", "agents", "memory", "workflow", "swarm", "session", "commands", "system"}
        assert expected.issubset(categories)

    def test_alias_structure(self):
        """Each alias has required fields."""
        for name, alias in ALIASES.items():
            assert alias.name == name
            assert alias.tool
            assert alias.description
            assert alias.category

    def test_reverse_mapping(self):
        """Tool to alias reverse mapping works."""
        assert "swarm_status" in TOOL_TO_ALIAS
        assert TOOL_TO_ALIAS["swarm_status"] == "status"

    def test_common_aliases_exist(self):
        """Common short aliases are defined."""
        expected_aliases = [
            "status", "health", "agents", "spawn", "route",
            "remember", "recall", "search", "plan", "done",
            "swarm", "session", "pause", "resume",
            "commit", "docs", "sql", "k8s",
        ]
        for alias in expected_aliases:
            assert alias in ALIASES, f"Missing alias: {alias}"


class TestAliasResolver:
    """Tests for the AliasResolver class."""

    def test_resolve_existing_alias(self):
        """Resolver finds existing aliases."""
        resolver = AliasResolver()
        alias = resolver.resolve("status")
        assert alias is not None
        assert alias.tool == "swarm_status"

    def test_resolve_case_insensitive(self):
        """Resolver handles case-insensitively."""
        resolver = AliasResolver()
        alias = resolver.resolve("STATUS")
        assert alias is not None
        assert alias.name == "status"

    def test_resolve_unknown_alias(self):
        """Resolver returns None for unknown aliases."""
        resolver = AliasResolver()
        alias = resolver.resolve("nonexistent")
        assert alias is None

    def test_list_aliases_all(self):
        """List all aliases without filter."""
        resolver = AliasResolver()
        aliases = resolver.list_aliases()
        assert len(aliases) == len(ALIASES)

    def test_list_aliases_by_category(self):
        """List aliases filtered by category."""
        resolver = AliasResolver()
        status_aliases = resolver.list_aliases(category="status")
        assert len(status_aliases) > 0
        assert all(a["category"] == "status" for a in status_aliases)

    def test_get_categories(self):
        """Get all unique categories."""
        resolver = AliasResolver()
        categories = resolver.get_categories()
        assert isinstance(categories, list)
        assert "status" in categories
        assert "memory" in categories

    def test_suggest_matching(self):
        """Suggest aliases matching partial input."""
        resolver = AliasResolver()
        suggestions = resolver.suggest("sta")
        assert "status" in suggestions
        assert "storage" in suggestions

    def test_suggest_from_description(self):
        """Suggest aliases from description match."""
        resolver = AliasResolver()
        suggestions = resolver.suggest("swarm")
        assert len(suggestions) > 0

    def test_singleton(self):
        """Singleton pattern works."""
        r1 = get_alias_resolver()
        r2 = get_alias_resolver()
        assert r1 is r2


# === Intent Tests ===


class TestIntentPatterns:
    """Tests for intent pattern definitions."""

    def test_patterns_defined(self):
        """Intent patterns are defined."""
        assert len(INTENT_PATTERNS) > 0

    def test_action_mapping_complete(self):
        """All actions have tool mappings."""
        actions = set(p[3] for p in INTENT_PATTERNS)  # action is at index 3
        for action in actions:
            assert action in ACTION_TO_TOOL, f"Missing tool mapping for action: {action}"


class TestIntentDetector:
    """Tests for the IntentDetector class."""

    def test_detect_sql_help(self):
        """Detect SQL help intent."""
        detector = IntentDetector()
        intent = detector.detect("help me with SQL")
        assert intent is not None
        assert intent.agent == "sql-specialist"
        assert intent.category == IntentCategory.CREATE

    def test_detect_code_review(self):
        """Detect code review intent."""
        detector = IntentDetector()
        intent = detector.detect("review this code")
        assert intent is not None
        assert intent.category == IntentCategory.REVIEW

    def test_detect_debugging(self):
        """Detect debugging intent."""
        detector = IntentDetector()
        intent = detector.detect("fix this bug in the auth module")
        assert intent is not None
        assert intent.category == IntentCategory.FIX

    def test_detect_optimization(self):
        """Detect optimization intent."""
        detector = IntentDetector()
        intent = detector.detect("optimize this query")
        assert intent is not None
        assert intent.category == IntentCategory.OPTIMIZE
        assert intent.agent == "sql-specialist"

    def test_detect_docker(self):
        """Detect Docker/container intent."""
        detector = IntentDetector()
        intent = detector.detect("create a docker container")
        assert intent is not None
        assert intent.category == IntentCategory.DEPLOY
        assert intent.agent == "container-specialist"

    def test_detect_pipeline_creation(self):
        """Detect pipeline creation intent."""
        detector = IntentDetector()
        intent = detector.detect("create a data pipeline")
        assert intent is not None
        assert intent.category == IntentCategory.CREATE
        assert "pipeline" in intent.action

    def test_detect_no_match(self):
        """No match for random text."""
        detector = IntentDetector()
        intent = detector.detect("random gibberish xyz123")
        # May or may not match depending on patterns
        # Low confidence should be returned or None
        if intent:
            assert intent.confidence < 0.9

    def test_detect_all_intents(self):
        """Detect multiple intents."""
        detector = IntentDetector()
        intents = detector.detect_all("review and optimize this code")
        assert len(intents) >= 1
        # Should find both review and optimize intents

    def test_detect_all_with_threshold(self):
        """Threshold filters low-confidence intents."""
        detector = IntentDetector()
        high_threshold = detector.detect_all("maybe do something", threshold=0.9)
        low_threshold = detector.detect_all("maybe do something", threshold=0.1)
        assert len(high_threshold) <= len(low_threshold)

    def test_get_suggested_tool(self):
        """Get tool suggestion for intent."""
        detector = IntentDetector()
        intent = detector.detect("optimize this query")
        assert intent is not None
        tool = detector.get_suggested_tool(intent)
        assert tool is not None

    def test_explain_intent(self):
        """Generate explanation for intent."""
        detector = IntentDetector()
        intent = detector.detect("fix this bug")
        assert intent is not None
        explanation = detector.explain_intent(intent)
        assert "fix" in explanation.lower() or "debug" in explanation.lower()
        assert intent.agent in explanation

    def test_context_extraction_files(self):
        """Extract file paths from context."""
        detector = IntentDetector()
        intent = detector.detect("fix the bug in src/main.py")
        assert intent is not None
        # Context should contain file info
        assert "matched_text" in intent.context

    def test_singleton(self):
        """Singleton pattern works."""
        d1 = get_intent_detector()
        d2 = get_intent_detector()
        assert d1 is d2


# === Shortcut Tests ===


class TestShortcutRegistry:
    """Tests for shortcut definitions."""

    def test_shortcuts_defined(self):
        """Shortcuts are defined."""
        assert len(SHORTCUTS) > 0

    def test_shortcut_structure(self):
        """Each shortcut has required fields."""
        for name, shortcut in SHORTCUTS.items():
            assert shortcut.name == name
            assert shortcut.description
            assert shortcut.category
            assert len(shortcut.steps) > 0

    def test_expected_shortcuts_exist(self):
        """Common shortcuts are defined."""
        expected = ["etl-pipeline", "deploy-service", "start-rag"]
        for name in expected:
            assert name in SHORTCUTS, f"Missing shortcut: {name}"


class TestListShortcuts:
    """Tests for listing shortcuts."""

    def test_list_all(self):
        """List all shortcuts."""
        shortcuts = list_shortcuts()
        assert len(shortcuts) == len(SHORTCUTS)

    def test_list_by_category(self):
        """List shortcuts by category."""
        shortcuts = list_shortcuts(category="data")
        assert len(shortcuts) > 0
        assert all(s["category"] == "data" for s in shortcuts)

    def test_get_categories(self):
        """Get all shortcut categories."""
        categories = get_shortcut_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0


class TestProjectDetection:
    """Tests for project type detection."""

    def test_patterns_defined(self):
        """Project patterns are defined."""
        assert "python" in PROJECT_PATTERNS
        assert "node" in PROJECT_PATTERNS
        assert "dbt" in PROJECT_PATTERNS

    def test_agents_defined(self):
        """Project agents are defined."""
        assert "python" in PROJECT_AGENTS
        assert "airflow" in PROJECT_AGENTS

    def test_detect_current_project(self):
        """Detect current project type (should be Python)."""
        executor = ShortcutExecutor()
        # Run from project root which has pyproject.toml
        result = executor.detect_project_type()
        assert "python" in result["detected_types"]
        assert "python-developer" in result["recommended_agents"]

    def test_detect_with_path(self, tmp_path):
        """Detect project with custom path."""
        # Create a fake node project
        (tmp_path / "package.json").write_text("{}")

        executor = ShortcutExecutor()
        result = executor.detect_project_type(tmp_path)
        assert "node" in result["detected_types"]

    def test_detect_empty_directory(self, tmp_path):
        """Detect in empty directory."""
        executor = ShortcutExecutor()
        result = executor.detect_project_type(tmp_path)
        assert result["detected_types"] == []
        assert result["primary_type"] == "unknown"


class TestShortcutExecutor:
    """Tests for the ShortcutExecutor class."""

    def test_register_tool(self):
        """Register a tool function."""
        executor = ShortcutExecutor()
        mock_func = MagicMock(return_value={"result": "ok"})
        executor.register_tool("test_tool", mock_func)
        assert "test_tool" in executor._tool_registry

    def test_register_tools_bulk(self):
        """Register multiple tools at once."""
        executor = ShortcutExecutor()
        tools = {
            "tool1": MagicMock(),
            "tool2": MagicMock(),
        }
        executor.register_tools(tools)
        assert "tool1" in executor._tool_registry
        assert "tool2" in executor._tool_registry

    def test_singleton(self):
        """Singleton pattern works."""
        e1 = get_shortcut_executor()
        e2 = get_shortcut_executor()
        assert e1 is e2


# === Integration Tests ===


class TestErgonomicsIntegration:
    """Integration tests for ergonomics tools."""

    def test_alias_to_intent_flow(self):
        """Alias resolution falls back to intent detection."""
        resolver = AliasResolver()
        detector = IntentDetector()

        # First try alias
        alias = resolver.resolve("help me with SQL")
        assert alias is None  # Not an exact alias match

        # Fall back to intent
        intent = detector.detect("help me with SQL")
        assert intent is not None
        assert intent.agent == "sql-specialist"

    def test_shortcut_with_steps(self):
        """Shortcut steps are well-formed."""
        shortcut = SHORTCUTS["etl-pipeline"]
        assert len(shortcut.steps) >= 2
        assert shortcut.steps[0].tool == "create_pipeline"
        assert shortcut.required_args == ["source", "target", "name"]

    def test_end_to_end_command_parsing(self):
        """Parse various command formats."""
        resolver = AliasResolver()
        detector = IntentDetector()

        test_cases = [
            ("status", "alias"),  # Direct alias
            ("help me with SQL queries", "intent"),  # Natural language
            ("spawn python-developer", "alias"),  # Alias with args
            ("review this pull request", "intent"),  # Intent
        ]

        for command, expected_type in test_cases:
            first_word = command.split()[0].lower()
            alias = resolver.resolve(first_word)

            if alias:
                assert expected_type == "alias", f"Expected {expected_type} for '{command}'"
            else:
                intent = detector.detect(command)
                if intent and intent.confidence >= 0.6:
                    assert expected_type == "intent", f"Expected {expected_type} for '{command}'"
