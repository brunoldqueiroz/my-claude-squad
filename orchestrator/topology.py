"""Swarm topology management for coordinated agent workflows.

Provides four topology patterns inspired by claude-flow:
- Hierarchical: Queen-Worker delegation pattern
- Mesh: Peer-to-peer collaboration
- Ring: Sequential pipeline processing
- Star: Hub-spoke coordination

Each topology defines how agents communicate, delegate, and report results.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from orchestrator.types import (
    Swarm,
    SwarmMember,
    SwarmRole,
    Task,
    TaskStatus,
    TopologyType,
)

logger = logging.getLogger(__name__)


class TopologyManager:
    """Manages swarm topologies and agent coordination patterns.

    Handles:
    - Swarm creation with different topologies
    - Task routing based on topology rules
    - Inter-agent communication patterns
    - Workflow execution within swarms
    """

    def __init__(self, memory: Any | None = None):
        """Initialize the topology manager.

        Args:
            memory: Optional SwarmMemory for persistence
        """
        self._swarms: dict[str, Swarm] = {}
        self._memory = memory

    def create_swarm(
        self,
        name: str,
        topology: TopologyType,
        agents: list[str],
        coordinator: str | None = None,
    ) -> Swarm:
        """Create a new swarm with the specified topology.

        Args:
            name: Human-readable swarm name
            topology: Topology pattern to use
            agents: List of agent names to include
            coordinator: Agent to act as coordinator (required for hierarchical/star)

        Returns:
            Created Swarm instance

        Raises:
            ValueError: If topology requirements not met
        """
        if not agents:
            raise ValueError("Swarm must have at least one agent")

        swarm_id = str(uuid.uuid4())[:8]
        members: list[SwarmMember] = []

        if topology == TopologyType.HIERARCHICAL:
            members = self._create_hierarchical(agents, coordinator)
        elif topology == TopologyType.MESH:
            members = self._create_mesh(agents)
        elif topology == TopologyType.RING:
            members = self._create_ring(agents)
        elif topology == TopologyType.STAR:
            members = self._create_star(agents, coordinator)

        swarm = Swarm(
            id=swarm_id,
            name=name,
            topology=topology,
            members=members,
        )

        self._swarms[swarm_id] = swarm
        logger.info(f"Created {topology.value} swarm '{name}' with {len(members)} agents")

        return swarm

    def _create_hierarchical(
        self, agents: list[str], coordinator: str | None
    ) -> list[SwarmMember]:
        """Create hierarchical (Queen-Worker) topology.

        The coordinator (queen) delegates to all workers and receives reports.
        Workers only communicate with the coordinator.
        """
        if not coordinator:
            coordinator = agents[0]  # First agent becomes coordinator

        if coordinator not in agents:
            raise ValueError(f"Coordinator '{coordinator}' not in agent list")

        members = []
        workers = [a for a in agents if a != coordinator]

        # Create coordinator (queen)
        queen = SwarmMember(
            agent_name=coordinator,
            role=SwarmRole.COORDINATOR,
            can_delegate_to=workers,
            reports_to=None,
        )
        members.append(queen)

        # Create workers
        for worker_name in workers:
            worker = SwarmMember(
                agent_name=worker_name,
                role=SwarmRole.WORKER,
                can_delegate_to=[],  # Workers can't delegate
                reports_to=coordinator,
            )
            members.append(worker)

        return members

    def _create_mesh(self, agents: list[str]) -> list[SwarmMember]:
        """Create mesh (peer-to-peer) topology.

        All agents can communicate with all others.
        No central coordinator - democratic collaboration.
        """
        members = []
        for agent_name in agents:
            others = [a for a in agents if a != agent_name]
            peer = SwarmMember(
                agent_name=agent_name,
                role=SwarmRole.PEER,
                can_delegate_to=others,  # Can delegate to any peer
                reports_to=None,  # No hierarchy
            )
            members.append(peer)

        return members

    def _create_ring(self, agents: list[str]) -> list[SwarmMember]:
        """Create ring (pipeline) topology.

        Sequential processing: A -> B -> C -> ... -> A (circular).
        Each agent passes results to the next in the ring.
        """
        members = []
        n = len(agents)

        for i, agent_name in enumerate(agents):
            next_agent = agents[(i + 1) % n]  # Circular: last -> first
            member = SwarmMember(
                agent_name=agent_name,
                role=SwarmRole.PEER,
                position=i,
                can_delegate_to=[next_agent] if next_agent != agent_name else [],
                reports_to=agents[(i - 1) % n] if n > 1 else None,  # Previous in ring
            )
            members.append(member)

        return members

    def _create_star(
        self, agents: list[str], coordinator: str | None
    ) -> list[SwarmMember]:
        """Create star (hub-spoke) topology.

        Central hub coordinates all spokes.
        Spokes don't communicate with each other.
        Similar to hierarchical but emphasizes the hub as the only communication point.
        """
        if not coordinator:
            coordinator = agents[0]

        if coordinator not in agents:
            raise ValueError(f"Coordinator (hub) '{coordinator}' not in agent list")

        members = []
        spokes = [a for a in agents if a != coordinator]

        # Create hub
        hub = SwarmMember(
            agent_name=coordinator,
            role=SwarmRole.COORDINATOR,
            can_delegate_to=spokes,
            reports_to=None,
        )
        members.append(hub)

        # Create spokes
        for spoke_name in spokes:
            spoke = SwarmMember(
                agent_name=spoke_name,
                role=SwarmRole.WORKER,
                can_delegate_to=[],  # Spokes can only talk to hub
                reports_to=coordinator,
            )
            members.append(spoke)

        return members

    def get_swarm(self, swarm_id: str) -> Swarm | None:
        """Get a swarm by ID."""
        return self._swarms.get(swarm_id)

    def list_swarms(self, active_only: bool = True) -> list[Swarm]:
        """List all swarms.

        Args:
            active_only: If True, only return active swarms

        Returns:
            List of swarms
        """
        swarms = list(self._swarms.values())
        if active_only:
            swarms = [s for s in swarms if s.active]
        return swarms

    def delete_swarm(self, swarm_id: str) -> bool:
        """Delete a swarm.

        Args:
            swarm_id: ID of swarm to delete

        Returns:
            True if deleted, False if not found
        """
        if swarm_id in self._swarms:
            del self._swarms[swarm_id]
            logger.info(f"Deleted swarm {swarm_id}")
            return True
        return False

    def deactivate_swarm(self, swarm_id: str) -> bool:
        """Deactivate a swarm (soft delete).

        Args:
            swarm_id: ID of swarm to deactivate

        Returns:
            True if deactivated, False if not found
        """
        swarm = self._swarms.get(swarm_id)
        if swarm:
            swarm.active = False
            logger.info(f"Deactivated swarm {swarm_id}")
            return True
        return False

    def get_delegation_target(
        self, swarm_id: str, from_agent: str, task: Task
    ) -> str | None:
        """Determine which agent should receive a delegated task.

        Based on topology rules:
        - Hierarchical: Coordinator delegates to workers
        - Mesh: Any peer can delegate to any other
        - Ring: Delegate to next in sequence
        - Star: Hub delegates to appropriate spoke

        Args:
            swarm_id: ID of the swarm
            from_agent: Agent delegating the task
            task: Task being delegated

        Returns:
            Agent name to delegate to, or None if delegation not allowed
        """
        swarm = self._swarms.get(swarm_id)
        if not swarm:
            return None

        # Find the member
        member = next((m for m in swarm.members if m.agent_name == from_agent), None)
        if not member:
            return None

        if not member.can_delegate_to:
            return None

        # For ring topology, always delegate to next in sequence
        if swarm.topology == TopologyType.RING:
            return member.can_delegate_to[0] if member.can_delegate_to else None

        # For other topologies, return the first available delegate
        # (In practice, this could be enhanced with load balancing or task matching)
        return member.can_delegate_to[0] if member.can_delegate_to else None

    def get_report_target(self, swarm_id: str, from_agent: str) -> str | None:
        """Get the agent that should receive results from this agent.

        Args:
            swarm_id: ID of the swarm
            from_agent: Agent that completed a task

        Returns:
            Agent name to report to, or None if no reporting required
        """
        swarm = self._swarms.get(swarm_id)
        if not swarm:
            return None

        member = next((m for m in swarm.members if m.agent_name == from_agent), None)
        return member.reports_to if member else None

    def create_workflow_tasks(
        self, swarm_id: str, task_description: str
    ) -> list[Task]:
        """Create tasks for a swarm workflow based on topology.

        For ring topology: Creates sequential tasks through the pipeline.
        For hierarchical/star: Creates coordinator task that will delegate.
        For mesh: Creates a shared task for collaborative work.

        Args:
            swarm_id: ID of the swarm
            task_description: Description of the overall task

        Returns:
            List of tasks to execute
        """
        swarm = self._swarms.get(swarm_id)
        if not swarm:
            return []

        tasks = []

        if swarm.topology == TopologyType.RING:
            # Create sequential tasks for each member in ring order
            ring_members = swarm.get_ring_order()
            for i, member in enumerate(ring_members):
                task = Task(
                    id=f"{swarm_id}-ring-{i}",
                    description=f"[Ring step {i+1}/{len(ring_members)}] {task_description}",
                    agent_name=member.agent_name,
                    status=TaskStatus.PENDING,
                )
                tasks.append(task)

        elif swarm.topology in (TopologyType.HIERARCHICAL, TopologyType.STAR):
            # Create initial task for coordinator
            coordinator = swarm.get_coordinator()
            if coordinator:
                task = Task(
                    id=f"{swarm_id}-coord",
                    description=f"[Coordinate] {task_description}",
                    agent_name=coordinator.agent_name,
                    status=TaskStatus.PENDING,
                )
                tasks.append(task)

        elif swarm.topology == TopologyType.MESH:
            # Create collaborative task for all peers
            for i, member in enumerate(swarm.get_peers()):
                task = Task(
                    id=f"{swarm_id}-mesh-{i}",
                    description=f"[Collaborate] {task_description}",
                    agent_name=member.agent_name,
                    status=TaskStatus.PENDING,
                )
                tasks.append(task)

        return tasks

    def get_swarm_status(self, swarm_id: str) -> dict[str, Any]:
        """Get detailed status of a swarm.

        Returns:
            Status dictionary with topology info and member states
        """
        swarm = self._swarms.get(swarm_id)
        if not swarm:
            return {"error": f"Swarm {swarm_id} not found"}

        return {
            "id": swarm.id,
            "name": swarm.name,
            "topology": swarm.topology.value,
            "active": swarm.active,
            "created_at": swarm.created_at.isoformat(),
            "member_count": len(swarm.members),
            "members": [
                {
                    "agent": m.agent_name,
                    "role": m.role.value,
                    "position": m.position,
                    "can_delegate_to": m.can_delegate_to,
                    "reports_to": m.reports_to,
                }
                for m in swarm.members
            ],
            "coordinator": (
                swarm.get_coordinator().agent_name if swarm.get_coordinator() else None
            ),
        }
