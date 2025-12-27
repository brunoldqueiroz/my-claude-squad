"""Tool aliases for simplified MCP invocation.

Provides short, memorable aliases for common MCP tool operations.
Instead of calling mcp__squad__memory_query, users can use 'squad memory search'.
"""

from dataclasses import dataclass
from typing import Any, Callable

from orchestrator.tracing import observe


@dataclass
class Alias:
    """Represents a tool alias mapping."""

    name: str  # Short name (e.g., "status")
    tool: str  # Full tool name (e.g., "swarm_status")
    description: str
    category: str  # Group for organization
    default_args: dict[str, Any] | None = None  # Sensible defaults


# Alias registry - maps short names to full tool invocations
ALIASES: dict[str, Alias] = {
    # === Status & Info ===
    "status": Alias(
        name="status",
        tool="swarm_status",
        description="Get swarm status overview",
        category="status",
    ),
    "health": Alias(
        name="health",
        tool="get_health",
        description="Get system health",
        category="status",
    ),
    "metrics": Alias(
        name="metrics",
        tool="get_metrics",
        description="Get orchestration metrics",
        category="status",
    ),
    "agents": Alias(
        name="agents",
        tool="list_agents",
        description="List all available agents",
        category="agents",
    ),

    # === Agent Operations ===
    "spawn": Alias(
        name="spawn",
        tool="spawn_agent",
        description="Spawn an agent for a task",
        category="agents",
    ),
    "route": Alias(
        name="route",
        tool="route_task",
        description="Find best agent for a task",
        category="agents",
    ),
    "agent-health": Alias(
        name="agent-health",
        tool="get_agent_health",
        description="Get health status of agents",
        category="agents",
    ),

    # === Memory Operations ===
    "remember": Alias(
        name="remember",
        tool="memory_store",
        description="Store a key-value memory",
        category="memory",
    ),
    "recall": Alias(
        name="recall",
        tool="memory_query",
        description="Query stored memories",
        category="memory",
    ),
    "search": Alias(
        name="search",
        tool="semantic_search",
        description="Semantic similarity search",
        category="memory",
    ),
    "learn": Alias(
        name="learn",
        tool="semantic_store",
        description="Store memory with semantic embedding",
        category="memory",
    ),

    # === Task & Workflow ===
    "plan": Alias(
        name="plan",
        tool="decompose_task",
        description="Decompose a complex task",
        category="workflow",
    ),
    "tasks": Alias(
        name="tasks",
        tool="get_task_graph",
        description="View task dependency graph",
        category="workflow",
    ),
    "ready": Alias(
        name="ready",
        tool="get_ready_tasks",
        description="Get tasks ready to execute",
        category="workflow",
    ),
    "done": Alias(
        name="done",
        tool="complete_run",
        description="Mark a task as complete",
        category="workflow",
    ),
    "workflow": Alias(
        name="workflow",
        tool="execute_workflow",
        description="Execute a task workflow",
        category="workflow",
    ),

    # === Swarms & Topology ===
    "swarm": Alias(
        name="swarm",
        tool="create_swarm",
        description="Create a new swarm",
        category="swarm",
    ),
    "swarms": Alias(
        name="swarms",
        tool="list_swarms",
        description="List all swarms",
        category="swarm",
    ),

    # === Sessions ===
    "session": Alias(
        name="session",
        tool="create_session",
        description="Create a work session",
        category="session",
    ),
    "sessions": Alias(
        name="sessions",
        tool="list_sessions_tool",
        description="List all sessions",
        category="session",
    ),
    "pause": Alias(
        name="pause",
        tool="pause_session",
        description="Pause a session",
        category="session",
    ),
    "resume": Alias(
        name="resume",
        tool="resume_session",
        description="Resume a session",
        category="session",
    ),
    "progress": Alias(
        name="progress",
        tool="get_session_progress",
        description="Get session progress",
        category="session",
    ),

    # === Command Tools ===
    "pipeline": Alias(
        name="pipeline",
        tool="create_pipeline",
        description="Generate data pipeline boilerplate",
        category="commands",
    ),
    "dockerfile": Alias(
        name="dockerfile",
        tool="create_dockerfile",
        description="Create optimized Dockerfile",
        category="commands",
    ),
    "k8s": Alias(
        name="k8s",
        tool="create_k8s_manifest",
        description="Generate Kubernetes manifests",
        category="commands",
    ),
    "rag": Alias(
        name="rag",
        tool="scaffold_rag",
        description="Scaffold RAG application",
        category="commands",
    ),
    "mcp": Alias(
        name="mcp",
        tool="scaffold_mcp_server",
        description="Scaffold MCP server",
        category="commands",
    ),
    "commit": Alias(
        name="commit",
        tool="generate_commit_message",
        description="Generate commit message",
        category="commands",
    ),
    "docs": Alias(
        name="docs",
        tool="lookup_docs",
        description="Look up library documentation",
        category="commands",
    ),
    "sql": Alias(
        name="sql",
        tool="analyze_query",
        description="Analyze SQL query",
        category="commands",
    ),
    "profile": Alias(
        name="profile",
        tool="analyze_data",
        description="Profile a dataset",
        category="commands",
    ),

    # === Events & Hooks ===
    "events": Alias(
        name="events",
        tool="get_events",
        description="Get recent events",
        category="system",
    ),
    "hooks": Alias(
        name="hooks",
        tool="list_hooks",
        description="List registered hooks",
        category="system",
    ),
    "cleanup": Alias(
        name="cleanup",
        tool="cleanup_storage",
        description="Clean up old data",
        category="system",
    ),
    "storage": Alias(
        name="storage",
        tool="get_storage_stats",
        description="Get storage statistics",
        category="system",
    ),
}

