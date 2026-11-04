"""Switching-aware conductive reachability over canonical Network topology.

This resolver composes committed SimpleWire/Junction connectivity with explicit
internal conductive paths through in-service, conducting two-terminal equipment.
It is a physical reachability view, not a numerical impedance model and not a
universal protection-zone assignment engine.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from core.model import (
    Branch, Breaker, Cable, CurrentTransformer, Disconnector, EndpointReference,
    Fuse, Line, Switch,
)
from .connectivity import ConnectivityResolver, ConnectivityError
from .electrical_boundary import conduction_state
from .topology_endpoint_reference import TopologyEndpointReference


@dataclass(frozen=True, slots=True)
class ConductivePath:
    """Immutable path and the switching equipment that makes it conductive."""

    source: TopologyEndpointReference
    target: TopologyEndpointReference
    endpoints: tuple[TopologyEndpointReference, ...]
    traversed_equipment: tuple[str, ...]
    topology_revision: int

    def __post_init__(self) -> None:
        if not self.endpoints or self.endpoints[0] != self.source or self.endpoints[-1] != self.target:
            raise ValueError("ConductivePath endpoints must include the exact source and target.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")


class ConductiveReachabilityResolver:
    """Resolve live conductive paths, respecting switching and service state.

    Traversable internal paths are deliberately restricted to two-terminal
    series devices: breakers, switches, disconnectors, fuses, CT primaries,
    and two-terminal Branch/Line/Cable conductors. Transformers are excluded:
    their windings transfer power electromagnetically but are not one galvanic
    conductor path. Multiport equipment requires an explicit future path model.
    """

    _CONDUCTIVE_TYPES = (Branch, Breaker, Switch, Disconnector, Fuse, CurrentTransformer, Line, Cable)

    def __init__(self, network: Any) -> None:
        if network is None:
            raise ValueError("network is required.")
        self._network = network

    @staticmethod
    def _terminal_ref(equipment: Any, terminal: Any) -> TopologyEndpointReference:
        from core.model.endpoint_reference import EquipmentType
        raw_type = str(getattr(equipment, "TYPE", getattr(equipment, "element_type", ""))).strip().lower()
        if raw_type == "electrical_object":
            raw_type = type(equipment).__name__.lower()
        try:
            kind = EquipmentType(raw_type)
        except ValueError as exc:
            raise ConnectivityError(
                f"Equipment {getattr(equipment, 'id', None)!r} has no canonical terminal type for conductive reachability."
            ) from exc
        return TopologyEndpointReference.from_terminal(
            EndpointReference.terminal(
                equipment_type=kind,
                equipment_id=equipment.id,
                terminal_role=terminal.role,
            )
        )

    def _equipment(self) -> tuple[Any, ...]:
        """Return canonical equipment collections exposed by Network."""
        names = (
            "buses", "lines", "cables", "branches", "transformers", "breakers",
            "switches", "disconnectors", "fuses", "current_transformers",
            "potential_transformers", "capacitive_voltage_transformers",
            "loads", "generators", "synchronous_machines", "motors", "shunts",
            "capacitors", "reactors", "solar", "batteries", "grids",
        )
        values: dict[str, Any] = {}
        for name in names:
            for item in getattr(self._network, name, ()):
                identity = getattr(item, "id", None)
                if isinstance(identity, str):
                    values[identity] = item
        return tuple(values[key] for key in sorted(values))

    def _adjacency(
        self, excluded_equipment_ids: frozenset[str] = frozenset()
    ) -> dict[TopologyEndpointReference, set[TopologyEndpointReference]]:
        state = self._network.state
        if bool(getattr(state, "topology_dirty", False)) or not bool(getattr(state, "topology_valid", False)):
            raise ConnectivityError(
                "Switching-aware conductive reachability requires a clean, valid committed topology snapshot."
            )
        resolved = ConnectivityResolver(self._network).resolve()
        graph: dict[TopologyEndpointReference, set[TopologyEndpointReference]] = {
            source: set(targets) for source, targets in resolved.topology_adjacency
        }

        # Direct Terminal.attach(Bus) relationships are authoritative physical
        # attachments even when no explicit SimpleWire edge was persisted.
        from core.model import Bus
        from core.model.endpoint_reference import EndpointReference as ER
        for equipment in self._equipment():
            for terminal in getattr(equipment, "terminals", ()):
                if terminal.owner is not equipment or not isinstance(terminal.endpoint, Bus):
                    continue
                source = self._terminal_ref(equipment, terminal)
                bus_ref = TopologyEndpointReference.from_bus(
                    ER.bus(terminal.endpoint.id, "attachment-0")
                )
                graph.setdefault(source, set()).add(bus_ref)
                graph.setdefault(bus_ref, set()).add(source)

        # Add only physically defensible internal series paths. An open or
        # failed device contributes no edge; it cannot be bypassed by topology.
        for equipment in self._equipment():
            if getattr(equipment, "id", None) in excluded_equipment_ids:
                continue
            if not isinstance(equipment, self._CONDUCTIVE_TYPES):
                continue
            terminals = tuple(
                terminal for terminal in getattr(equipment, "terminals", ())
                if terminal.owner is equipment
            )
            if len(terminals) != 2 or not conduction_state(equipment):
                continue
            left, right = (self._terminal_ref(equipment, terminal) for terminal in terminals)
            graph.setdefault(left, set()).add(right)
            graph.setdefault(right, set()).add(left)
        return graph

    def resolve_path(
        self,
        source: EndpointReference | TopologyEndpointReference,
        target: EndpointReference | TopologyEndpointReference,
        *,
        excluded_equipment_ids: frozenset[str] = frozenset(),
    ) -> ConductivePath | None:
        """Return the deterministic shortest live path, or None when isolated.

        Explicitly excluded equipment contributes no internal conductive path;
        its terminal attachment vertices and external SimpleWire paths remain.
        This supports proof that a CT is a boundary rather than traversing it.
        """
        start = self._coerce(source)
        finish = self._coerce(target)
        excluded = frozenset(excluded_equipment_ids)
        if any(not isinstance(item, str) or not item.strip() for item in excluded):
            raise ValueError("excluded_equipment_ids must contain canonical equipment identities.")
        graph = self._adjacency(excluded)
        if start == finish:
            return ConductivePath(start, finish, (start,), (), self._network.state.topology_revision)
        queue = deque([start])
        previous: dict[TopologyEndpointReference, TopologyEndpointReference | None] = {start: None}
        while queue:
            current = queue.popleft()
            for neighbour in sorted(graph.get(current, ()), key=self._key):
                if neighbour in previous:
                    continue
                previous[neighbour] = current
                if neighbour == finish:
                    queue.clear()
                    break
                queue.append(neighbour)
        if finish not in previous:
            return None
        path: list[TopologyEndpointReference] = []
        cursor: TopologyEndpointReference | None = finish
        while cursor is not None:
            path.append(cursor)
            cursor = previous[cursor]
        path.reverse()
        # An equipment identity is traversed only when the path crosses
        # between two of that equipment's terminals. Merely starting or
        # ending at a terminal does not mean its internal path was traversed.
        equipment_ids = tuple(dict.fromkeys(
            left.terminal_reference.object_id
            for left, right in zip(path, path[1:])
            if left.is_terminal
            and right.is_terminal
            and left.terminal_reference.object_id == right.terminal_reference.object_id
        ))
        return ConductivePath(
            start, finish, tuple(path), equipment_ids,
            self._network.state.topology_revision,
        )

    def reachable(
        self,
        source: EndpointReference | TopologyEndpointReference,
        *,
        excluded_equipment_ids: frozenset[str] = frozenset(),
    ) -> tuple[TopologyEndpointReference, ...]:
        """Return all endpoints conductively reachable from source."""
        start = self._coerce(source)
        graph = self._adjacency(frozenset(excluded_equipment_ids))
        seen = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbour in graph.get(current, ()):
                if neighbour not in seen:
                    seen.add(neighbour)
                    queue.append(neighbour)
        return tuple(sorted(seen, key=self._key))

    @staticmethod
    def _coerce(value: EndpointReference | TopologyEndpointReference) -> TopologyEndpointReference:
        if isinstance(value, TopologyEndpointReference):
            return value
        if isinstance(value, EndpointReference) and value.is_terminal:
            return TopologyEndpointReference.from_terminal(value)
        if isinstance(value, EndpointReference) and value.is_bus:
            return TopologyEndpointReference.from_bus(value)
        raise TypeError("Conductive reachability requires a canonical terminal or Bus endpoint.")

    @staticmethod
    def _key(reference: TopologyEndpointReference) -> tuple[str, str, str, str]:
        if reference.is_terminal:
            item = reference.terminal_reference
            return (reference.kind.value, item.equipment_type.value, item.object_id, item.terminal_role)
        if reference.is_bus:
            item = reference.bus_reference
            return (reference.kind.value, "", item.object_id, item.attachment_id or "")
        return (reference.kind.value, "", reference.junction_id or "", "")


__all__ = ["ConductivePath", "ConductiveReachabilityResolver"]
