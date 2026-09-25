# ============================================================
# File: core/application/commands/simple_wire_commands.py
# GridForge V2 — Simple Wire Application Commands
# ============================================================

"""Immutable commands for authoritative Simple Wire relationships."""

from __future__ import annotations

from uuid import UUID, uuid4

from core.model import EndpointReference
from ..command import Command
from ..reversible import ReversibleCommand


CREATE_SIMPLE_WIRE = "connectivity.create_simple_wire"
REMOVE_SIMPLE_WIRE = "connectivity.remove_simple_wire"


class CreateSimpleWireConnectionCommand(ReversibleCommand):
    """Create one immutable Simple Wire relationship."""

    def __init__(
        self,
        *,
        endpoint_a: EndpointReference,
        endpoint_b: EndpointReference,
        connection_id: str | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(endpoint_a, EndpointReference):
            raise TypeError("endpoint_a must be an EndpointReference.")
        if not isinstance(endpoint_b, EndpointReference):
            raise TypeError("endpoint_b must be an EndpointReference.")
        self._connection_id = connection_id or f"SWC-{uuid4().hex}"
        super().__init__(
            command_type=CREATE_SIMPLE_WIRE,
            payload={
                "connection_id": self._connection_id,
                "endpoint_a": endpoint_a,
                "endpoint_b": endpoint_b,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    @property
    def connection_id(self) -> str:
        return self._connection_id

    def inverse(self) -> Command:
        return RemoveSimpleWireConnectionCommand(
            connection_id=self.connection_id,
            endpoint_a=self.payload["endpoint_a"],
            endpoint_b=self.payload["endpoint_b"],
            correlation_id=self.correlation_id,
            causation_id=self.command_id,
        )


class RemoveSimpleWireConnectionCommand(ReversibleCommand):
    """Remove one Simple Wire relationship while preserving its identity."""

    def __init__(
        self,
        *,
        connection_id: str,
        endpoint_a: EndpointReference | None = None,
        endpoint_b: EndpointReference | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(connection_id, str) or not connection_id.strip():
            raise ValueError("connection_id must be a non-empty string.")
        if endpoint_a is not None and not isinstance(endpoint_a, EndpointReference):
            raise TypeError("endpoint_a must be an EndpointReference or None.")
        if endpoint_b is not None and not isinstance(endpoint_b, EndpointReference):
            raise TypeError("endpoint_b must be an EndpointReference or None.")
        super().__init__(
            command_type=REMOVE_SIMPLE_WIRE,
            payload={
                "connection_id": connection_id.strip(),
                "endpoint_a": endpoint_a,
                "endpoint_b": endpoint_b,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    @property
    def connection_id(self) -> str:
        return str(self.payload["connection_id"])

    def inverse(self) -> Command:
        endpoint_a = self.payload.get("endpoint_a")
        endpoint_b = self.payload.get("endpoint_b")
        if not isinstance(endpoint_a, EndpointReference) or not isinstance(endpoint_b, EndpointReference):
            raise ValueError(
                "A remove command needs endpoint snapshots to construct an inverse create command."
            )
        return CreateSimpleWireConnectionCommand(
            connection_id=self.connection_id,
            endpoint_a=endpoint_a,
            endpoint_b=endpoint_b,
            correlation_id=self.correlation_id,
            causation_id=self.command_id,
        )


__all__ = [
    "CREATE_SIMPLE_WIRE",
    "REMOVE_SIMPLE_WIRE",
    "CreateSimpleWireConnectionCommand",
    "RemoveSimpleWireConnectionCommand",
]
