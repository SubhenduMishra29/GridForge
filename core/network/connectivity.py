# ============================================================
# File: core/network/connectivity.py
# GridForge V2 — Authoritative Simple Wired Connectivity
# ============================================================

"""Authoritative persistent terminal-to-terminal Simple Wire relationships."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from core.model import EndpointReference, EndpointReferenceKind


SIMPLE_WIRE_KIND = "SIMPLE_WIRE"


class ConnectivityError(ValueError):
    """Raised when authoritative relationship validation fails."""


@dataclass(frozen=True, slots=True)
class SimpleWireConnection:
    """Immutable engineering relationship between two Core terminals.

    SimpleWireConnection is deliberately not an ElectricalObject and therefore
    is not registered in NetworkRegistry. It has no electrical parameters.
    """

    connection_id: str
    endpoint_a: EndpointReference
    endpoint_b: EndpointReference
    kind: str = SIMPLE_WIRE_KIND

    def __post_init__(self) -> None:
        if not isinstance(self.connection_id, str) or not self.connection_id.strip():
            raise ValueError("connection_id must be a non-empty string.")
        object.__setattr__(self, "connection_id", self.connection_id.strip())
        if not isinstance(self.endpoint_a, EndpointReference) or not self.endpoint_a.is_terminal:
            raise TypeError("endpoint_a must be a terminal EndpointReference.")
        if not isinstance(self.endpoint_b, EndpointReference) or not self.endpoint_b.is_terminal:
            raise TypeError("endpoint_b must be a terminal EndpointReference.")
        if not isinstance(self.kind, str) or self.kind != SIMPLE_WIRE_KIND:
            raise ValueError(f"Simple Wire kind must be {SIMPLE_WIRE_KIND!r}.")
        if self.endpoint_a == self.endpoint_b:
            raise ConnectivityError("A Simple Wire cannot connect a terminal to itself.")

    @property
    def endpoint_pair_key(self) -> tuple[EndpointReference, EndpointReference]:
        """Return a deterministic unordered endpoint pair for duplicate detection."""
        left, right = self.endpoint_a, self.endpoint_b
        return (left, right) if _endpoint_sort_key(left) <= _endpoint_sort_key(right) else (right, left)

    @property
    def equipment_ids(self) -> tuple[str, str]:
        return self.endpoint_a.object_id, self.endpoint_b.object_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "kind": self.kind,
            "endpoint_a": dict(self.endpoint_a.to_mapping()),
            "endpoint_b": dict(self.endpoint_b.to_mapping()),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimpleWireConnection":
        if not isinstance(data, dict):
            raise TypeError("Simple Wire persistence entry must be an object.")
        return cls(
            connection_id=str(data["connection_id"]),
            kind=str(data.get("kind", SIMPLE_WIRE_KIND)),
            endpoint_a=_endpoint_from_mapping(data.get("endpoint_a")),
            endpoint_b=_endpoint_from_mapping(data.get("endpoint_b")),
        )


def _endpoint_sort_key(reference: EndpointReference) -> tuple[str, str, str, str]:
    return (
        reference.kind.value,
        reference.equipment_type.value if reference.equipment_type is not None else "",
        reference.object_id,
        reference.terminal_role or "",
    )


def _endpoint_from_mapping(data: Any) -> EndpointReference:
    if not isinstance(data, dict):
        raise ConnectivityError("Persisted Simple Wire endpoint must be an object.")
    if data.get("kind") != EndpointReferenceKind.TERMINAL.value:
        raise ConnectivityError("Simple Wire endpoints must be terminal references.")
    from core.model import EquipmentType

    equipment_type = data.get("equipment_type")
    role = data.get("terminal_role")
    object_id = data.get("object_id")
    if not isinstance(equipment_type, str) or not equipment_type.strip():
        raise ConnectivityError("Simple Wire endpoint equipment_type is required.")
    try:
        equipment_enum = EquipmentType(equipment_type.strip().lower())
    except ValueError as exc:
        raise ConnectivityError(f"Unknown terminal equipment type: {equipment_type!r}.") from exc
    if not isinstance(object_id, str) or not object_id.strip():
        raise ConnectivityError("Simple Wire endpoint object_id is required.")
    if not isinstance(role, str) or not role.strip():
        raise ConnectivityError("Simple Wire endpoint terminal_role is required.")
    return EndpointReference.terminal(
        equipment_type=equipment_enum,
        equipment_id=object_id,
        terminal_role=role,
    )


class SimpleWireCompatibility:
    """Authoritative terminal compatibility/cardinality contract."""

    _DOMAIN_ROLES = {
        "current_transformer": {
            "P1": "primary", "P2": "primary", "S1": "secondary", "S2": "secondary",
        },
        "potential_transformer": {
            "primary_a": "primary", "primary_b": "primary",
            "secondary_a": "secondary", "secondary_b": "secondary",
        },
        "capacitive_voltage_transformer": {
            "H1": "primary", "H2": "primary", "X1": "secondary", "X2": "secondary",
        },
    }

    @classmethod
    def validate(cls, first: EndpointReference, second: EndpointReference, store: "ConnectivityStore") -> None:
        if not first.is_terminal or not second.is_terminal:
            raise ConnectivityError("Simple Wire endpoints must both identify terminals.")
        if first == second:
            raise ConnectivityError("A Simple Wire cannot connect a terminal to itself.")

        first_domain = cls.domain(first)
        second_domain = cls.domain(second)
        if first_domain != second_domain:
            raise ConnectivityError(
                "Terminal compatibility violation: endpoints belong to different electrical domains."
            )

        if first.equipment_type == second.equipment_type and first.object_id == second.object_id:
            if first_domain != "generic":
                raise ConnectivityError("A Simple Wire cannot bridge two domains of the same instrument.")
            raise ConnectivityError("A Simple Wire cannot connect two terminals on the same equipment.")

        # Bus terminals may fan out. Non-bus terminal references are one-to-one
        # relationship endpoints in the authoritative Simple Wire store.
        for endpoint in (first, second):
            if endpoint.equipment_type is None:
                continue
            if endpoint.equipment_type.value != "bus":
                existing = store.connections_for_endpoint(endpoint)
                if existing:
                    raise ConnectivityError(
                        f"Terminal {endpoint} already participates in a Simple Wire relationship."
                    )

    @classmethod
    def domain(cls, reference: EndpointReference) -> str:
        if reference.equipment_type is None:
            return "generic"
        return cls._DOMAIN_ROLES.get(reference.equipment_type.value, {}).get(
            reference.terminal_role or "", "generic"
        )


class ConnectivityStore:
    """Single authoritative relationship collection owned by Network."""

    def __init__(self) -> None:
        self._connections: dict[str, SimpleWireConnection] = {}
        self._endpoint_index: dict[EndpointReference, set[str]] = {}
        self._equipment_index: dict[str, set[str]] = {}

    @property
    def connections(self) -> tuple[SimpleWireConnection, ...]:
        return tuple(self._connections.values())

    def add(self, connection: SimpleWireConnection) -> SimpleWireConnection:
        if not isinstance(connection, SimpleWireConnection):
            raise TypeError("connection must be a SimpleWireConnection.")
        if connection.connection_id in self._connections:
            raise ConnectivityError(
                f"Simple Wire connection ID already exists: {connection.connection_id}"
            )
        for existing in self._connections.values():
            if existing.endpoint_pair_key == connection.endpoint_pair_key:
                raise ConnectivityError("Duplicate Simple Wire relationship (including reversed endpoints).")
        SimpleWireCompatibility.validate(connection.endpoint_a, connection.endpoint_b, self)
        self._connections[connection.connection_id] = connection
        self._index(connection)
        return connection

    def remove(self, connection_id: str) -> SimpleWireConnection:
        connection = self.get(connection_id)
        del self._connections[connection.connection_id]
        self._deindex(connection)
        return connection

    def get(self, connection_id: str) -> SimpleWireConnection:
        try:
            return self._connections[connection_id]
        except KeyError as exc:
            raise KeyError(f"Simple Wire connection is not registered: {connection_id}") from exc

    def contains(self, connection_id: str) -> bool:
        return connection_id in self._connections

    def connections_for_endpoint(self, endpoint: EndpointReference) -> tuple[SimpleWireConnection, ...]:
        ids = self._endpoint_index.get(endpoint, set())
        return tuple(self._connections[item] for item in sorted(ids))

    def connections_for_equipment(self, equipment_id: str) -> tuple[SimpleWireConnection, ...]:
        ids = self._equipment_index.get(equipment_id, set())
        return tuple(self._connections[item] for item in sorted(ids))

    def validate(self, network: Any) -> None:
        if network is None:
            raise TypeError("network is required for connectivity validation.")
        for connection in self._connections.values():
            for endpoint in (connection.endpoint_a, connection.endpoint_b):
                equipment = network.get_by_identity(endpoint.object_id)
                expected = endpoint.equipment_type.value if endpoint.equipment_type else None
                actual = str(getattr(equipment, "element_type", "")).strip().lower()
                if expected != actual:
                    raise ConnectivityError(
                        f"Simple Wire {connection.connection_id} endpoint {endpoint} "
                        f"does not resolve to the declared equipment type."
                    )
                matches = [
                    terminal for terminal in getattr(equipment, "terminals", ())
                    if terminal.owner is equipment and terminal.role == endpoint.terminal_role
                ]
                if len(matches) != 1:
                    raise ConnectivityError(
                        f"Simple Wire {connection.connection_id} endpoint {endpoint} does not resolve to exactly one terminal."
                    )
        # Rebuild duplicate/cardinality invariants from authoritative data.
        rebuilt = ConnectivityStore()
        for connection in self._connections.values():
            rebuilt.add(connection)
        if tuple(rebuilt._connections) != tuple(self._connections):
            raise ConnectivityError("Connectivity indexes are inconsistent with authoritative relationships.")

    def _index(self, connection: SimpleWireConnection) -> None:
        for endpoint in (connection.endpoint_a, connection.endpoint_b):
            self._endpoint_index.setdefault(endpoint, set()).add(connection.connection_id)
            self._equipment_index.setdefault(endpoint.object_id, set()).add(connection.connection_id)

    def _deindex(self, connection: SimpleWireConnection) -> None:
        for endpoint in (connection.endpoint_a, connection.endpoint_b):
            ids = self._endpoint_index.get(endpoint)
            if ids is not None:
                ids.discard(connection.connection_id)
                if not ids:
                    self._endpoint_index.pop(endpoint, None)
            equipment_ids = self._equipment_index.get(endpoint.object_id)
            if equipment_ids is not None:
                equipment_ids.discard(connection.connection_id)
                if not equipment_ids:
                    self._equipment_index.pop(endpoint.object_id, None)


@dataclass(frozen=True, slots=True)
class ResolvedConnectivity:
    """Immutable normalized terminal adjacency consumed by TopologyManager."""

    terminal_adjacency: tuple[tuple[EndpointReference, tuple[EndpointReference, ...]], ...]

    def neighbours(self, endpoint: EndpointReference) -> tuple[EndpointReference, ...]:
        for source, targets in self.terminal_adjacency:
            if source == endpoint:
                return targets
        return ()


class ConnectivityResolver:
    """Normalize chained Simple Wires into deterministic terminal adjacency."""

    def __init__(self, network: Any) -> None:
        self._network = network

    def resolve(self) -> ResolvedConnectivity:
        adjacency: dict[EndpointReference, set[EndpointReference]] = {}
        for connection in self._network.connectivity.connections:
            adjacency.setdefault(connection.endpoint_a, set()).add(connection.endpoint_b)
            adjacency.setdefault(connection.endpoint_b, set()).add(connection.endpoint_a)

        # Traversal is iterative and cycle-safe. The normalized graph preserves
        # terminal boundaries; it never crosses from one equipment terminal to
        # another. Equipment conduction remains a TopologyManager concern.
        normalized: dict[EndpointReference, tuple[EndpointReference, ...]] = {}
        for source in sorted(adjacency, key=_endpoint_sort_key):
            normalized[source] = tuple(
                sorted(adjacency[source], key=_endpoint_sort_key)
            )

        return ResolvedConnectivity(
            terminal_adjacency=tuple(normalized.items())
        )

    def terminal_component(self, endpoint: EndpointReference) -> tuple[EndpointReference, ...]:
        resolved = self.resolve()
        seen = {endpoint}
        queue = [endpoint]
        while queue:
            current = queue.pop(0)
            for neighbour in resolved.neighbours(current):
                if neighbour in seen:
                    continue
                seen.add(neighbour)
                queue.append(neighbour)
        return tuple(sorted(seen, key=_endpoint_sort_key))


__all__ = [
    "ConnectivityError",
    "ConnectivityResolver",
    "ConnectivityStore",
    "ResolvedConnectivity",
    "SIMPLE_WIRE_KIND",
    "SimpleWireCompatibility",
    "SimpleWireConnection",
]
