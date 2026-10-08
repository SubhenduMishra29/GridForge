# ============================================================
# File: core/network/connectivity.py
# GridForge V2
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model import EndpointReference
from .electrical_boundary import EndpointCompatibility
from .topology_endpoint_reference import TopologyEndpointReference

SIMPLE_WIRE_KIND = "SIMPLE_WIRE"


class ConnectivityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SimpleWireConnection:
    connection_id: str
    endpoint_a: TopologyEndpointReference
    endpoint_b: TopologyEndpointReference
    kind: str = SIMPLE_WIRE_KIND

    def __post_init__(self) -> None:
        if not isinstance(self.connection_id, str) or not self.connection_id.strip():
            raise ValueError("connection_id must be a non-empty string.")
        object.__setattr__(self, "connection_id", self.connection_id.strip())
        object.__setattr__(
            self,
            "endpoint_a",
            _coerce_topology_endpoint(self.endpoint_a),
        )
        object.__setattr__(
            self,
            "endpoint_b",
            _coerce_topology_endpoint(self.endpoint_b),
        )
        if self.kind != SIMPLE_WIRE_KIND:
            raise ValueError(
                f"Simple Wire kind must be {SIMPLE_WIRE_KIND!r}."
            )
        EndpointCompatibility.validate_pair(
            self.endpoint_a.endpoint_reference,
            self.endpoint_b.endpoint_reference,
        )

    @property
    def endpoint_pair_key(self):
        a, b = self.endpoint_a, self.endpoint_b
        return (a, b) if _key(a) <= _key(b) else (b, a)

    @property
    def equipment_ids(self):
        return (
            self.endpoint_a.endpoint_reference.object_id,
            self.endpoint_b.endpoint_reference.object_id,
        )

    def to_dict(self):
        # Keep the terminal-only persisted/read-model shape stable. The
        # topology wrapper is an internal connectivity identity boundary.
        return {
            "connection_id": self.connection_id,
            "kind": self.kind,
            "endpoint_a": dict(self.endpoint_a.to_mapping()),
            "endpoint_b": dict(self.endpoint_b.to_mapping()),
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ConnectivityError(
                "Persisted Simple Wire connection must be an object."
            )
        try:
            endpoint_a = _endpoint_from_mapping(data.get("endpoint_a"))
            endpoint_b = _endpoint_from_mapping(data.get("endpoint_b"))
            connection_id = str(data["connection_id"])
            kind = str(data.get("kind", SIMPLE_WIRE_KIND))
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectivityError(
                "Persisted Simple Wire connection is invalid."
            ) from exc
        return cls(connection_id, endpoint_a, endpoint_b, kind)


def _coerce_topology_endpoint(value: Any) -> TopologyEndpointReference:
    if isinstance(value, TopologyEndpointReference):
        return value
    if isinstance(value, EndpointReference):
        return TopologyEndpointReference.from_terminal(value)
    raise TypeError(
        "Simple Wire endpoints must be TopologyEndpointReference or "
        "terminal EndpointReference values."
    )


def _key(reference: TopologyEndpointReference):
    endpoint = reference.endpoint_reference
    return (
        reference.kind.value,
        endpoint.equipment_type.value if endpoint.equipment_type else "",
        endpoint.object_id,
        endpoint.terminal_role or "",
    )


def _endpoint_from_mapping(data):
    if not isinstance(data, dict):
        raise ConnectivityError(
            "Persisted Simple Wire endpoint must be an object."
        )
    try:
        return TopologyEndpointReference.from_mapping(data)
    except (TypeError, ValueError) as exc:
        raise ConnectivityError(
            "Persisted Simple Wire endpoint is not a supported terminal topology endpoint."
        ) from exc


class ConnectivityStore:
    def __init__(self):
        self._connections = {}
        self._endpoint_index = {}
        self._equipment_index = {}

    @property
    def connections(self):
        return tuple(self._connections.values())

    def add(self, connection, network=None):
        if not isinstance(connection, SimpleWireConnection):
            raise TypeError("connection must be a SimpleWireConnection.")
        EndpointCompatibility.validate_pair(
            connection.endpoint_a.endpoint_reference,
            connection.endpoint_b.endpoint_reference,
            network,
        )
        if connection.connection_id in self._connections:
            raise ConnectivityError(
                f"Simple Wire connection ID already exists: {connection.connection_id}"
            )
        if any(
            x.endpoint_pair_key == connection.endpoint_pair_key
            for x in self._connections.values()
        ):
            raise ConnectivityError("Duplicate Simple Wire relationship.")
        for endpoint in (connection.endpoint_a, connection.endpoint_b):
            if endpoint.is_terminal and self.connections_for_endpoint(endpoint):
                raise ConnectivityError(
                    "Terminal "
                    f"{endpoint.endpoint_reference} already participates "
                    "in a Simple Wire relationship."
                )
        self._connections[connection.connection_id] = connection
        self._index(connection)
        return connection

    def remove(self, connection_id):
        connection = self.get(connection_id)
        del self._connections[connection.connection_id]
        self._deindex(connection)
        return connection

    def get(self, connection_id):
        try:
            return self._connections[connection_id]
        except KeyError as exc:
            raise KeyError(
                f"Simple Wire connection is not registered: {connection_id}"
            ) from exc

    def contains(self, connection_id):
        return connection_id in self._connections

    def connections_for_endpoint(self, endpoint):
        endpoint = _coerce_topology_endpoint(endpoint)
        return tuple(
            self._connections[connection_id]
            for connection_id in sorted(
                self._endpoint_index.get(endpoint, set())
            )
        )

    def connections_for_equipment(self, equipment_id):
        return tuple(
            self._connections[connection_id]
            for connection_id in sorted(
                self._equipment_index.get(equipment_id, set())
            )
        )

    def validate(self, network):
        rebuilt = ConnectivityStore()
        for connection in sorted(
            self._connections.values(),
            key=lambda item: item.connection_id,
        ):
            rebuilt.add(connection, network)
        if tuple(rebuilt._connections) != tuple(sorted(self._connections)):
            raise ConnectivityError("Connectivity indexes are inconsistent.")

    def _index(self, connection):
        for endpoint in (connection.endpoint_a, connection.endpoint_b):
            endpoint_reference = endpoint.endpoint_reference
            self._endpoint_index.setdefault(endpoint, set()).add(
                connection.connection_id
            )
            self._equipment_index.setdefault(
                endpoint_reference.object_id,
                set(),
            ).add(connection.connection_id)

    def _deindex(self, connection):
        for endpoint in (connection.endpoint_a, connection.endpoint_b):
            endpoint_reference = endpoint.endpoint_reference
            ids = self._endpoint_index.get(endpoint)
            if ids is not None:
                ids.discard(connection.connection_id)
                if not ids:
                    self._endpoint_index.pop(endpoint, None)
            ids = self._equipment_index.get(endpoint_reference.object_id)
            if ids is not None:
                ids.discard(connection.connection_id)
                if not ids:
                    self._equipment_index.pop(
                        endpoint_reference.object_id,
                        None,
                    )


@dataclass(frozen=True, slots=True)
class ResolvedConnectivity:
    terminal_adjacency: tuple[
        tuple[EndpointReference, tuple[EndpointReference, ...]],
        ...,
    ]

    def neighbours(self, endpoint):
        for source, targets in self.terminal_adjacency:
            if source == endpoint:
                return targets
        return ()


class ConnectivityResolver:
    def __init__(self, network):
        self._network = network

    def bus_ids_for_terminal(
        self,
        endpoint: EndpointReference,
    ) -> tuple[str, ...]:
        """Resolve the Bus boundaries reached by one terminal through Simple Wire."""
        if not isinstance(endpoint, EndpointReference) or not endpoint.is_terminal:
            raise ConnectivityError(
                "bus_ids_for_terminal requires a terminal EndpointReference."
            )
        component = self.terminal_component(endpoint)
        return tuple(
            sorted(
                {
                    reference.object_id
                    for reference in component
                    if reference.is_bus
                }
            )
        )

    def bus_for_terminal(
        self,
        endpoint: EndpointReference,
    ) -> str | None:
        buses = self.bus_ids_for_terminal(endpoint)
        if len(buses) > 1:
            raise ConnectivityError(
                f"Terminal {endpoint} reaches multiple Bus endpoints: {buses!r}."
            )
        return buses[0] if buses else None

    def resolve(self):
        adjacency = {}
        for connection in sorted(
            self._network.connectivity.connections,
            key=lambda item: item.connection_id,
        ):
            endpoint_a = connection.endpoint_a.endpoint_reference
            endpoint_b = connection.endpoint_b.endpoint_reference
            adjacency.setdefault(endpoint_a, set()).add(endpoint_b)
            adjacency.setdefault(endpoint_b, set()).add(endpoint_a)
        return ResolvedConnectivity(
            tuple(
                (
                    source,
                    tuple(sorted(targets, key=_reference_key)),
                )
                for source, targets in sorted(
                    adjacency.items(),
                    key=lambda item: _reference_key(item[0]),
                )
            )
        )

    def terminal_component(self, endpoint):
        if not isinstance(endpoint, EndpointReference) or not endpoint.is_terminal:
            raise ConnectivityError(
                "terminal_component requires a terminal EndpointReference."
            )
        resolved = self.resolve()
        seen = {endpoint}
        queue = [endpoint]
        while queue:
            current = queue.pop(0)
            for neighbour in resolved.neighbours(current):
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return tuple(sorted(seen, key=_reference_key))


def _reference_key(reference: EndpointReference):
    return (
        reference.kind.value,
        reference.equipment_type.value if reference.equipment_type else "",
        reference.object_id,
        reference.terminal_role or "",
        reference.attachment_id or "",
    )


SimpleWireCompatibility = EndpointCompatibility


__all__ = [
    "ConnectivityError",
    "ConnectivityResolver",
    "ConnectivityStore",
    "ResolvedConnectivity",
    "SIMPLE_WIRE_KIND",
    "SimpleWireCompatibility",
    "SimpleWireConnection",
]
