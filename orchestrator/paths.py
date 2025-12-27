"""Path utilities for locating resources.

Resources (agents/, skills/, commands/) are served via MCP and read from the project root.
They are NOT bundled in the wheel - the MCP server reads them directly.

Path resolution order:
1. SQUAD_ROOT environment variable (if set)
2. Project root detection (finds pyproject.toml)
3. Current working directory
"""

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    """Get the project root directory.

    Resolution order:
    1. SQUAD_ROOT environment variable
    2. Walk up from this file to find pyproject.toml
    3. Current working directory

    Returns:
        Path to project root
    """
    # 1. Check environment variable
    env_root = os.environ.get("SQUAD_ROOT")
    if env_root:
        path = Path(env_root)
        if path.exists():
            return path

    # 2. Walk up from this file to find pyproject.toml
    current = Path(__file__).parent.parent
    for _ in range(5):  # Don't go too far up
        if (current / "pyproject.toml").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    # 3. Check current working directory
    cwd = Path.cwd()
    if (cwd / "agents").exists():
        return cwd

    # Fall back to parent of orchestrator package
    return Path(__file__).parent.parent


def _get_resource_path(resource_name: str) -> Path:
    """Get path to a resource directory.

    Args:
        resource_name: Name of the resource directory (agents, skills, commands)

    Returns:
        Path to the resource directory

    Raises:
        FileNotFoundError: If resource directory cannot be found
    """
    root = get_project_root()
    resource_path = root / resource_name

    if resource_path.exists():
        return resource_path

    raise FileNotFoundError(
        f"Resource '{resource_name}' not found at {resource_path}. "
        f"Project root: {root}. "
        f"Set SQUAD_ROOT environment variable to override."
    )


def get_agents_dir() -> Path:
    """Get path to the agents directory."""
    return _get_resource_path("agents")


def get_skills_dir() -> Path:
    """Get path to the skills directory."""
    return _get_resource_path("skills")


def get_commands_dir() -> Path:
    """Get path to the commands directory."""
    return _get_resource_path("commands")


def get_swarm_dir() -> Path:
    """Get path to the .swarm directory for persistent data.

    Creates the directory if it doesn't exist.
    """
    root = get_project_root()
    swarm_dir = root / ".swarm"
    swarm_dir.mkdir(exist_ok=True)
    return swarm_dir


def get_all_resource_dirs() -> dict[str, Path]:
    """Get paths to all resource directories.

    Returns:
        Dict mapping resource names to their paths
    """
    return {
        "agents": get_agents_dir(),
        "skills": get_skills_dir(),
        "commands": get_commands_dir(),
    }