# Reverse mapping: tool name -> alias name
TOOL_TO_ALIAS: dict[str, str] = {alias.tool: name for name, alias in ALIASES.items()}


class AliasResolver:
    """Resolves aliases to tool invocations."""

    def __init__(self, tool_registry: dict[str, Callable] | None = None):
        """Initialize resolver.

        Args:
            tool_registry: Optional mapping of tool names to functions
        """
        self.tool_registry = tool_registry or {}

    def register_tool(self, name: str, func: Callable) -> None:
        """Register a tool function.

        Args:
            name: Tool name
            func: Tool function
        """
        self.tool_registry[name] = func

    @observe(name="resolve_alias")
    def resolve(self, alias_name: str) -> Alias | None:
        """Resolve an alias to its full tool information.

        Args:
            alias_name: Short alias name

        Returns:
            Alias info or None if not found
        """
        return ALIASES.get(alias_name.lower())

    @observe(name="execute_alias")
    def execute(self, alias_name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute an alias with optional arguments.

        Args:
            alias_name: Short alias name
            **kwargs: Arguments to pass to the tool

        Returns:
            Result from the tool execution
        """
        alias = self.resolve(alias_name)
        if not alias:
            return {
                "success": False,
                "error": f"Unknown alias: {alias_name}",
                "available": list(ALIASES.keys()),
            }

        tool_func = self.tool_registry.get(alias.tool)
        if not tool_func:
            return {
                "success": False,
                "error": f"Tool not registered: {alias.tool}",
                "alias": alias_name,
            }

        # Merge default args with provided args
        args = {**(alias.default_args or {}), **kwargs}

        try:
            result = tool_func(**args)
            return {"success": True, "result": result, "tool": alias.tool}
        except Exception as e:
            return {"success": False, "error": str(e), "tool": alias.tool}

    def list_aliases(self, category: str | None = None) -> list[dict[str, Any]]:
        """List available aliases.

        Args:
            category: Optional category filter

        Returns:
            List of alias information
        """
        aliases = []
        for name, alias in ALIASES.items():
            if category and alias.category != category:
                continue
            aliases.append({
                "alias": name,
                "tool": alias.tool,
                "description": alias.description,
                "category": alias.category,
            })
        return sorted(aliases, key=lambda x: (x["category"], x["alias"]))

    def get_categories(self) -> list[str]:
        """Get all alias categories.

        Returns:
            Sorted list of category names
        """
        return sorted(set(a.category for a in ALIASES.values()))

    def suggest(self, partial: str) -> list[str]:
        """Suggest aliases matching a partial input.

        Args:
            partial: Partial alias name

        Returns:
            List of matching alias names
        """
        partial_lower = partial.lower()
        matches = []

        for name, alias in ALIASES.items():
            if name.startswith(partial_lower):
                matches.append(name)
            elif partial_lower in alias.description.lower():
                matches.append(name)
            elif partial_lower in alias.tool.lower():
                matches.append(name)

        return sorted(set(matches))


# Singleton instance
_resolver: AliasResolver | None = None


def get_alias_resolver() -> AliasResolver:
    """Get the global alias resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = AliasResolver()
    return _resolver
