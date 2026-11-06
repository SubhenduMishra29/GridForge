"""Immutable Application commands for physical conductor graph mutations."""
from __future__ import annotations

from uuid import UUID, uuid4

from core.network.phase_domain_conductor_network import (
    PhaseDomainConductorNode,
    PhaseDomainConnection,
)
from ..command import Command
from ..reversible import ReversibleCommand

CREATE_PHASE_DOMAIN_NODE = "connectivity.create_phase_domain_node"
REMOVE_PHASE_DOMAIN_NODE = "connectivity.remove_phase_domain_node"
CREATE_PHASE_DOMAIN_CONNECTION = "connectivity.create_phase_domain_connection"
REMOVE_PHASE_DOMAIN_CONNECTION = "connectivity.remove_phase_domain_connection"


class CreatePhaseDomainNodeCommand(ReversibleCommand):
    def __init__(self, *, node: PhaseDomainConductorNode, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(node, PhaseDomainConductorNode):
            raise TypeError("node must be a PhaseDomainConductorNode.")
        super().__init__(command_type=CREATE_PHASE_DOMAIN_NODE, payload={"node": node},
                         command_id=command_id or uuid4(), correlation_id=correlation_id,
                         causation_id=causation_id)

    def inverse(self) -> Command:
        node = self.payload["node"]
        return RemovePhaseDomainNodeCommand(node_id=node.node_id, node=node,
                                             correlation_id=self.correlation_id,
                                             causation_id=self.command_id)


class RemovePhaseDomainNodeCommand(ReversibleCommand):
    def __init__(self, *, node_id: str, node: PhaseDomainConductorNode | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id must be non-empty.")
        if node is not None and (not isinstance(node, PhaseDomainConductorNode) or node.node_id != node_id):
            raise ValueError("node snapshot must match node_id.")
        super().__init__(command_type=REMOVE_PHASE_DOMAIN_NODE,
                         payload={"node_id": node_id.strip(), "node": node},
                         command_id=command_id or uuid4(), correlation_id=correlation_id,
                         causation_id=causation_id)

    def inverse(self) -> Command:
        node = self.payload.get("node")
        if not isinstance(node, PhaseDomainConductorNode):
            raise ValueError("Removing a phase-domain node requires its immutable snapshot for undo.")
        return CreatePhaseDomainNodeCommand(node=node, correlation_id=self.correlation_id,
                                             causation_id=self.command_id)


class CreatePhaseDomainConnectionCommand(ReversibleCommand):
    def __init__(self, *, connection: PhaseDomainConnection, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(connection, PhaseDomainConnection):
            raise TypeError("connection must be a PhaseDomainConnection.")
        super().__init__(command_type=CREATE_PHASE_DOMAIN_CONNECTION,
                         payload={"connection": connection}, command_id=command_id or uuid4(),
                         correlation_id=correlation_id, causation_id=causation_id)

    def inverse(self) -> Command:
        connection = self.payload["connection"]
        return RemovePhaseDomainConnectionCommand(
            connection_id=connection.connection_id, connection=connection,
            correlation_id=self.correlation_id, causation_id=self.command_id,
        )


class RemovePhaseDomainConnectionCommand(ReversibleCommand):
    def __init__(self, *, connection_id: str, connection: PhaseDomainConnection | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(connection_id, str) or not connection_id.strip():
            raise ValueError("connection_id must be non-empty.")
        if connection is not None and (
            not isinstance(connection, PhaseDomainConnection)
            or connection.connection_id != connection_id
        ):
            raise ValueError("connection snapshot must match connection_id.")
        super().__init__(command_type=REMOVE_PHASE_DOMAIN_CONNECTION,
                         payload={"connection_id": connection_id.strip(), "connection": connection},
                         command_id=command_id or uuid4(), correlation_id=correlation_id,
                         causation_id=causation_id)

    def inverse(self) -> Command:
        connection = self.payload.get("connection")
        if not isinstance(connection, PhaseDomainConnection):
            raise ValueError("Removing a phase-domain connection requires its immutable snapshot for undo.")
        return CreatePhaseDomainConnectionCommand(connection=connection,
                                                   correlation_id=self.correlation_id,
                                                   causation_id=self.command_id)


__all__ = [
    "CREATE_PHASE_DOMAIN_NODE", "REMOVE_PHASE_DOMAIN_NODE",
    "CREATE_PHASE_DOMAIN_CONNECTION", "REMOVE_PHASE_DOMAIN_CONNECTION",
    "CreatePhaseDomainNodeCommand", "RemovePhaseDomainNodeCommand",
    "CreatePhaseDomainConnectionCommand", "RemovePhaseDomainConnectionCommand",
]
