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
from .topology_endpoint_reference import (
    TopologyEndpointReference,
    TopologyEndpointReferenceKind,
)

SIMPLE_WIRE_KIND = "SIMPLE_WIRE"


class ConnectivityError(ValueError):
    """Controlled domain error for invalid Core connectivity operations."""


@dataclass(frozen=True, slots=True)
class SimpleWireConnection:
    connection_id: str
    endpoint_a: TopologyEndpointReference
    endpoint_b: TopologyEndpointReference
    kind: str = SIMPLE_WIRE_KIND

    def __post_init__(self) -> None:
        if not isinstance(self.connection_id, str) or not self.connection_id.strip():
            raise ConnectivityError("connection_id must be a non-empty string.")
        object.__setattr__(self, "connection_id", self.connection_id.strip())
        try:
            endpoint_a = _coerce_topology_endpoint(self.endpoint_a)
            endpoint_b = _coerce_topology_endpoint(self.endpoint_b)
        except (TypeError, ValueError) as exc:
            raise ConnectivityError("Simple Wire endpoints are invalid.") from exc
        object.__setattr__(self, "endpoint_a", endpoint_a)
        object.__setattr__(self, "endpoint_b", endpoint_b)
        if self.kind != SIMPLE_WIRE_KIND:
            raise ConnectivityError(
                f"Simple Wire kind must be {SIMPLE_WIRE_KIND!r}."
            )
        if endpoint_a == endpoint_b:
            raise ConnectivityError("A Simple Wire cannot connect a topology endpoint to itself.")
        _validate_topology_endpoint_shape(endpoint_a)
        _validate_topology_endpoint_shape(endpoint_b)

        # Terminal-to-terminal compatibility remains owned by the existing
        # EndpointCompatibility boundary. Junction endpoints deliberately do
        # not masquerade as EndpointReference values.
        if endpoint_a.is_terminal and endpoint_b.is_terminal:
            EndpointCompatibility.validate_pair(
                endpoint_a.terminal_reference,
                endpoint_b.terminal_reference,
            )

    @property
    def endpoint_pair_key(self) -> tuple[TopologyEndpointReference, TopologyEndpointReference]:
        a, b = self.endpoint_a, self.endpoint_b
        return (a, b) if _key(a) <= _key(b) else (b, a)

    @property
    def equipment_ids(self) -> tuple[str, ...]:
        """Return only actual equipment identities represented by endpoints."""
        return tuple(
            endpoint.terminal_reference.object_id
            for endpoint in (self.endpoint_a, self.endpoint_b)
            if endpoint.is_terminal
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize both endpoint kinds through the canonical discriminator."""
        return {
            "connection_id": self.connection_id,
            "kind": self.kind,
            "endpoint_a": dict(self.endpoint_a.to_mapping()),
            "endpoint_b": dict(self.endpoint_b.to_mapping()),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "SimpleWireConnection":
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
        if not value.is_terminal:
            raise ConnectivityError(
                "Simple Wire EndpointReference values must identify terminals."
            )
        return TopologyEndpointReference.from_terminal(value)
    raise ConnectivityError(
        "Simple Wire endpoints must be TopologyEndpointReference or "
        "terminal EndpointReference values."
    )


def _validate_topology_endpoint_shape(
    reference: TopologyEndpointReference,
) -> None:
    if not isinstance(reference, TopologyEndpointReference):
        raise ConnectivityError("Expected a TopologyEndpointReference.")
    if reference.kind is TopologyEndpointReferenceKind.TERMINAL:
        endpoint = reference.terminal_reference
        if not isinstance(endpoint, EndpointReference) or not endpoint.is_terminal:
            raise ConnectivityError(
                "Terminal topology endpoint does not contain a valid terminal EndpointReference."
            )
        return
    if reference.kind is TopologyEndpointReferenceKind.JUNCTION:
        if not isinstance(reference.junction_id, str) or not reference.junction_id.strip():
            raise ConnectivityError(
                "Junction topology endpoint requires a canonical junction ID."
            )
        return
    raise ConnectivityError(
        f"Unsupported topology endpoint kind: {reference.kind!r}."
    )


def _key(reference: TopologyEndpointReference) -> tuple[str, str, str, str]:
    _validate_topology_endpoint_shape(reference)
    if reference.is_terminal:
        endpoint = reference.terminal_reference
        return (
            reference.kind.value,
            endpoint.equipment_type.value,
            endpoint.object_id,
            endpoint.terminal_role,
        )
    return (
        reference.kind.value,
        "",
        reference.junction_id,
        "",
    )


def _endpoint_from_mapping(data: Any) -> TopologyEndpointReference:
    if not isinstance(data, dict):
        raise ConnectivityError(
            "Persisted Simple Wire endpoint must be an object."
        )
    try:
        return TopologyEndpointReference.from_mapping(data)
    except (TypeError, ValueError) as exc:
        raise ConnectivityError(
            "Persisted Simple Wire endpoint topology identity is invalid."
        ) from exc


class ConnectivityStore:
    """Authoritative deterministic index of binary Simple Wire relationships."""

    def __init__(self):
        self._connections: dict[str, SimpleWireConnection] = {}
        self._endpoint_index: dict[TopologyEndpointReference, set[str]] = {}
        # Equipment indexing is intentionally separate from topology-endpoint
        # indexing. Junction identities never enter this index.
        self._equipment_index: dict[str, set[str]] = {}

    @property
    def connections(self) -> tuple[SimpleWireConnection, ...]:
        return tuple(self._connections.values())

    def add(self, connection: SimpleWireConnection, network: Any | None = None) -> SimpleWireConnection:
        if not isinstance(connection, SimpleWireConnection):
            raise ConnectivityError("connection must be a SimpleWireConnection.")

        endpoint_a = connection.endpoint_a
        endpoint_b = connection.endpoint_b
        _validate_topology_endpoint_shape(endpoint_a)
        _validate_topology_endpoint_shape(endpoint_b)

        if endpoint_a == endpoint_b:
            raise ConnectivityError("A Simple Wire cannot connect a topology endpoint to itself.")

        self._validate_endpoint_membership(endpoint_a, network)
        self._validate_endpoint_membership(endpoint_b, network)

        if endpoint_a.is_terminal and endpoint_b.is_terminal:
            EndpointCompatibility.validate_pair(
                endpoint_a.terminal_reference,
                endpoint_b.terminal_reference,
                network,
            )

        if connection.connection_id in self._connections:
            raise ConnectivityError(
                f"Simple Wire connection ID already exists: {connection.connection_id}"
            )

        if any(
            existing.endpoint_pair_key == connection.endpoint_pair_key
            for existing in self._connections.values()
        ):
            raise ConnectivityError("Duplicate Simple Wire relationship.")

        # Cardinality is a property of the endpoint kind:
        # terminal -> at most one Simple Wire; junction -> N Simple Wires.
        for endpoint in (endpoint_a, endpoint_b):
            if endpoint.is_terminal and self.connections_for_endpoint(endpoint):
                raise ConnectivityError(
                    f"Terminal {endpoint.terminal_reference} already participates "
                    "in a Simple Wire relationship."
                )

        # All validation/index preconditions have succeeded before mutation.
        self._connections[connection.connection_id] = connection
        try:
            self._index(connection)
        except Exception:
            self._connections.pop(connection.connection_id, None)
            raise
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
            raise ConnectivityError(
                f"Simple Wire connection is not registered: {connection_id}"
            ) from exc

    def contains(self, connection_id: str) -> bool:
        return connection_id in self._connections

    def connections_for_endpoint(self, endpoint: Any) -> tuple[SimpleWireConnection, ...]:
        try:
            endpoint = _coerce_topology_endpoint(endpoint)
        except (TypeError, ValueError) as exc:
            raise ConnectivityError("Invalid topology endpoint identity.") from exc
        _validate_topology_endpoint_shape(endpoint)
        return tuple(
            self._connections[connection_id]
            for connection_id in sorted(self._endpoint_index.get(endpoint, set()))
        )

    def connections_for_equipment(self, equipment_id: str) -> tuple[SimpleWireConnection, ...]:
        if not isinstance(equipment_id, str) or not equipment_id.strip():
            raise ConnectivityError("equipment_id must be a non-empty string.")
        return tuple(
            self._connections[connection_id]
            for connection_id in sorted(
                self._equipment_index.get(equipment_id.strip(), set())
            )
        )

    def validate(self, network: Any) -> None:
        rebuilt = ConnectivityStore()
        for connection in sorted(
            self._connections.values(),
            key=lambda item: item.connection_id,
        ):
            rebuilt.add(connection, network)
        if tuple(rebuilt._connections) != tuple(sorted(self._connections)):
            raise ConnectivityError("Connectivity indexes are inconsistent.")
        if rebuilt._endpoint_index != self._endpoint_index:
            raise ConnectivityError("Topology endpoint incidence index is inconsistent.")
        if rebuilt._equipment_index != self._equipment_index:
            raise ConnectivityError("Equipment connectivity index is inconsistent.")

    @staticmethod
    def _validate_endpoint_membership(
        endpoint: TopologyEndpointReference,
        network: Any | None,
    ) -> None:
        if network is None:
            return
        if endpoint.is_terminal:
            EndpointCompatibility.validate_reference(
                endpoint.terminal_reference,
                network,
            )
            return
        junction_id = endpoint.junction_id
        try:
            exists = network.contains_junction(junction_id)
        except (AttributeError, TypeError) as exc:
            raise ConnectivityError(
                "The supplied Network cannot validate Junction topology endpoints."
            ) from exc
        if not exists:
            raise ConnectivityError(
                f"Junction '{junction_id}' is not registered on this Network."
            )
        try:
            junction = network.get_junction(junction_id)
        except (KeyError, TypeError, ValueError) as exc:
            raise ConnectivityError(
                f"Junction '{junction_id}' could not be resolved on this Network."
            ) from exc
        token = getattr(junction, "_gridforge_network_token", None)
        registry = getattr(network, "_junctions", None)
        registry_token = getattr(registry, "_network_token", None)
        if token is not None and registry_token is not None and token is not registry_token:
            raise ConnectivityError(
                f"Junction '{junction_id}' is owned by another Network."
            )

    def _index(self, connection: SimpleWireConnection) -> None:
        for endpoint in (connection.endpoint_a, connection.endpoint_b):
            self._endpoint_index.setdefault(endpoint, set()).add(
                connection.connection_id
            )
            if endpoint.is_terminal:
                self._equipment_index.setdefault(
                    endpoint.terminal_reference.object_id,
                    set(),
                ).add(connection.connection_id)

    def _deindex(self, connection: SimpleWireConnection) -> None:
        for endpoint in (connection.endpoint_a, connection.endpoint_b):
            ids = self._endpoint_index.get(endpoint)
            if ids is not None:
                ids.discard(connection.connection_id)
                if not ids:
                    self._endpoint_index.pop(endpoint, None)
            if endpoint.is_terminal:
                equipment_id = endpoint.terminal_reference.object_id
                ids = self._equipment_index.get(equipment_id)
                if ids is not None:
                    ids.discard(connection.connection_id)
                    if not ids:
                        self._equipment_index.pop(equipment_id, None)


@dataclass(frozen=True, slots=True)
class ResolvedConnectivity:
    """Explicit topology-endpoint graph produced from binary Simple Wires."""

    topology_adjacency: tuple[
        tuple[
            TopologyEndpointReference,
            tuple[TopologyEndpointReference, ...],
        ],
        ...,
    ]

    def neighbours(
        self,
        endpoint: TopologyEndpointReference,
    ) -> tuple[TopologyEndpointReference, ...]:
        for source, targets in self.topology_adjacency:
            if source == endpoint:
                return targets
        return ()

    @property
    def terminal_adjacency(
        self,
    ) -> tuple[tuple[EndpointReference, tuple[EndpointReference, ...]], ...]:
        """Compatibility view containing only terminal-to-terminal graph edges."""
        return tuple(
            (
                source.terminal_reference,
                tuple(
                    target.terminal_reference
                    for target in targets
                    if source.is_terminal and target.is_terminal
                ),
            )
            for source, targets in self.topology_adjacency
            if source.is_terminal
        )


class ConnectivityResolver:
    """Resolve the explicit Core topology graph without assigning Junction semantics."""

    def __init__(self, network: Any):
        self._network = network

    def bus_ids_for_terminal(
        self,
        endpoint: EndpointReference | TopologyEndpointReference,
    ) -> tuple[str, ...]:
        """Resolve Bus identities reached by a terminal through Simple Wire/Junction paths.

        Junctions are graph nodes only. No Bus identity is fabricated for a Junction.
        """
        terminal = self._terminal_reference(endpoint)
        component = self.terminal_component(terminal)
        bus_ids: set[str] = set()

        # Physical Bus attachments remain the existing electrical boundary.
        for reference in component:
            if not reference.is_terminal:
                continue
            equipment = self._network.get_by_identity(reference.object_id)
            for terminal_obj in getattr(equipment, "terminals", ()):
                if terminal_obj.owner is equipment and terminal_obj.role == reference.terminal_role:
                    attached = getattr(terminal_obj, "endpoint", None)
                    if attached is not None and attached in self._network.buses:
                        bus_ids.add(str(attached.id))
                    break

        return tuple(sorted(bus_ids))

    def bus_for_terminal(
        self,
        endpoint: EndpointReference | TopologyEndpointReference,
    ) -> str | None:
        buses = self.bus_ids_for_terminal(endpoint)
        if len(buses) > 1:
            raise ConnectivityError(
                f"Terminal {self._terminal_reference(endpoint)} reaches multiple Bus endpoints: {buses!r}."
            )
        return buses[0] if buses else None

    def resolve(self) -> ResolvedConnectivity:
        adjacency: dict[
            TopologyEndpointReference,
            set[TopologyEndpointReference],
        ] = {}
        for connection in sorted(
            self._network.connectivity.connections,
            key=lambda item: item.connection_id,
        ):
            endpoint_a = connection.endpoint_a
            endpoint_b = connection.endpoint_b
            _validate_topology_endpoint_shape(endpoint_a)
            _validate_topology_endpoint_shape(endpoint_b)
            adjacency.setdefault(endpoint_a, set()).add(endpoint_b)
            adjacency.setdefault(endpoint_b, set()).add(endpoint_a)

        return ResolvedConnectivity(
            tuple(
                (
                    source,
                    tuple(sorted(targets, key=_topology_reference_key)),
                )
                for source, targets in sorted(
                    adjacency.items(),
                    key=lambda item: _topology_reference_key(item[0]),
                )
            )
        )

    def components(self) -> tuple[tuple[TopologyEndpointReference, ...], ...]:
        """Return all deterministic connected components of the endpoint graph."""
        resolved=self.resolve()
        remaining={source for source,_ in resolved.topology_adjacency}
        components=[]
        while remaining:
            start=min(remaining,key=_topology_reference_key)
            seen={start}
            queue=[start]
            while queue:
                current=queue.pop(0)
                for neighbour in resolved.neighbours(current):
                    if neighbour not in seen:
                        seen.add(neighbour)
                        queue.append(neighbour)
            remaining-=seen
            components.append(tuple(sorted(seen,key=_topology_reference_key)))
        return tuple(components)

    def topology_component(
        self,
        endpoint: TopologyEndpointReference,
    ) -> tuple[TopologyEndpointReference, ...]:
        _validate_topology_endpoint_shape(endpoint)
        resolved = self.resolve()
        seen = {endpoint}
        queue = [endpoint]
        while queue:
            current = queue.pop(0)
            for neighbour in resolved.neighbours(current):
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return tuple(sorted(seen, key=_topology_reference_key))

    def terminal_component(
        self,
        endpoint: EndpointReference | TopologyEndpointReference,
    ) -> tuple[EndpointReference, ...]:
        terminal = self._terminal_reference(endpoint)
        return tuple(
            reference.terminal_reference
            for reference in self.topology_component(
                TopologyEndpointReference.from_terminal(terminal)
            )
            if reference.is_terminal
        )

    @staticmethod
    def _terminal_reference(
        endpoint: EndpointReference | TopologyEndpointReference,
    ) -> EndpointReference:
        if isinstance(endpoint, TopologyEndpointReference):
            if not endpoint.is_terminal:
                raise ConnectivityError(
                    "Terminal connectivity resolution requires a terminal topology endpoint."
                )
            endpoint = endpoint.terminal_reference
        if not isinstance(endpoint, EndpointReference) or not endpoint.is_terminal:
            raise ConnectivityError(
                "Connectivity resolution requires a terminal EndpointReference."
            )
        return endpoint


def _topology_reference_key(
    reference: TopologyEndpointReference,
) -> tuple[str, str, str, str]:
    _validate_topology_endpoint_shape(reference)
    if reference.is_terminal:
        endpoint = reference.terminal_reference
        return (
            reference.kind.value,
            endpoint.equipment_type.value if endpoint.equipment_type else "",
            endpoint.object_id,
            endpoint.terminal_role or "",
        )
    return (
        reference.kind.value,
        "",
        reference.junction_id,
        "",
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
