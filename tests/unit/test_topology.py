"""Tests for swarm topology management."""

import pytest

from orchestrator.topology import TopologyManager
from orchestrator.types import (
    Swarm,
    SwarmMember,
    SwarmRole,
    Task,
    TaskStatus,
    TopologyType,
)


class TestTopologyManager:
    """Tests for TopologyManager class."""

    def test_create_hierarchical_swarm(self):
        """Test creating a hierarchical swarm."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Test Hierarchical",
            topology=TopologyType.HIERARCHICAL,
            agents=["queen-agent", "worker1", "worker2"],
            coordinator="queen-agent",
        )

        assert swarm.name == "Test Hierarchical"
        assert swarm.topology == TopologyType.HIERARCHICAL
        assert len(swarm.members) == 3

        # Check coordinator
        coord = swarm.get_coordinator()
        assert coord is not None
        assert coord.agent_name == "queen-agent"
        assert coord.role == SwarmRole.COORDINATOR
        assert set(coord.can_delegate_to) == {"worker1", "worker2"}

        # Check workers
        workers = swarm.get_workers()
        assert len(workers) == 2
        for w in workers:
            assert w.role == SwarmRole.WORKER
            assert w.reports_to == "queen-agent"
            assert w.can_delegate_to == []

    def test_create_hierarchical_uses_first_agent_as_default_coordinator(self):
        """Test that first agent becomes coordinator if not specified."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Auto Coordinator",
            topology=TopologyType.HIERARCHICAL,
            agents=["agent1", "agent2", "agent3"],
        )

        coord = swarm.get_coordinator()
        assert coord is not None
        assert coord.agent_name == "agent1"

    def test_create_mesh_swarm(self):
        """Test creating a mesh swarm."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Test Mesh",
            topology=TopologyType.MESH,
            agents=["peer1", "peer2", "peer3"],
        )

        assert swarm.topology == TopologyType.MESH
        assert len(swarm.members) == 3

        # No coordinator in mesh
        assert swarm.get_coordinator() is None

        # All peers
        peers = swarm.get_peers()
        assert len(peers) == 3

        # Each peer can delegate to others
        for peer in peers:
            assert peer.role == SwarmRole.PEER
            assert peer.reports_to is None
            others = [p.agent_name for p in peers if p != peer]
            assert set(peer.can_delegate_to) == set(others)

    def test_create_ring_swarm(self):
        """Test creating a ring (pipeline) swarm."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Test Ring",
            topology=TopologyType.RING,
            agents=["step1", "step2", "step3"],
        )

        assert swarm.topology == TopologyType.RING

        # Check ring order
        ring = swarm.get_ring_order()
        assert len(ring) == 3
        assert ring[0].position == 0
        assert ring[1].position == 1
        assert ring[2].position == 2

        # Check delegation chain: step1 -> step2 -> step3 -> step1 (circular)
        assert ring[0].can_delegate_to == ["step2"]
        assert ring[1].can_delegate_to == ["step3"]
        assert ring[2].can_delegate_to == ["step1"]  # Circular

        # Check reports_to (previous in ring)
        assert ring[0].reports_to == "step3"  # Circular
        assert ring[1].reports_to == "step1"
        assert ring[2].reports_to == "step2"

    def test_create_star_swarm(self):
        """Test creating a star (hub-spoke) swarm."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Test Star",
            topology=TopologyType.STAR,
            agents=["hub", "spoke1", "spoke2", "spoke3"],
            coordinator="hub",
        )

        assert swarm.topology == TopologyType.STAR

        # Check hub
        hub = swarm.get_coordinator()
        assert hub is not None
        assert hub.agent_name == "hub"
        assert set(hub.can_delegate_to) == {"spoke1", "spoke2", "spoke3"}

        # Check spokes
        workers = swarm.get_workers()
        assert len(workers) == 3
        for spoke in workers:
            assert spoke.role == SwarmRole.WORKER
            assert spoke.reports_to == "hub"
            assert spoke.can_delegate_to == []

    def test_create_swarm_requires_agents(self):
        """Test that creating a swarm requires at least one agent."""
        mgr = TopologyManager()

        with pytest.raises(ValueError, match="at least one agent"):
            mgr.create_swarm(
                name="Empty",
                topology=TopologyType.MESH,
                agents=[],
            )

    def test_create_swarm_validates_coordinator(self):
        """Test that coordinator must be in agents list."""
        mgr = TopologyManager()

        with pytest.raises(ValueError, match="not in agent list"):
            mgr.create_swarm(
                name="Bad Coordinator",
                topology=TopologyType.HIERARCHICAL,
                agents=["agent1", "agent2"],
                coordinator="not-in-list",
            )

    def test_get_swarm(self):
        """Test retrieving a swarm by ID."""
        mgr = TopologyManager()

        created = mgr.create_swarm(
            name="Test",
            topology=TopologyType.MESH,
            agents=["a", "b"],
        )

        retrieved = mgr.get_swarm(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test"

    def test_get_swarm_not_found(self):
        """Test retrieving non-existent swarm."""
        mgr = TopologyManager()

        assert mgr.get_swarm("nonexistent") is None

    def test_list_swarms(self):
        """Test listing all swarms."""
        mgr = TopologyManager()

        mgr.create_swarm("S1", TopologyType.MESH, ["a"])
        mgr.create_swarm("S2", TopologyType.RING, ["b", "c"])

        swarms = mgr.list_swarms()
        assert len(swarms) == 2

    def test_list_swarms_active_only(self):
        """Test filtering inactive swarms."""
        mgr = TopologyManager()

        s1 = mgr.create_swarm("Active", TopologyType.MESH, ["a"])
        s2 = mgr.create_swarm("Inactive", TopologyType.MESH, ["b"])
        mgr.deactivate_swarm(s2.id)

        active = mgr.list_swarms(active_only=True)
        all_swarms = mgr.list_swarms(active_only=False)

        assert len(active) == 1
        assert active[0].id == s1.id
        assert len(all_swarms) == 2

    def test_delete_swarm(self):
        """Test deleting a swarm."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm("ToDelete", TopologyType.MESH, ["a"])
        swarm_id = swarm.id

        assert mgr.delete_swarm(swarm_id) is True
        assert mgr.get_swarm(swarm_id) is None

        # Deleting again returns False
        assert mgr.delete_swarm(swarm_id) is False

    def test_deactivate_swarm(self):
        """Test deactivating a swarm."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm("ToDeactivate", TopologyType.MESH, ["a"])
        assert swarm.active is True

        mgr.deactivate_swarm(swarm.id)

        # Still exists but inactive
        retrieved = mgr.get_swarm(swarm.id)
        assert retrieved is not None
        assert retrieved.active is False

    def test_get_delegation_target_hierarchical(self):
        """Test delegation in hierarchical topology."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Hierarchical",
            topology=TopologyType.HIERARCHICAL,
            agents=["queen", "worker1", "worker2"],
            coordinator="queen",
        )

        task = Task(id="t1", description="Test task", agent_name="queen")

        # Queen can delegate
        target = mgr.get_delegation_target(swarm.id, "queen", task)
        assert target in ["worker1", "worker2"]

        # Workers cannot delegate
        worker_target = mgr.get_delegation_target(swarm.id, "worker1", task)
        assert worker_target is None

    def test_get_delegation_target_ring(self):
        """Test delegation in ring topology."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Ring",
            topology=TopologyType.RING,
            agents=["step1", "step2", "step3"],
        )

        task = Task(id="t1", description="Test task")

        # Each step delegates to next
        assert mgr.get_delegation_target(swarm.id, "step1", task) == "step2"
        assert mgr.get_delegation_target(swarm.id, "step2", task) == "step3"
        assert mgr.get_delegation_target(swarm.id, "step3", task) == "step1"  # Circular

    def test_get_report_target(self):
        """Test getting report target."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Hierarchical",
            topology=TopologyType.HIERARCHICAL,
            agents=["queen", "worker"],
            coordinator="queen",
        )

        # Worker reports to queen
        assert mgr.get_report_target(swarm.id, "worker") == "queen"

        # Queen reports to no one
        assert mgr.get_report_target(swarm.id, "queen") is None

    def test_create_workflow_tasks_ring(self):
        """Test creating workflow tasks for ring topology."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Pipeline",
            topology=TopologyType.RING,
            agents=["extract", "transform", "load"],
        )

        tasks = mgr.create_workflow_tasks(swarm.id, "Process data")

        assert len(tasks) == 3
        assert tasks[0].agent_name == "extract"
        assert tasks[1].agent_name == "transform"
        assert tasks[2].agent_name == "load"

        # Check task descriptions include step info
        assert "[Ring step 1/3]" in tasks[0].description
        assert "[Ring step 2/3]" in tasks[1].description
        assert "[Ring step 3/3]" in tasks[2].description

    def test_create_workflow_tasks_hierarchical(self):
        """Test creating workflow tasks for hierarchical topology."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Delegation",
            topology=TopologyType.HIERARCHICAL,
            agents=["coordinator", "worker1", "worker2"],
            coordinator="coordinator",
        )

        tasks = mgr.create_workflow_tasks(swarm.id, "Coordinate work")

        # Only coordinator gets initial task
        assert len(tasks) == 1
        assert tasks[0].agent_name == "coordinator"
        assert "[Coordinate]" in tasks[0].description

    def test_create_workflow_tasks_mesh(self):
        """Test creating workflow tasks for mesh topology."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Collaboration",
            topology=TopologyType.MESH,
            agents=["peer1", "peer2", "peer3"],
        )

        tasks = mgr.create_workflow_tasks(swarm.id, "Collaborate on task")

        # All peers get tasks
        assert len(tasks) == 3
        agent_names = [t.agent_name for t in tasks]
        assert set(agent_names) == {"peer1", "peer2", "peer3"}

        # Check collaborative description
        for task in tasks:
            assert "[Collaborate]" in task.description

    def test_get_swarm_status(self):
        """Test getting swarm status."""
        mgr = TopologyManager()

        swarm = mgr.create_swarm(
            name="Status Test",
            topology=TopologyType.STAR,
            agents=["hub", "spoke1", "spoke2"],
            coordinator="hub",
        )

        status = mgr.get_swarm_status(swarm.id)

        assert status["id"] == swarm.id
        assert status["name"] == "Status Test"
        assert status["topology"] == "star"
        assert status["active"] is True
        assert status["member_count"] == 3
        assert status["coordinator"] == "hub"
        assert len(status["members"]) == 3

    def test_get_swarm_status_not_found(self):
        """Test getting status of non-existent swarm."""
        mgr = TopologyManager()

        status = mgr.get_swarm_status("nonexistent")

        assert "error" in status


class TestSwarmModel:
    """Tests for the Swarm Pydantic model."""

    def test_get_coordinator(self):
        """Test getting coordinator from swarm."""
        swarm = Swarm(
            id="test",
            name="Test",
            topology=TopologyType.HIERARCHICAL,
            members=[
                SwarmMember(agent_name="coord", role=SwarmRole.COORDINATOR),
                SwarmMember(agent_name="worker", role=SwarmRole.WORKER),
            ],
        )

        coord = swarm.get_coordinator()
        assert coord is not None
        assert coord.agent_name == "coord"

    def test_get_coordinator_none(self):
        """Test getting coordinator when none exists."""
        swarm = Swarm(
            id="test",
            name="Test",
            topology=TopologyType.MESH,
            members=[
                SwarmMember(agent_name="peer1", role=SwarmRole.PEER),
                SwarmMember(agent_name="peer2", role=SwarmRole.PEER),
            ],
        )

        assert swarm.get_coordinator() is None

    def test_get_workers(self):
        """Test getting workers from swarm."""
        swarm = Swarm(
            id="test",
            name="Test",
            topology=TopologyType.STAR,
            members=[
                SwarmMember(agent_name="hub", role=SwarmRole.COORDINATOR),
                SwarmMember(agent_name="w1", role=SwarmRole.WORKER),
                SwarmMember(agent_name="w2", role=SwarmRole.WORKER),
            ],
        )

        workers = swarm.get_workers()
        assert len(workers) == 2
        assert all(w.role == SwarmRole.WORKER for w in workers)

    def test_get_peers(self):
        """Test getting peers from swarm."""
        swarm = Swarm(
            id="test",
            name="Test",
            topology=TopologyType.MESH,
            members=[
                SwarmMember(agent_name="p1", role=SwarmRole.PEER),
                SwarmMember(agent_name="p2", role=SwarmRole.PEER),
            ],
        )

        peers = swarm.get_peers()
        assert len(peers) == 2

    def test_get_ring_order(self):
        """Test getting ring order by position."""
        swarm = Swarm(
            id="test",
            name="Test",
            topology=TopologyType.RING,
            members=[
                SwarmMember(agent_name="c", role=SwarmRole.PEER, position=2),
                SwarmMember(agent_name="a", role=SwarmRole.PEER, position=0),
                SwarmMember(agent_name="b", role=SwarmRole.PEER, position=1),
            ],
        )

        ordered = swarm.get_ring_order()
        assert [m.agent_name for m in ordered] == ["a", "b", "c"]
