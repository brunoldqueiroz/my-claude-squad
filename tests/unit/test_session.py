"""Tests for session management."""

import pytest
from datetime import datetime

from orchestrator.session import SessionManager
from orchestrator.memory import SwarmMemory
from orchestrator.topology import TopologyManager
from orchestrator.types import (
    Session,
    SessionStatus,
    SessionTask,
    TaskStatus,
    TopologyType,
)


@pytest.fixture
def memory(tmp_path):
    """Create a temporary memory instance."""
    db_path = tmp_path / "test.duckdb"
    return SwarmMemory(db_path)


@pytest.fixture
def topology_manager(memory):
    """Create a topology manager."""
    return TopologyManager(memory=memory)


@pytest.fixture
def session_manager(memory, topology_manager):
    """Create a session manager."""
    return SessionManager(memory=memory, topology_manager=topology_manager)


class TestSessionManager:
    """Tests for SessionManager class."""

    def test_create_session_basic(self, session_manager):
        """Test creating a basic session."""
        session = session_manager.create_session(
            name="Test Session",
            description="A test session",
        )

        assert session.name == "Test Session"
        assert session.description == "A test session"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.tasks) == 0

    def test_create_session_with_tasks(self, session_manager):
        """Test creating a session with initial tasks."""
        tasks = [
            {"description": "Task 1", "agent_name": "python-developer"},
            {"description": "Task 2"},
            {"description": "Task 3", "agent_name": "sql-specialist"},
        ]

        session = session_manager.create_session(
            name="Task Session",
            tasks=tasks,
        )

        assert len(session.tasks) == 3
        assert session.tasks[0].description == "Task 1"
        assert session.tasks[0].agent_name == "python-developer"
        assert session.tasks[1].agent_name is None
        assert session.tasks[2].order == 2

    def test_get_session(self, session_manager):
        """Test retrieving a session by ID."""
        created = session_manager.create_session(name="Test")

        retrieved = session_manager.get_session(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test"

    def test_get_session_not_found(self, session_manager):
        """Test retrieving non-existent session."""
        assert session_manager.get_session("nonexistent") is None

    def test_list_sessions(self, session_manager):
        """Test listing sessions."""
        session_manager.create_session(name="Session 1")
        session_manager.create_session(name="Session 2")

        sessions = session_manager.list_sessions()
        assert len(sessions) == 2

    def test_list_sessions_by_status(self, session_manager):
        """Test filtering sessions by status."""
        s1 = session_manager.create_session(name="Active")
        s2 = session_manager.create_session(name="To Pause")
        session_manager.pause_session(s2.id)

        active = session_manager.list_sessions(status=SessionStatus.ACTIVE)
        paused = session_manager.list_sessions(status=SessionStatus.PAUSED)

        assert len(active) == 1
        assert active[0].name == "Active"
        assert len(paused) == 1
        assert paused[0].name == "To Pause"

    def test_list_sessions_active_only(self, session_manager):
        """Test filtering active/paused sessions only."""
        s1 = session_manager.create_session(name="Active")
        s2 = session_manager.create_session(name="Paused")
        s3 = session_manager.create_session(name="Cancelled")
        session_manager.pause_session(s2.id)
        session_manager.cancel_session(s3.id)

        active_sessions = session_manager.list_sessions(active_only=True)
        assert len(active_sessions) == 2  # Active and Paused

    def test_pause_session(self, session_manager):
        """Test pausing a session."""
        session = session_manager.create_session(name="To Pause")
        assert session.status == SessionStatus.ACTIVE

        paused = session_manager.pause_session(session.id)

        assert paused is not None
        assert paused.status == SessionStatus.PAUSED
        assert paused.paused_at is not None

    def test_pause_non_active_session(self, session_manager):
        """Test that only active sessions can be paused."""
        session = session_manager.create_session(name="Test")
        session_manager.cancel_session(session.id)

        result = session_manager.pause_session(session.id)
        assert result is None

    def test_resume_session(self, session_manager):
        """Test resuming a paused session."""
        session = session_manager.create_session(name="To Resume")
        session_manager.pause_session(session.id)

        resumed = session_manager.resume_session(session.id)

        assert resumed is not None
        assert resumed.status == SessionStatus.ACTIVE
        assert resumed.paused_at is None

    def test_resume_non_paused_session(self, session_manager):
        """Test that only paused sessions can be resumed."""
        session = session_manager.create_session(name="Active")

        result = session_manager.resume_session(session.id)
        assert result is None

    def test_cancel_session(self, session_manager):
        """Test cancelling a session."""
        session = session_manager.create_session(name="To Cancel")

        cancelled = session_manager.cancel_session(session.id)

        assert cancelled is not None
        assert cancelled.status == SessionStatus.CANCELLED
        assert cancelled.completed_at is not None

    def test_cancel_already_completed(self, session_manager):
        """Test cancelling already completed/cancelled session."""
        session = session_manager.create_session(name="Test")
        session_manager.cancel_session(session.id)

        # Cancelling again should return the session as-is
        result = session_manager.cancel_session(session.id)
        assert result.status == SessionStatus.CANCELLED

    def test_add_task(self, session_manager):
        """Test adding a task to a session."""
        session = session_manager.create_session(name="Task Test")

        task = session_manager.add_task(
            session.id,
            description="New Task",
            agent_name="python-developer",
        )

        assert task is not None
        assert task.description == "New Task"
        assert task.agent_name == "python-developer"
        assert task.status == TaskStatus.PENDING

        # Verify task is in session
        updated = session_manager.get_session(session.id)
        assert len(updated.tasks) == 1

    def test_add_task_to_inactive_session(self, session_manager):
        """Test that tasks can't be added to completed/cancelled sessions."""
        session = session_manager.create_session(name="Test")
        session_manager.cancel_session(session.id)

        task = session_manager.add_task(session.id, "New Task")
        assert task is None

    def test_start_task(self, session_manager):
        """Test starting a task."""
        session = session_manager.create_session(
            name="Test",
            tasks=[{"description": "Task 1"}],
        )
        task_id = session.tasks[0].task_id

        started = session_manager.start_task(session.id, task_id)

        assert started is not None
        assert started.status == TaskStatus.IN_PROGRESS
        assert started.started_at is not None

    def test_start_non_pending_task(self, session_manager):
        """Test that only pending tasks can be started."""
        session = session_manager.create_session(
            name="Test",
            tasks=[{"description": "Task 1"}],
        )
        task_id = session.tasks[0].task_id

        # Start the task
        session_manager.start_task(session.id, task_id)

        # Try to start again - should return the task but already in progress
        result = session_manager.start_task(session.id, task_id)
        assert result.status == TaskStatus.IN_PROGRESS

    def test_complete_task_success(self, session_manager):
        """Test completing a task successfully."""
        session = session_manager.create_session(
            name="Test",
            tasks=[{"description": "Task 1"}],
        )
        task_id = session.tasks[0].task_id

        completed = session_manager.complete_task(
            session.id,
            task_id,
            result="Task completed successfully",
            success=True,
        )

        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED
        assert completed.result == "Task completed successfully"
        assert completed.completed_at is not None

    def test_complete_task_failure(self, session_manager):
        """Test completing a task with failure."""
        session = session_manager.create_session(
            name="Test",
            tasks=[{"description": "Task 1"}],
        )
        task_id = session.tasks[0].task_id

        failed = session_manager.complete_task(
            session.id,
            task_id,
            result="Error occurred",
            success=False,
        )

        assert failed is not None
        assert failed.status == TaskStatus.FAILED
        assert failed.error == "Error occurred"

    def test_session_completes_when_all_tasks_done(self, session_manager):
        """Test that session completes when all tasks are done."""
        session = session_manager.create_session(
            name="Test",
            tasks=[
                {"description": "Task 1"},
                {"description": "Task 2"},
            ],
        )

        # Complete both tasks
        session_manager.complete_task(session.id, session.tasks[0].task_id)
        session_manager.complete_task(session.id, session.tasks[1].task_id)

        updated = session_manager.get_session(session.id)
        assert updated.status == SessionStatus.COMPLETED
        assert updated.completed_at is not None

    def test_session_fails_when_any_task_fails(self, session_manager):
        """Test that session fails when any task fails."""
        session = session_manager.create_session(
            name="Test",
            tasks=[
                {"description": "Task 1"},
                {"description": "Task 2"},
            ],
        )

        # Complete one, fail one
        session_manager.complete_task(session.id, session.tasks[0].task_id, success=True)
        session_manager.complete_task(session.id, session.tasks[1].task_id, success=False)

        updated = session_manager.get_session(session.id)
        assert updated.status == SessionStatus.FAILED

    def test_get_next_task(self, session_manager):
        """Test getting the next pending task."""
        session = session_manager.create_session(
            name="Test",
            tasks=[
                {"description": "Task 1"},
                {"description": "Task 2"},
            ],
        )

        next_task = session_manager.get_next_task(session.id)
        assert next_task is not None
        assert next_task.description == "Task 1"

        # Complete first task
        session_manager.complete_task(session.id, session.tasks[0].task_id)

        next_task = session_manager.get_next_task(session.id)
        assert next_task.description == "Task 2"

    def test_get_session_progress(self, session_manager):
        """Test getting session progress."""
        session = session_manager.create_session(
            name="Progress Test",
            tasks=[
                {"description": "Task 1"},
                {"description": "Task 2"},
                {"description": "Task 3"},
            ],
        )

        progress = session_manager.get_session_progress(session.id)

        assert progress["total_tasks"] == 3
        assert progress["pending"] == 3
        assert progress["completed"] == 0
        assert progress["progress"] == 0.0

        # Complete one task
        session_manager.complete_task(session.id, session.tasks[0].task_id)
        progress = session_manager.get_session_progress(session.id)

        assert progress["pending"] == 2
        assert progress["completed"] == 1
        assert progress["progress"] == pytest.approx(0.333, rel=0.01)

    def test_delete_session(self, session_manager):
        """Test deleting a session."""
        session = session_manager.create_session(name="To Delete")
        session_id = session.id

        result = session_manager.delete_session(session_id)
        assert result is True

        # Verify it's gone
        assert session_manager.get_session(session_id) is None

    def test_delete_nonexistent_session(self, session_manager):
        """Test deleting non-existent session."""
        result = session_manager.delete_session("nonexistent")
        assert result is False

    def test_session_persistence(self, memory, topology_manager):
        """Test that sessions persist across manager instances."""
        # Create session with first manager
        mgr1 = SessionManager(memory=memory, topology_manager=topology_manager)
        session = mgr1.create_session(
            name="Persistent",
            tasks=[{"description": "Task 1"}],
        )
        session_id = session.id

        # Create new manager and verify session persists
        mgr2 = SessionManager(memory=memory, topology_manager=topology_manager)
        retrieved = mgr2.get_session(session_id)

        assert retrieved is not None
        assert retrieved.name == "Persistent"
        assert len(retrieved.tasks) == 1


class TestSessionWithTopology:
    """Tests for session creation from swarm topologies."""

    def test_create_session_from_ring_swarm(self, session_manager, topology_manager):
        """Test creating a session from a ring topology swarm."""
        # Create a ring swarm
        swarm = topology_manager.create_swarm(
            name="Pipeline",
            topology=TopologyType.RING,
            agents=["step1", "step2", "step3"],
        )

        session = session_manager.create_session_from_swarm(
            name="Ring Session",
            swarm_id=swarm.id,
            task_description="Process data through pipeline",
        )

        assert session is not None
        assert session.swarm_id == swarm.id
        assert len(session.tasks) == 3
        assert session.tasks[0].agent_name == "step1"
        assert session.tasks[1].agent_name == "step2"
        assert session.tasks[2].agent_name == "step3"

    def test_create_session_from_hierarchical_swarm(self, session_manager, topology_manager):
        """Test creating a session from a hierarchical swarm."""
        swarm = topology_manager.create_swarm(
            name="Delegation",
            topology=TopologyType.HIERARCHICAL,
            agents=["queen", "worker1", "worker2"],
            coordinator="queen",
        )

        session = session_manager.create_session_from_swarm(
            name="Hierarchical Session",
            swarm_id=swarm.id,
            task_description="Coordinate work",
        )

        assert session is not None
        # Hierarchical creates only coordinator task initially
        assert len(session.tasks) == 1
        assert session.tasks[0].agent_name == "queen"

    def test_create_session_from_mesh_swarm(self, session_manager, topology_manager):
        """Test creating a session from a mesh swarm."""
        swarm = topology_manager.create_swarm(
            name="Collaboration",
            topology=TopologyType.MESH,
            agents=["peer1", "peer2", "peer3"],
        )

        session = session_manager.create_session_from_swarm(
            name="Mesh Session",
            swarm_id=swarm.id,
            task_description="Collaborate on task",
        )

        assert session is not None
        assert len(session.tasks) == 3
        agent_names = {t.agent_name for t in session.tasks}
        assert agent_names == {"peer1", "peer2", "peer3"}

    def test_create_session_from_nonexistent_swarm(self, session_manager):
        """Test creating session from non-existent swarm."""
        session = session_manager.create_session_from_swarm(
            name="Test",
            swarm_id="nonexistent",
            task_description="Test",
        )

        assert session is None

    def test_session_without_topology_manager(self, memory):
        """Test that session creation from swarm fails without topology manager."""
        mgr = SessionManager(memory=memory, topology_manager=None)

        session = mgr.create_session_from_swarm(
            name="Test",
            swarm_id="some-id",
            task_description="Test",
        )

        assert session is None


class TestSessionModel:
    """Tests for the Session Pydantic model."""

    def test_progress_empty_session(self):
        """Test progress calculation for empty session."""
        session = Session(id="test", name="Test")
        assert session.progress == 0.0

    def test_progress_with_tasks(self):
        """Test progress calculation with tasks."""
        session = Session(
            id="test",
            name="Test",
            tasks=[
                SessionTask(task_id="t1", description="Task 1", status=TaskStatus.COMPLETED),
                SessionTask(task_id="t2", description="Task 2", status=TaskStatus.COMPLETED),
                SessionTask(task_id="t3", description="Task 3", status=TaskStatus.PENDING),
                SessionTask(task_id="t4", description="Task 4", status=TaskStatus.PENDING),
            ],
        )
        assert session.progress == 0.5

    def test_current_task(self):
        """Test getting current task."""
        session = Session(
            id="test",
            name="Test",
            current_task_index=1,
            tasks=[
                SessionTask(task_id="t1", description="Task 1"),
                SessionTask(task_id="t2", description="Task 2"),
            ],
        )
        assert session.current_task is not None
        assert session.current_task.task_id == "t2"

    def test_current_task_out_of_range(self):
        """Test current task when index is out of range."""
        session = Session(
            id="test",
            name="Test",
            current_task_index=5,
            tasks=[SessionTask(task_id="t1", description="Task 1")],
        )
        assert session.current_task is None

    def test_get_pending_tasks(self):
        """Test filtering pending tasks."""
        session = Session(
            id="test",
            name="Test",
            tasks=[
                SessionTask(task_id="t1", description="Done", status=TaskStatus.COMPLETED),
                SessionTask(task_id="t2", description="Pending 1", status=TaskStatus.PENDING),
                SessionTask(task_id="t3", description="Pending 2", status=TaskStatus.PENDING),
            ],
        )
        pending = session.get_pending_tasks()
        assert len(pending) == 2
        assert all(t.status == TaskStatus.PENDING for t in pending)

    def test_get_completed_tasks(self):
        """Test filtering completed tasks."""
        session = Session(
            id="test",
            name="Test",
            tasks=[
                SessionTask(task_id="t1", description="Done 1", status=TaskStatus.COMPLETED),
                SessionTask(task_id="t2", description="Done 2", status=TaskStatus.COMPLETED),
                SessionTask(task_id="t3", description="Pending", status=TaskStatus.PENDING),
            ],
        )
        completed = session.get_completed_tasks()
        assert len(completed) == 2
        assert all(t.status == TaskStatus.COMPLETED for t in completed)

    def test_get_failed_tasks(self):
        """Test filtering failed tasks."""
        session = Session(
            id="test",
            name="Test",
            tasks=[
                SessionTask(task_id="t1", description="Failed", status=TaskStatus.FAILED),
                SessionTask(task_id="t2", description="Done", status=TaskStatus.COMPLETED),
            ],
        )
        failed = session.get_failed_tasks()
        assert len(failed) == 1
        assert failed[0].status == TaskStatus.FAILED
