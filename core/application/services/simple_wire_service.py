# ============================================================
# File: core/application/services/simple_wire_service.py
# GridForge V2 — Simple Wire Application Service
# ============================================================

"""Application orchestration for authoritative Simple Wire relationships."""

from __future__ import annotations

from typing import Any

from core.network import SimpleWireConnection
from ..command import Command
from ..commands.simple_wire_commands import CREATE_SIMPLE_WIRE, REMOVE_SIMPLE_WIRE
from ..endpoint_resolver import resolve_terminal_reference
from ..errors import ResourceError, ValidationError
from ..results import ApplicationResult
from ..transaction import Transaction


class SimpleWireConnectionService:
    """Own Simple Wire command orchestration without owning presentation state."""

    COMMAND_TYPES = frozenset({CREATE_SIMPLE_WIRE, REMOVE_SIMPLE_WIRE})

    def supports(self, command: Command) -> bool:
        return command.command_type in self.COMMAND_TYPES

    def execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        if not isinstance(command, Command):
            raise TypeError("command must be a Command.")
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction.")
        if not self.supports(command):
            raise ValueError(f"Unsupported Simple Wire command: {command.command_type}")
        if command.command_type == CREATE_SIMPLE_WIRE:
            return self._create(command, context, transaction)
        return self._remove(command, context, transaction)

    def _network(self, context: Any) -> Any:
        network = getattr(context, "network", None)
        if network is None:
            raise ResourceError(
                code="NETWORK_CONTEXT_MISSING",
                message="Application context does not expose the canonical Core Network.",
                details={},
            )
        return network

    def _create(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        network = self._network(context)
        endpoint_a = command.payload["endpoint_a"]
        endpoint_b = command.payload["endpoint_b"]
        if not getattr(endpoint_a, "is_terminal", False) or not getattr(endpoint_b, "is_terminal", False):
            raise ValidationError(
                code="INVALID_SIMPLE_WIRE_ENDPOINT",
                message="Simple Wire requires two terminal EndpointReferences.",
                details={},
            )

        # Resolve exact terminal ownership without requiring an attached
        # endpoint. The relationship itself establishes connectivity.
        resolve_terminal_reference(context, endpoint_a)
        resolve_terminal_reference(context, endpoint_b)

        connection = SimpleWireConnection(
            connection_id=str(command.payload["connection_id"]),
            endpoint_a=endpoint_a,
            endpoint_b=endpoint_b,
        )
        network.add_simple_wire_connection(connection)
        transaction.record_undo(
            lambda connection_id=connection.connection_id, network=network: network.remove_simple_wire_connection(connection_id)
        )
        return ApplicationResult.success_result(
            value=connection,
            message=f"Simple Wire {connection.connection_id} created.",
            metadata={
                "connection_id": connection.connection_id,
                "endpoint_a": dict(endpoint_a.to_mapping()),
                "endpoint_b": dict(endpoint_b.to_mapping()),
                "connection_kind": connection.kind,
            },
        )

    def _remove(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        network = self._network(context)
        connection_id = str(command.payload["connection_id"])
        connection = network.get_simple_wire_connection(connection_id)
        removed = network.remove_simple_wire_connection(connection_id)
        transaction.record_undo(
            lambda connection=removed, network=network: network.add_simple_wire_connection(connection)
        )
        return ApplicationResult.success_result(
            value=removed,
            message=f"Simple Wire {connection_id} removed.",
            metadata={
                "connection_id": connection_id,
                "endpoint_a": dict(connection.endpoint_a.to_mapping()),
                "endpoint_b": dict(connection.endpoint_b.to_mapping()),
                "connection_kind": connection.kind,
            },
        )


class SimpleWireConnectionCommandHandlers:
    """Bind Simple Wire commands to the canonical Application service."""

    def __init__(self, service: SimpleWireConnectionService | None = None) -> None:
        self._service = service or SimpleWireConnectionService()

    def handlers(self) -> dict[str, Any]:
        return {
            CREATE_SIMPLE_WIRE: self.create,
            REMOVE_SIMPLE_WIRE: self.remove,
        }

    def create(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)

    def remove(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)


__all__ = ["SimpleWireConnectionCommandHandlers", "SimpleWireConnectionService"]
