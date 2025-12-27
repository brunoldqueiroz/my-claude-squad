"""Coordinator - routes tasks to agents and manages task decomposition."""

import uuid
from datetime import datetime
from pathlib import Path

from orchestrator.agent_registry import AgentRegistry
from orchestrator.memory import SwarmMemory
from orchestrator.tracing import observe, score_task, update_span, update_trace
from orchestrator.types import Agent, AgentRun, SwarmStatus, Task, TaskStatus


class Coordinator:
    """Coordinates task routing and agent management."""

    def __init__(self, agents_dir: Path | None = None, db_path: Path | None = None):
        """Initialize the coordinator.

        Args:
            agents_dir: Path to agents directory
            db_path: Path to DuckDB database
        """
        self.registry = AgentRegistry(agents_dir)
        self.memory = SwarmMemory(db_path)
        self._active_tasks: dict[str, Task] = {}
        self._task_to_run: dict[str, str] = {}  # task_id -> run_id mapping

    @observe(name="route_task")
    def route_task(self, task_description: str) -> Agent | None:
        """Find the best agent for a given task.

        Args:
            task_description: Description of the task

        Returns:
            Best matching agent, or None if no match
        """
        task_lower = task_description.lower()

        # Define keyword to agent mappings (ordered by specificity - more specific first)
        routing_rules = {
            # Snowflake (specific platform)
            "snowflake": "snowflake-specialist",
            "snowpipe": "snowflake-specialist",
            "snowflake stream": "snowflake-specialist",
            "snowflake task": "snowflake-specialist",
            "snowflake share": "snowflake-specialist",
            # SQL Server (specific platform)
            "sql server": "sql-server-specialist",
            "sqlserver": "sql-server-specialist",
            "t-sql": "sql-server-specialist",
            "tsql": "sql-server-specialist",
            "ssis": "sql-server-specialist",
            "ssrs": "sql-server-specialist",
            "ssas": "sql-server-specialist",
            "mssql": "sql-server-specialist",
            "stored procedure": "sql-server-specialist",
            # Spark (specific platform)
            "spark": "spark-specialist",
            "pyspark": "spark-specialist",
            "databricks": "spark-specialist",
            "delta lake": "spark-specialist",
            "spark sql": "spark-specialist",
            # Airflow (specific platform)
            "airflow": "airflow-specialist",
            "mwaa": "airflow-specialist",
            "dag": "airflow-specialist",
            "xcom": "airflow-specialist",
            "airflow operator": "airflow-specialist",
            "airflow sensor": "airflow-specialist",
            # AWS (cloud services)
            "aws": "aws-specialist",
            "s3": "aws-specialist",
            "lambda": "aws-specialist",
            "glue": "aws-specialist",
            "redshift": "aws-specialist",
            "athena": "aws-specialist",
            "ecs": "aws-specialist",
            "eks": "aws-specialist",
            "sagemaker": "aws-specialist",
            "kinesis": "aws-specialist",
            "step function": "aws-specialist",
            "stepfunction": "aws-specialist",
            "cloudformation": "aws-specialist",
            "terraform": "aws-specialist",
            "cdk": "aws-specialist",
            "iam role": "aws-specialist",
            "dynamodb": "aws-specialist",
            "sqs": "aws-specialist",
            "sns": "aws-specialist",
            "eventbridge": "aws-specialist",
            # Containers
            "docker": "container-specialist",
            "dockerfile": "container-specialist",
            "container": "container-specialist",
            "docker-compose": "container-specialist",
            "docker compose": "container-specialist",
            "podman": "container-specialist",
            "buildkit": "container-specialist",
            "multi-stage": "container-specialist",
            # Kubernetes
            "kubernetes": "kubernetes-specialist",
            "k8s": "kubernetes-specialist",
            "helm": "kubernetes-specialist",
            "kubectl": "kubernetes-specialist",
            "kustomize": "kubernetes-specialist",
            "argocd": "kubernetes-specialist",
            "ingress": "kubernetes-specialist",
            "deployment yaml": "kubernetes-specialist",
            # RAG & Vector DBs (before generic terms)
            "rag": "rag-specialist",
            "retrieval augmented": "rag-specialist",
            "vector database": "rag-specialist",
            "vector db": "rag-specialist",
            "embedding": "rag-specialist",
            "qdrant": "rag-specialist",
            "chromadb": "rag-specialist",
            "chroma": "rag-specialist",
            "pinecone": "rag-specialist",
            "weaviate": "rag-specialist",
            "pgvector": "rag-specialist",
            "llamaindex": "rag-specialist",
            "llama-index": "rag-specialist",
            "semantic search": "rag-specialist",
            "chunking": "rag-specialist",
            # Agent Frameworks
            "langchain": "agent-framework-specialist",
            "langgraph": "agent-framework-specialist",
            "crewai": "agent-framework-specialist",
            "autogen": "agent-framework-specialist",
            "pydantic-ai": "agent-framework-specialist",
            "smolagents": "agent-framework-specialist",
            "agency swarm": "agent-framework-specialist",
            "multi-agent system": "agent-framework-specialist",
            # LLM Integration
            "llm": "llm-specialist",
            "ollama": "llm-specialist",
            "prompt engineering": "llm-specialist",
            "prompt template": "llm-specialist",
            "openai api": "llm-specialist",
            "anthropic api": "llm-specialist",
            "claude api": "llm-specialist",
            "gemini": "llm-specialist",
            "mistral": "llm-specialist",
            "groq": "llm-specialist",
            "together ai": "llm-specialist",
            "litellm": "llm-specialist",
            "structured output": "llm-specialist",
            "function calling": "llm-specialist",
            "tool use": "llm-specialist",
            # Automation & Chatbots
            "n8n": "automation-specialist",
            "dify": "automation-specialist",
            "mcp server": "automation-specialist",
            "chatbot": "automation-specialist",
            "webhook": "automation-specialist",
            "zapier": "automation-specialist",
            "make.com": "automation-specialist",
            "workflow automation": "automation-specialist",
            # Python Development
            "python": "python-developer",
            "etl": "python-developer",
            "pandas": "python-developer",
            "polars": "python-developer",
            "fastapi": "python-developer",
            "flask": "python-developer",
            "pytest": "python-developer",
            "poetry": "python-developer",
            "uv package": "python-developer",
            # SQL (generic - after specific DBs)
            "sql query": "sql-specialist",
            "sql optimization": "sql-specialist",
            "query optimization": "sql-specialist",
            "cte": "sql-specialist",
            "window function": "sql-specialist",
            "subquery": "sql-specialist",
            "join optimization": "sql-specialist",
            "index strategy": "sql-specialist",
            # Documentation
            "document": "documenter",
            "readme": "documenter",
            "changelog": "documenter",
            "adr": "documenter",
            "architecture decision": "documenter",
            "api doc": "documenter",
            "docstring": "documenter",
            # Git
            "commit message": "git-commit-writer",
            "git commit": "git-commit-writer",
            # Plugin Development
            "plugin": "plugin-developer",
            "new agent": "plugin-developer",
            "new command": "plugin-developer",
            "new skill": "plugin-developer",
            # Orchestration / Complex Tasks
            "coordinate": "squad-orchestrator",
            "decompose": "squad-orchestrator",
            "orchestrate": "squad-orchestrator",
            "multi-specialist": "squad-orchestrator",
            "complex task": "squad-orchestrator",
            "end-to-end": "squad-orchestrator",
            "full pipeline": "squad-orchestrator",
            # Self-Improvement
            "audit plugin": "squad-orchestrator",
            "improve routing": "squad-orchestrator",
            "self-improve": "squad-orchestrator",
            "add tests": "squad-orchestrator",
            "test coverage": "squad-orchestrator",
        }

        # Check routing rules
        matched_keyword = None
        confidence = "low"
        agent = None

        for keyword, agent_name in routing_rules.items():
            if keyword in task_lower:
                agent = self.registry.get_agent(agent_name)
                if agent:
                    matched_keyword = keyword
                    confidence = "high"
                    break

        # Fall back to registry search
        if not agent:
            matches = self.registry.find_agents_by_trigger(task_description)
            if matches:
                agent = matches[0]
                confidence = "medium"

        # Default to squad-orchestrator for complex tasks
        if not agent:
            agent = self.registry.get_agent("squad-orchestrator")

        # Update Langfuse span with routing metadata
        if agent:
            update_span(
                metadata={
                    "task": task_description[:200],
                    "confidence": confidence,
                    "matched_keyword": matched_keyword,
                    "model": agent.model.value,
                },
                output={"agent": agent.name, "confidence": confidence},
            )

        return agent

    def decompose_task(self, task_description: str) -> list[tuple[str, Agent | None]]:
        """Decompose a complex task into subtasks with agent assignments.

        Args:
            task_description: Complex task description

        Returns:
            List of (subtask, agent) tuples
        """
        subtasks = []

        # Simple decomposition based on connectors
        connectors = [" and ", " then ", " with ", ", "]

        parts = [task_description]
        for connector in connectors:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(connector))
            parts = new_parts

        # Clean and assign agents
        for part in parts:
            part = part.strip()
            if len(part) > 10:  # Minimum meaningful task length
                agent = self.route_task(part)
                subtasks.append((part, agent))

        # If no decomposition happened, return original with best agent
        if len(subtasks) <= 1:
            agent = self.route_task(task_description)
            return [(task_description, agent)]

        return subtasks

    @observe(name="create_task")
    def create_task(self, description: str, agent_name: str | None = None) -> Task:
        """Create a new task.

        Args:
            description: Task description
            agent_name: Optional agent name override

        Returns:
            Created Task
        """
        task_id = str(uuid.uuid4())[:8]

        if agent_name is None:
            agent = self.route_task(description)
            agent_name = agent.name if agent else None

        task = Task(
            id=task_id,
            description=description,
            agent_name=agent_name,
            status=TaskStatus.PENDING,
            trace_id=task_id,  # Use task_id as trace reference
        )

        self._active_tasks[task_id] = task

        # Update Langfuse trace with task context
        update_trace(
            user_id=agent_name,
            metadata={"description": description[:500], "task_id": task_id},
            tags=["task", agent_name or "unassigned"],
        )

        return task

    @observe(name="start_task")
    def start_task(self, task_id: str) -> AgentRun | None:
        """Start a task and create an agent run.

        Args:
            task_id: Task ID to start

        Returns:
            AgentRun if task exists, None otherwise
        """
        task = self._active_tasks.get(task_id)
        if not task or not task.agent_name:
            return None

        task.status = TaskStatus.IN_PROGRESS
        run_id = str(uuid.uuid4())[:8]

        # Store mapping for completion
        self._task_to_run[task_id] = run_id

        self.memory.log_run_start(run_id, task.agent_name, task.description)

        # Update Langfuse span
        update_span(
            metadata={"run_id": run_id, "task_id": task_id},
            output={"status": "started", "agent": task.agent_name},
        )

        return AgentRun(
            id=run_id,
            agent_name=task.agent_name,
            task=task.description,
            status=TaskStatus.IN_PROGRESS,
        )

    @observe(name="complete_task")
    def complete_task(
        self, task_id: str, result: str | None = None, success: bool = True, tokens_used: int = 0
    ) -> None:
        """Mark a task as complete.

        Args:
            task_id: Task ID to complete
            result: Optional result text
            success: Whether task succeeded
            tokens_used: Number of tokens used
        """
        task = self._active_tasks.get(task_id)
        if not task:
            return

        # Update task status
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.result = result

        # Calculate duration
        duration_ms = (task.completed_at - task.created_at).total_seconds() * 1000

        # Persist to database
        run_id = self._task_to_run.get(task_id)
        if run_id:
            self.memory.log_run_complete(
                run_id=run_id,
                status=task.status,
                result=result,
                tokens=tokens_used,
            )
            del self._task_to_run[task_id]

        # Update Langfuse span with completion details
        update_span(
            metadata={
                "duration_ms": duration_ms,
                "tokens_used": tokens_used,
                "agent": task.agent_name,
            },
            output={
                "result": result[:200] if result else None,
                "success": success,
            },
        )

        # Score the task in Langfuse
        score_task(
            name="success",
            value=1.0 if success else 0.0,
            comment=f"Task {'completed' if success else 'failed'}: {task_id}",
        )

    def get_swarm_status(self) -> SwarmStatus:
        """Get current swarm status.

        Returns:
            SwarmStatus with current state
        """
        agents = self.registry.list_agents()
        stats = self.memory.get_run_stats()
        recent_runs = self.memory.get_recent_runs(5)

        active_count = sum(1 for t in self._active_tasks.values() if t.status == TaskStatus.IN_PROGRESS)

        return SwarmStatus(
            total_agents=len(agents),
            active_tasks=active_count,
            completed_tasks=stats["completed"],
            agents=agents,
            recent_runs=recent_runs,
        )

    def close(self) -> None:
        """Close resources."""
        self.memory.close()
