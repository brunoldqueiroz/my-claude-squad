"""Session management for persistent, resumable workflows.

Sessions provide:
- Persistent multi-task workflows that survive restarts
- Pause/resume capability for long-running work
- Progress tracking across tasks
- Optional integration with swarm topologies

Sessions can be associated with swarms for topology-aware execution.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from orchestrator.memory import SwarmMemory
from orchestrator.topology import TopologyManager
from orchestrator.types import (
    Session,
    SessionStatus,
    SessionTask,
    Task,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages persistent, resumable work sessions.

    Handles:
    - Session lifecycle (create, pause, resume, complete)
    - Task progress tracking within sessions
    - Integration with TopologyManager for swarm-aware execution
    - Persistence via SwarmMemory
    """

    def __init__(
        self,
        memory: SwarmMemory | None = None,
        topology_manager: TopologyManager | None = None,
    ):
        """Initialize the session manager.

        Args:
            memory: SwarmMemory for persistence
            topology_manager: Optional TopologyManager for swarm integration
        """
        self._memory = memory or SwarmMemory()
        self._topology_manager = topology_manager
        # Cache of active sessions for fast lookup
        self._sessions: dict[str, Session] = {}
        self._load_active_sessions()

    def _load_active_sessions(self) -> None:
        """Load active/paused sessions from storage into cache."""
        try:
            sessions = self._memory.get_active_sessions()
            for session in sessions:
                self._sessions[session.id] = session
            logger.info(f"Loaded {len(sessions)} active sessions from storage")
        except Exception as e:
            logger.warning(f"Failed to load sessions: {e}")

    def create_session(
        self,
        name: str,
        tasks: list[dict[str, Any]] | None = None,
        description: str | None = None,
        swarm_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session.

        Args:
            name: Human-readable session name
            tasks: Optional list of task dicts with 'description' and optional 'agent_name'
            description: Optional session description
            swarm_id: Optional swarm ID for topology-aware execution
            metadata: Optional metadata dict

        Returns:
            Created Session instance
        """
        session_id = str(uuid.uuid4())[:8]

        # Convert task dicts to SessionTask objects
        session_tasks = []
        if tasks:
            for i, task_data in enumerate(tasks):
                session_task = SessionTask(
                    task_id=f"{session_id}-task-{i}",
                    description=task_data.get("description", ""),
                    agent_name=task_data.get("agent_name"),
                    order=i,
                )
                session_tasks.append(session_task)

        session = Session(
            id=session_id,
            name=name,
            description=description,
            status=SessionStatus.ACTIVE,
            swarm_id=swarm_id,
            tasks=session_tasks,
            metadata=metadata or {},
        )

        # Save to storage and cache
        self._memory.save_session(session)
        self._sessions[session_id] = session

        logger.info(f"Created session '{name}' ({session_id}) with {len(session_tasks)} tasks")
        return session

    def create_session_from_swarm(
        self,
        name: str,
        swarm_id: str,
        task_description: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session | None:
        """Create a session with tasks generated from a swarm topology.

        Uses the TopologyManager to create tasks based on the swarm's
        coordination pattern.

        Args:
            name: Human-readable session name
            swarm_id: ID of the swarm to use for task generation
            task_description: Description of the overall task
            description: Optional session description
            metadata: Optional metadata dict

        Returns:
            Created Session instance or None if swarm not found
        """
        if not self._topology_manager:
            logger.error("No TopologyManager configured for swarm-based sessions")
            return None

        # Get tasks from topology
        topology_tasks = self._topology_manager.create_workflow_tasks(
            swarm_id, task_description
        )

        if not topology_tasks:
            logger.warning(f"No tasks generated from swarm {swarm_id}")
            return None

        # Convert topology tasks to session task dicts
        task_dicts = [
            {"description": t.description, "agent_name": t.agent_name}
            for t in topology_tasks
        ]

        return self.create_session(
            name=name,
            tasks=task_dicts,
            description=description,
            swarm_id=swarm_id,
            metadata=metadata,
        )

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session instance or None if not found
        """
        # Check cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Try loading from storage
        session = self._memory.get_session(session_id)
        if session:
            self._sessions[session_id] = session
        return session

    def list_sessions(
        self,
        status: SessionStatus | None = None,
        active_only: bool = False,
        limit: int = 50,
    ) -> list[Session]:
        """List sessions with optional filtering.

        Args:
            status: Optional status to filter by
            active_only: If True, only return active/paused sessions
            limit: Maximum results to return

        Returns:
            List of Session instances
        """
        if active_only:
            return self._memory.get_active_sessions()
        return self._memory.list_sessions(status=status, limit=limit)

    def pause_session(self, session_id: str) -> Session | None:
        """Pause an active session.

        Args:
            session_id: Session ID to pause

        Returns:
            Updated Session instance or None if not found/invalid
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return None

        if session.status != SessionStatus.ACTIVE:
            logger.warning(f"Cannot pause session {session_id} with status {session.status}")
            return None

        session.status = SessionStatus.PAUSED
        session.paused_at = datetime.now()
        session.updated_at = datetime.now()

        self._memory.save_session(session)
        self._sessions[session_id] = session

        logger.info(f"Paused session {session_id}")
        return session

    def resume_session(self, session_id: str) -> Session | None:
        """Resume a paused session.

        Args:
            session_id: Session ID to resume

        Returns:
            Updated Session instance or None if not found/invalid
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return None

        if session.status != SessionStatus.PAUSED:
            logger.warning(f"Cannot resume session {session_id} with status {session.status}")
            return None

        session.status = SessionStatus.ACTIVE
        session.paused_at = None
        session.updated_at = datetime.now()

        self._memory.save_session(session)
        self._sessions[session_id] = session

        logger.info(f"Resumed session {session_id}")
        return session

    def cancel_session(self, session_id: str) -> Session | None:
        """Cancel a session.

        Args:
            session_id: Session ID to cancel

        Returns:
            Updated Session instance or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return None

        if session.status in (SessionStatus.COMPLETED, SessionStatus.CANCELLED):
            logger.warning(f"Session {session_id} already {session.status.value}")
            return session

        session.status = SessionStatus.CANCELLED
        session.completed_at = datetime.now()
        session.updated_at = datetime.now()

        self._memory.save_session(session)
        # Remove from active cache
        self._sessions.pop(session_id, None)

        logger.info(f"Cancelled session {session_id}")
        return session

    def add_task(
        self,
        session_id: str,
        description: str,
        agent_name: str | None = None,
    ) -> SessionTask | None:
        """Add a new task to a session.

        Args:
            session_id: Session ID to add task to
            description: Task description
            agent_name: Optional agent to assign

        Returns:
            Created SessionTask or None if session not found/inactive
        """
        session = self.get_session(session_id)
        if not session:
            return None

        if session.status not in (SessionStatus.ACTIVE, SessionStatus.PAUSED):
            logger.warning(f"Cannot add task to session {session_id} with status {session.status}")
            return None

        task_id = f"{session_id}-task-{len(session.tasks)}"
        task = SessionTask(
            task_id=task_id,
            description=description,
            agent_name=agent_name,
            order=len(session.tasks),
        )

        session.tasks.append(task)
        session.updated_at = datetime.now()

        self._memory.save_session(session)
        self._sessions[session_id] = session

        logger.info(f"Added task {task_id} to session {session_id}")
        return task

    def start_task(self, session_id: str, task_id: str) -> SessionTask | None:
        """Mark a task as in progress.

        Args:
            session_id: Session ID
            task_id: Task ID to start

        Returns:
            Updated SessionTask or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        task = next((t for t in session.tasks if t.task_id == task_id), None)
        if not task:
            logger.warning(f"Task {task_id} not found in session {session_id}")
            return None

        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not pending (status: {task.status})")
            return task

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        session.updated_at = datetime.now()

        # Update current task index if this task is being started
        for i, t in enumerate(session.tasks):
            if t.task_id == task_id:
                session.current_task_index = i
                break

        self._memory.save_session(session)
        self._sessions[session_id] = session

        logger.info(f"Started task {task_id} in session {session_id}")
        return task

    def complete_task(
        self,
        session_id: str,
        task_id: str,
        result: str | None = None,
        success: bool = True,
    ) -> SessionTask | None:
        """Mark a task as completed or failed.

        Args:
            session_id: Session ID
            task_id: Task ID to complete
            result: Optional result text
            success: Whether the task succeeded

        Returns:
            Updated SessionTask or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        task = next((t for t in session.tasks if t.task_id == task_id), None)
        if not task:
            logger.warning(f"Task {task_id} not found in session {session_id}")
            return None

        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.result = result
        if not success:
            task.error = result  # Store error message

        session.updated_at = datetime.now()

        # Check if all tasks are complete
        all_done = all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            for t in session.tasks
        )
        any_failed = any(t.status == TaskStatus.FAILED for t in session.tasks)

        if all_done:
            session.status = SessionStatus.FAILED if any_failed else SessionStatus.COMPLETED
            session.completed_at = datetime.now()
            # Remove from active cache
            self._sessions.pop(session_id, None)
            logger.info(f"Session {session_id} completed (status: {session.status.value})")
        else:
            # Advance to next pending task
            for i, t in enumerate(session.tasks):
                if t.status == TaskStatus.PENDING:
                    session.current_task_index = i
                    break

        self._memory.save_session(session)
        if session_id in self._sessions:
            self._sessions[session_id] = session

        logger.info(f"Completed task {task_id} in session {session_id} (success: {success})")
        return task

    def get_next_task(self, session_id: str) -> SessionTask | None:
        """Get the next pending task in a session.

        Args:
            session_id: Session ID

        Returns:
            Next pending SessionTask or None if all done
        """
        session = self.get_session(session_id)
        if not session:
            return None

        return session.current_task

    def get_session_progress(self, session_id: str) -> dict[str, Any] | None:
        """Get detailed progress information for a session.

        Args:
            session_id: Session ID

        Returns:
            Progress dict or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        pending = session.get_pending_tasks()
        completed = session.get_completed_tasks()
        failed = session.get_failed_tasks()
        in_progress = [t for t in session.tasks if t.status == TaskStatus.IN_PROGRESS]

        return {
            "session_id": session_id,
            "name": session.name,
            "status": session.status.value,
            "progress": session.progress,
            "total_tasks": len(session.tasks),
            "pending": len(pending),
            "in_progress": len(in_progress),
            "completed": len(completed),
            "failed": len(failed),
            "current_task": session.current_task.model_dump() if session.current_task else None,
            "swarm_id": session.swarm_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Remove from cache
        self._sessions.pop(session_id, None)

        # Remove from storage
        result = self._memory.delete_session(session_id)

        if result:
            logger.info(f"Deleted session {session_id}")
        return result

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Delete old completed/failed/cancelled sessions.

        Args:
            days: Delete sessions older than this many days

        Returns:
            Number of sessions deleted
        """
        count = self._memory.cleanup_old_sessions(days)
        logger.info(f"Cleaned up {count} old sessions (older than {days} days)")
        return count

    def get_session_status(self, session_id: str) -> dict[str, Any]:
        """Get detailed status of a session.

        Returns:
            Status dictionary with session info
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": f"Session {session_id} not found"}

        return {
            "id": session.id,
            "name": session.name,
            "description": session.description,
            "status": session.status.value,
            "progress": session.progress,
            "current_task_index": session.current_task_index,
            "task_count": len(session.tasks),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "agent_name": t.agent_name,
                    "status": t.status.value,
                    "order": t.order,
                }
                for t in session.tasks
            ],
            "swarm_id": session.swarm_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "paused_at": session.paused_at.isoformat() if session.paused_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }
