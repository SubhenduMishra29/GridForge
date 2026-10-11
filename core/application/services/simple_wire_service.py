# ============================================================
# File: core/application/services/simple_wire_service.py
# GridForge V2 — Simple Wire Application Service
# ============================================================

"""Application orchestration for authoritative Simple Wire relationships."""

from __future__ import annotations

from typing import Any

from core.model import EndpointReference
from core.network import (
    ConnectivityError,
    EndpointCompatibility,
    EndpointCompatibilityError,
    SimpleWireConnection,
    TopologyEndpointReference,
    TopologyEndpointReferenceKind,
)
from ..command import Command
from ..commands.simple_wire_commands import CREATE_SIMPLE_WIRE, REMOVE_SIMPLE_WIRE, CreateSimpleWireConnectionCommand
from ..endpoint_resolver import resolve_terminal_reference
from ..errors import ResourceError, ValidationError
from ..results import ApplicationResult
from ..transaction import Transaction


class SimpleWireConnectionService:
    """Own Simple Wire command orchestration without owning presentation state."""

    COMMAND_TYPES = frozenset({CREATE_SIMPLE_WIRE, REMOVE_SIMPLE_WIRE})

    def supports(self, command: Command) -> bool:
        return command.command_type in self.COMMAND_TYPES

    def create_command(
        self,
        *,
        connection_id: str,
        source: EndpointReference | TopologyEndpointReference,
        target: EndpointReference | TopologyEndpointReference,
    ) -> Command:
        """Prepare an immutable Simple Wire command without mutating Core."""
        if not isinstance(connection_id, str) or not connection_id.strip():
            raise ValueError("connection_id must be a non-empty string.")
        if not isinstance(source, (EndpointReference, TopologyEndpointReference)) or not isinstance(
            target, (EndpointReference, TopologyEndpointReference)
        ):
            raise ValidationError(
                code="INVALID_SIMPLE_WIRE_ENDPOINT",
                message="Simple Wire endpoints must be topology endpoint references.",
                details={},
            )
        if source == target:
            raise ValidationError(
                code="INVALID_SIMPLE_WIRE_ENDPOINTS",
                message="Simple Wire endpoints must be distinct.",
                details={},
            )
        return CreateSimpleWireConnectionCommand(
            connection_id=connection_id.strip(),
            endpoint_a=source,
            endpoint_b=target,
        )

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
        if not isinstance(endpoint_a, TopologyEndpointReference) or not isinstance(endpoint_b, TopologyEndpointReference):
            raise ValidationError(
                code="INVALID_SIMPLE_WIRE_ENDPOINT",
                message="Simple Wire requires topology endpoint references.",
                details={},
            )

        for endpoint in (endpoint_a, endpoint_b):
            if endpoint.kind is TopologyEndpointReferenceKind.TERMINAL:
                try:
                    EndpointCompatibility.validate_reference(
                        endpoint.terminal_reference,
                        network,
                    )
                    resolve_terminal_reference(context, endpoint.terminal_reference)
                except (EndpointCompatibilityError, ResourceError, ValidationError) as exc:
                    if isinstance(exc, ValidationError):
                        raise
                    raise ValidationError(
                        code="INVALID_SIMPLE_WIRE_ENDPOINT",
                        message=str(exc),
                        details={"endpoint": str(endpoint)},
                    ) from exc
                continue

            if endpoint.kind is TopologyEndpointReferenceKind.JUNCTION:
                junction_id = endpoint.junction_id
                try:
                    junction = network.get_junction(junction_id)
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValidationError(
                        code="JUNCTION_NOT_FOUND",
                        message=f"Junction '{junction_id}' is not registered on this Network.",
                        details={"junction_id": junction_id},
                    ) from exc
                registry = getattr(network, "_junctions", None)
                if registry is None or getattr(
                    junction,
                    "_gridforge_network_token",
                    None,
                ) is not getattr(registry, "_network_token", None):
                    raise ValidationError(
                        code="JUNCTION_WRONG_NETWORK",
                        message=f"Junction '{junction_id}' is not owned by this Network.",
                        details={"junction_id": junction_id},
                    )
                continue

            raise ValidationError(
                code="UNSUPPORTED_TOPOLOGY_ENDPOINT",
                message=f"Unsupported topology endpoint kind: {endpoint.kind.value!r}.",
                details={},
            )

        if endpoint_a.is_terminal and endpoint_b.is_terminal:
            try:
                EndpointCompatibility.validate_pair(
                    endpoint_a.terminal_reference,
                    endpoint_b.terminal_reference,
                    network,
                )
            except EndpointCompatibilityError as exc:
                raise ValidationError(
                    code="INVALID_SIMPLE_WIRE_ENDPOINT",
                    message=str(exc),
                    details={},
                ) from exc

        connection = SimpleWireConnection(
            connection_id=str(command.payload["connection_id"]),
            endpoint_a=endpoint_a,
            endpoint_b=endpoint_b,
        )
        try:
            network.add_simple_wire_connection(connection)
        except ConnectivityError as exc:
            raise ValidationError(
                code="INVALID_SIMPLE_WIRE_CONNECTION",
                message=str(exc),
                details={
                    "connection_id": connection.connection_id,
                    "endpoint_a": dict(endpoint_a.to_mapping()),
                    "endpoint_b": dict(endpoint_b.to_mapping()),
                },
            ) from exc
        transaction.record_undo(
            lambda connection_id=connection.connection_id, network=network: network.remove_simple_wire_connection(connection_id)
        )
        return ApplicationResult.success_result(
            value=None,
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
            value=None,
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
