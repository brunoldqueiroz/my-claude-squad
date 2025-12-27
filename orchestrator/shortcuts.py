"""Compound commands that orchestrate multiple tools in one invocation.

Shortcuts combine common multi-step workflows into single commands,
reducing the need to manually chain MCP tool calls.
"""

from dataclasses import dataclass, field
from typing import Any, Callable
from pathlib import Path
import os

from orchestrator.tracing import observe


@dataclass
class ShortcutStep:
    """A single step in a shortcut workflow."""

    tool: str  # Tool name to call
    args: dict[str, Any]  # Arguments for the tool
    condition: str | None = None  # Optional condition to check
    store_result: str | None = None  # Key to store result for later steps


@dataclass
class Shortcut:
    """A compound command that executes multiple steps."""

    name: str
    description: str
    steps: list[ShortcutStep]
    category: str
    required_args: list[str] = field(default_factory=list)
    optional_args: dict[str, Any] = field(default_factory=dict)


# Project type detection patterns
PROJECT_PATTERNS: dict[str, list[str]] = {
    "python": ["pyproject.toml", "setup.py", "requirements.txt", "poetry.lock", "uv.lock"],
    "node": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
    "rust": ["Cargo.toml", "Cargo.lock"],
    "go": ["go.mod", "go.sum"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "dbt": ["dbt_project.yml"],
    "airflow": ["airflow.cfg", "dags/"],
    "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    "kubernetes": ["k8s/", "kubernetes/", "helm/"],
    "terraform": ["main.tf", "terraform.tfstate"],
}

# Agent suggestions by project type
PROJECT_AGENTS: dict[str, list[str]] = {
    "python": ["python-developer", "sql-specialist"],
    "node": ["python-developer"],  # We don't have a dedicated node agent yet
    "rust": ["python-developer"],
    "go": ["python-developer"],
    "java": ["python-developer"],
    "dbt": ["sql-specialist", "snowflake-specialist"],
    "airflow": ["airflow-specialist", "python-developer"],
    "docker": ["container-specialist", "kubernetes-specialist"],
    "kubernetes": ["kubernetes-specialist", "container-specialist"],
    "terraform": ["aws-specialist"],
}


class ShortcutExecutor:
    """Executes compound shortcuts by orchestrating multiple tools."""

    def __init__(self):
        """Initialize the executor."""
        self._tool_registry: dict[str, Callable] = {}
        self._results: dict[str, Any] = {}

    def register_tool(self, name: str, func: Callable) -> None:
        """Register a tool function for shortcut execution.

        Args:
            name: Tool name
            func: Tool function
        """
        self._tool_registry[name] = func

    def register_tools(self, tools: dict[str, Callable]) -> None:
        """Register multiple tools at once.

        Args:
            tools: Mapping of tool names to functions
        """
        self._tool_registry.update(tools)

    @observe(name="detect_project_type")
    def detect_project_type(self, path: str | Path | None = None) -> dict[str, Any]:
        """Detect project type from directory contents.

        Args:
            path: Path to check (defaults to cwd)

        Returns:
            Project type information with recommended agents
        """
        check_path = Path(path) if path else Path.cwd()
        detected: list[str] = []

        for project_type, patterns in PROJECT_PATTERNS.items():
            for pattern in patterns:
                check_target = check_path / pattern
                if check_target.exists():
                    detected.append(project_type)
                    break

        # Get recommended agents
        agents: set[str] = set()
        for ptype in detected:
            agents.update(PROJECT_AGENTS.get(ptype, []))

        return {
            "path": str(check_path),
            "detected_types": detected,
            "primary_type": detected[0] if detected else "unknown",
            "recommended_agents": list(agents),
            "files_checked": list(PROJECT_PATTERNS.keys()),
        }

    @observe(name="execute_shortcut")
    def execute(
        self,
        shortcut: Shortcut,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a compound shortcut.

        Args:
            shortcut: Shortcut to execute
            args: Arguments for the shortcut

        Returns:
            Combined results from all steps
        """
        # Validate required args
        missing = [arg for arg in shortcut.required_args if arg not in args]
        if missing:
            return {
                "success": False,
                "error": f"Missing required arguments: {missing}",
                "shortcut": shortcut.name,
            }

        # Merge with defaults
        full_args = {**shortcut.optional_args, **args}

        # Clear previous results
        self._results = {"_args": full_args}

        # Execute each step
        step_results: list[dict[str, Any]] = []
        for i, step in enumerate(shortcut.steps):
            try:
                result = self._execute_step(step, full_args)
                step_results.append({
                    "step": i + 1,
                    "tool": step.tool,
                    "success": True,
                    "result": result,
                })

                if step.store_result:
                    self._results[step.store_result] = result

            except Exception as e:
                step_results.append({
                    "step": i + 1,
                    "tool": step.tool,
                    "success": False,
                    "error": str(e),
                })
                # Continue on error by default

        return {
            "success": all(s["success"] for s in step_results),
            "shortcut": shortcut.name,
            "steps_executed": len(step_results),
            "results": step_results,
        }

    def _execute_step(self, step: ShortcutStep, args: dict[str, Any]) -> Any:
        """Execute a single step.

        Args:
            step: Step to execute
            args: Full arguments dictionary

        Returns:
            Step result
        """
        tool_func = self._tool_registry.get(step.tool)
        if not tool_func:
            raise ValueError(f"Tool not registered: {step.tool}")

        # Resolve step arguments (can reference previous results)
        resolved_args = self._resolve_args(step.args, args)

        return tool_func(**resolved_args)

    def _resolve_args(
        self,
        step_args: dict[str, Any],
        full_args: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve step arguments, replacing placeholders.

        Args:
            step_args: Arguments from step definition
            full_args: Full arguments from user

        Returns:
            Resolved arguments
        """
        resolved = {}
        for key, value in step_args.items():
            if isinstance(value, str):
                # Replace ${arg_name} with actual values
                if value.startswith("${") and value.endswith("}"):
                    ref = value[2:-1]
                    if ref in full_args:
                        resolved[key] = full_args[ref]
                    elif ref in self._results:
                        resolved[key] = self._results[ref]
                    else:
                        resolved[key] = value
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved


# Predefined shortcuts
SHORTCUTS: dict[str, Shortcut] = {
    "etl-pipeline": Shortcut(
        name="etl-pipeline",
        description="Create complete ETL pipeline with session tracking",
        category="data",
        required_args=["source", "target", "name"],
        optional_args={"incremental": False},
        steps=[
            ShortcutStep(
                tool="create_pipeline",
                args={
                    "source": "${source}",
                    "target": "${target}",
                    "name": "${name}",
                    "incremental": "${incremental}",
                },
                store_result="pipeline",
            ),
            ShortcutStep(
                tool="create_session",
                args={
                    "name": "${name}",
                    "description": "ETL Pipeline: ${source} → ${target}",
                },
                store_result="session",
            ),
        ],
    ),

    "review-pr": Shortcut(
        name="review-pr",
        description="Review a pull request with specialized agents",
        category="development",
        required_args=["pr_number"],
        optional_args={"repo": None},
        steps=[
            ShortcutStep(
                tool="route_task",
                args={"task": "Review pull request code changes"},
                store_result="reviewer",
            ),
            ShortcutStep(
                tool="create_session",
                args={
                    "name": "PR Review #${pr_number}",
                    "description": "Reviewing PR #${pr_number}",
                },
                store_result="session",
            ),
        ],
    ),

    "deploy-service": Shortcut(
        name="deploy-service",
        description="Generate deployment artifacts (Dockerfile + K8s)",
        category="devops",
        required_args=["app_name"],
        optional_args={"replicas": 2, "port": 8000},
        steps=[
            ShortcutStep(
                tool="create_dockerfile",
                args={"project_type": "python", "optimize_for": "size"},
                store_result="dockerfile",
            ),
            ShortcutStep(
                tool="create_k8s_manifest",
                args={
                    "app_name": "${app_name}",
                    "replicas": "${replicas}",
                    "port": "${port}",
                },
                store_result="k8s",
            ),
        ],
    ),

    "start-rag": Shortcut(
        name="start-rag",
        description="Scaffold RAG application with session tracking",
        category="ai",
        required_args=["name"],
        optional_args={"vectordb": "chromadb", "framework": "langchain"},
        steps=[
            ShortcutStep(
                tool="scaffold_rag",
                args={
                    "name": "${name}",
                    "vectordb": "${vectordb}",
                    "framework": "${framework}",
                },
                store_result="rag",
            ),
            ShortcutStep(
                tool="create_session",
                args={
                    "name": "RAG: ${name}",
                    "description": "Building RAG app with ${framework} + ${vectordb}",
                },
                store_result="session",
            ),
        ],
    ),

    "analyze-slow-query": Shortcut(
        name="analyze-slow-query",
        description="Analyze query and spawn SQL specialist",
        category="data",
        required_args=["sql"],
        optional_args={},
        steps=[
            ShortcutStep(
                tool="analyze_query",
                args={"sql": "${sql}"},
                store_result="analysis",
            ),
            ShortcutStep(
                tool="spawn_agent",
                args={
                    "agent_name": "sql-specialist",
                    "task": "Optimize query based on analysis",
                },
                store_result="agent",
            ),
        ],
    ),

    "learn-library": Shortcut(
        name="learn-library",
        description="Look up library docs and store in semantic memory",
        category="research",
        required_args=["library"],
        optional_args={"topic": None},
        steps=[
            ShortcutStep(
                tool="lookup_docs",
                args={
                    "library": "${library}",
                    "topic": "${topic}",
                },
                store_result="docs_info",
            ),
        ],
    ),
}


# Singleton instance
_executor: ShortcutExecutor | None = None


def get_shortcut_executor() -> ShortcutExecutor:
    """Get the global shortcut executor instance."""
    global _executor
    if _executor is None:
        _executor = ShortcutExecutor()
    return _executor


def list_shortcuts(category: str | None = None) -> list[dict[str, Any]]:
    """List available shortcuts.

    Args:
        category: Optional category filter

    Returns:
        List of shortcut information
    """
    result = []
    for name, shortcut in SHORTCUTS.items():
        if category and shortcut.category != category:
            continue
        result.append({
            "name": name,
            "description": shortcut.description,
            "category": shortcut.category,
            "required_args": shortcut.required_args,
            "optional_args": shortcut.optional_args,
            "steps": len(shortcut.steps),
        })
    return sorted(result, key=lambda x: (x["category"], x["name"]))


def get_shortcut_categories() -> list[str]:
    """Get all shortcut categories.

    Returns:
        Sorted list of category names
    """
    return sorted(set(s.category for s in SHORTCUTS.values()))
