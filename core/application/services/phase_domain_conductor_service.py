"""Application-owned transactional mutation of the physical conductor graph."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.network.phase_domain_conductor_network import PhaseDomainConductorNode, PhaseDomainConnection
from ..command import Command
from ..errors import ResourceError, ValidationError
from ..results import ApplicationResult
from ..transaction import Transaction
from ..commands.phase_domain_conductor_commands import (
    CREATE_PHASE_DOMAIN_NODE, REMOVE_PHASE_DOMAIN_NODE,
    CREATE_PHASE_DOMAIN_CONNECTION, REMOVE_PHASE_DOMAIN_CONNECTION,
)


class PhaseDomainConductorNetworkService:
    """Own transactional graph mutations; Core remains authoritative for validation."""

    COMMAND_TYPES = frozenset({
        CREATE_PHASE_DOMAIN_NODE, REMOVE_PHASE_DOMAIN_NODE,
        CREATE_PHASE_DOMAIN_CONNECTION, REMOVE_PHASE_DOMAIN_CONNECTION,
    })

    def supports(self, command: Command) -> bool:
        return isinstance(command, Command) and command.command_type in self.COMMAND_TYPES

    @staticmethod
    def _network(context: Any) -> Any:
        network = getattr(context, "network", None)
        if network is None:
            raise ResourceError(
                code="NETWORK_CONTEXT_MISSING",
                message="Application context does not expose the canonical Core Network.",
                details={},
            )
        return network

    def execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        if not isinstance(command, Command):
            raise TypeError("command must be a Command.")
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction.")
        if not self.supports(command):
            raise ValueError(f"Unsupported phase-domain graph command: {command.command_type}.")
        network = self._network(context)
        payload = command.payload

        if command.command_type == CREATE_PHASE_DOMAIN_NODE:
            node = payload.get("node")
            if not isinstance(node, PhaseDomainConductorNode):
                raise ValidationError(code="INVALID_PHASE_DOMAIN_NODE", message="A typed phase-domain node is required.", details={})
            try:
                network.add_phase_domain_node(node)
            except (TypeError, ValueError) as exc:
                raise ValidationError(code="INVALID_PHASE_DOMAIN_NODE", message=str(exc), details={"node_id": node.node_id}) from exc
            transaction.record_undo(lambda node_id=node.node_id, network=network: network.remove_phase_domain_node(node_id))
            return ApplicationResult.success_result(value=node, message=f"Phase-domain node {node.node_id} created.",
                                                    metadata={"node_id": node.node_id, "operation": "create"})

        if command.command_type == REMOVE_PHASE_DOMAIN_NODE:
            node_id = str(payload["node_id"])
            node = next((item for item in network.phase_domain_nodes if item.node_id == node_id), None)
            if node is None:
                raise ResourceError(code="PHASE_DOMAIN_NODE_NOT_FOUND", message=f"Phase-domain node not found: {node_id}", details={"node_id": node_id})
            expected = payload.get("node")
            if expected is not None and expected != node:
                raise ValidationError(code="PHASE_DOMAIN_NODE_SNAPSHOT_MISMATCH", message="Node snapshot does not match the registered node.", details={"node_id": node_id})
            try:
                removed = network.remove_phase_domain_node(node_id)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValidationError(code="PHASE_DOMAIN_NODE_REMOVE_FAILED", message=str(exc), details={"node_id": node_id}) from exc
            transaction.record_undo(lambda node=removed, network=network: network.add_phase_domain_node(node))
            return ApplicationResult.success_result(value=removed, message=f"Phase-domain node {node_id} removed.",
                                                    metadata={"node_id": node_id, "operation": "remove"})

        if command.command_type == CREATE_PHASE_DOMAIN_CONNECTION:
            connection = payload.get("connection")
            if not isinstance(connection, PhaseDomainConnection):
                raise ValidationError(code="INVALID_PHASE_DOMAIN_CONNECTION", message="A typed phase-domain connection is required.", details={})
            try:
                network.add_phase_domain_connection(connection)
            except (TypeError, ValueError) as exc:
                raise ValidationError(code="INVALID_PHASE_DOMAIN_CONNECTION", message=str(exc), details={"connection_id": connection.connection_id}) from exc
            transaction.record_undo(lambda connection_id=connection.connection_id, network=network: network.remove_phase_domain_connection(connection_id))
            return ApplicationResult.success_result(value=connection, message=f"Phase-domain connection {connection.connection_id} created.",
                                                    metadata={"connection_id": connection.connection_id, "operation": "create"})

        connection_id = str(payload["connection_id"])
        connection = next((item for item in network.phase_domain_connections if item.connection_id == connection_id), None)
        if connection is None:
            raise ResourceError(code="PHASE_DOMAIN_CONNECTION_NOT_FOUND", message=f"Phase-domain connection not found: {connection_id}", details={"connection_id": connection_id})
        expected = payload.get("connection")
        if expected is not None and expected != connection:
            raise ValidationError(code="PHASE_DOMAIN_CONNECTION_SNAPSHOT_MISMATCH", message="Connection snapshot does not match the registered connection.", details={"connection_id": connection_id})
        removed = network.remove_phase_domain_connection(connection_id)
        transaction.record_undo(lambda connection=removed, network=network: network.add_phase_domain_connection(connection))
        return ApplicationResult.success_result(value=removed, message=f"Phase-domain connection {connection_id} removed.",
                                                metadata={"connection_id": connection_id, "operation": "remove"})


class PhaseDomainConductorNetworkCommandHandlers:
    def __init__(self, service: PhaseDomainConductorNetworkService | None = None) -> None:
        self._service = service or PhaseDomainConductorNetworkService()

    def handlers(self) -> Mapping[str, Any]:
        return {
            CREATE_PHASE_DOMAIN_NODE: self.execute,
            REMOVE_PHASE_DOMAIN_NODE: self.execute,
            CREATE_PHASE_DOMAIN_CONNECTION: self.execute,
            REMOVE_PHASE_DOMAIN_CONNECTION: self.execute,
        }

    def execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)


__all__ = ["PhaseDomainConductorNetworkService", "PhaseDomainConductorNetworkCommandHandlers"]
