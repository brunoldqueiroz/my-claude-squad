"""Pytest fixtures for my-claude-squad tests."""

import os
from pathlib import Path

import pytest

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / "agents"
SKILLS_DIR = PROJECT_ROOT / "skills"
COMMANDS_DIR = PROJECT_ROOT / "commands"


@pytest.fixture
def project_root() -> Path:
    """Return project root path."""
    return PROJECT_ROOT


@pytest.fixture
def agents_dir() -> Path:
    """Return agents directory path."""
    return AGENTS_DIR


@pytest.fixture
def skills_dir() -> Path:
    """Return skills directory path."""
    return SKILLS_DIR


@pytest.fixture
def commands_dir() -> Path:
    """Return commands directory path."""
    return COMMANDS_DIR


@pytest.fixture
def agent_files(agents_dir: Path) -> list[Path]:
    """Return list of all agent markdown files."""
    return sorted(agents_dir.glob("*.md"))


@pytest.fixture
def skill_files(skills_dir: Path) -> list[Path]:
    """Return list of all skill markdown files."""
    return sorted(skills_dir.glob("*/SKILL.md"))


@pytest.fixture
def command_files(commands_dir: Path) -> list[Path]:
    """Return list of all command markdown files."""
    return sorted(commands_dir.glob("*/*.md"))
