"""Authoritative phase-domain conductor nodes and explicit return connections.

This Core contract is independent of SLD graphics and sequence networks.
Every neutral, PE, screen, bonding, electrode and earth-return relationship
must be declared as a node/connection. No implicit earth or equipotential
connection is created.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping


class PhaseDomainNodeKind(str, Enum):
    BUS_CONDUCTOR = "BUS_CONDUCTOR"
    BRANCH_TERMINAL = "BRANCH_TERMINAL"
    EQUIPMENT_TERMINAL = "EQUIPMENT_TERMINAL"
    FAULT_NODE = "FAULT_NODE"
    EARTH_NODE = "EARTH_NODE"
    EARTH_REFERENCE = "EARTH_REFERENCE"


class PhaseDomainConnectionKind(str, Enum):
    CONTINUITY = "CONTINUITY"
    BOND = "BOND"
    EQUIPMENT_BOND = "EQUIPMENT_BOND"
    SCREEN_BOND = "SCREEN_BOND"
    GROUND_ELECTRODE = "GROUND_ELECTRODE"
    EARTH_RETURN = "EARTH_RETURN"


def _identity(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _impedance(value: complex) -> complex:
    result = complex(value)
    if not math.isfinite(result.real) or not math.isfinite(result.imag):
        raise ValueError("Connection impedance must be finite.")
    if result.real < 0.0:
        raise ValueError("Connection resistance cannot be negative.")
    return result


@dataclass(frozen=True, slots=True)
class PhaseDomainConductorNode:
    """One electrical node for one explicitly identified physical conductor."""

    node_id: str
    kind: PhaseDomainNodeKind | str
    conductor_role: str
    conductor_id: str | None = None
    equipment_id: str | None = None
    terminal_role: str | None = None
    bus_id: str | None = None
    source_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _identity(self.node_id, "node_id"))
        try:
            kind = self.kind if isinstance(self.kind, PhaseDomainNodeKind) else PhaseDomainNodeKind(str(self.kind).strip().upper())
        except ValueError as exc:
            raise ValueError("Unsupported phase-domain node kind.") from exc
        object.__setattr__(self, "kind", kind)
        role = _identity(self.conductor_role, "conductor_role").upper()
        allowed = {"A", "B", "C", "N", "PE", "SHIELD", "PILOT", "OTHER", "EARTH"}
        if role not in allowed:
            raise ValueError(f"Unsupported physical conductor role {role!r}.")
        if kind in {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}:
            if role != "EARTH" or self.conductor_id is not None:
                raise ValueError("Earth-domain nodes must use role EARTH and no conductor_id.")
            if self.equipment_id is not None or self.terminal_role is not None or self.bus_id is not None:
                raise ValueError("Earth-domain nodes cannot claim equipment terminals or Bus attachments.")
        elif kind is PhaseDomainNodeKind.FAULT_NODE:
            if role != "OTHER" or self.conductor_id is not None:
                raise ValueError("Fault-star nodes must use role OTHER and no physical conductor_id.")
            if self.equipment_id is not None or self.terminal_role is not None or self.bus_id is not None:
                raise ValueError("Fault-star nodes cannot claim equipment terminals or Bus attachments.")
        else:
            if role == "EARTH":
                raise ValueError("EARTH role is reserved for explicit earth-domain nodes.")
            object.__setattr__(self, "conductor_id", _identity(self.conductor_id, "conductor_id"))
        for name in ("equipment_id", "terminal_role", "bus_id", "source_reference"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _identity(value, name))
        if kind in {PhaseDomainNodeKind.BRANCH_TERMINAL, PhaseDomainNodeKind.EQUIPMENT_TERMINAL}:
            if self.equipment_id is None or self.terminal_role is None:
                raise ValueError("Equipment-terminal nodes require equipment_id and terminal_role.")
        if kind is PhaseDomainNodeKind.BUS_CONDUCTOR and self.bus_id is None:
            raise ValueError("Bus-conductor nodes require an explicit bus_id.")


    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "kind": self.kind.value,
            "conductor_role": self.conductor_role,
            "conductor_id": self.conductor_id,
            "equipment_id": self.equipment_id,
            "terminal_role": self.terminal_role,
            "bus_id": self.bus_id,
            "source_reference": self.source_reference,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "PhaseDomainConductorNode":
        if not isinstance(data, Mapping):
            raise TypeError("Persisted phase-domain node must be an object.")
        allowed = {"node_id", "kind", "conductor_role", "conductor_id", "equipment_id", "terminal_role", "bus_id", "source_reference"}
        if set(data) != allowed:
            raise ValueError("Persisted phase-domain node fields are incomplete or unsupported.")
        return cls(**dict(data))


@dataclass(frozen=True, slots=True)
class PhaseDomainConnection:
    """Explicit conductive relationship with physical impedance in ohms."""

    connection_id: str
    kind: PhaseDomainConnectionKind | str
    from_node_id: str
    to_node_id: str
    impedance_ohm: complex
    in_service: bool = True
    source_reference: str | None = None

    def __post_init__(self) -> None:
        for name in ("connection_id", "from_node_id", "to_node_id"):
            object.__setattr__(self, name, _identity(getattr(self, name), name))
        if self.from_node_id == self.to_node_id:
            raise ValueError("A phase-domain connection must join two distinct nodes.")
        try:
            kind = self.kind if isinstance(self.kind, PhaseDomainConnectionKind) else PhaseDomainConnectionKind(str(self.kind).strip().upper())
        except ValueError as exc:
            raise ValueError("Unsupported phase-domain connection kind.") from exc
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "impedance_ohm", _impedance(self.impedance_ohm))
        if type(self.in_service) is not bool:
            raise TypeError("in_service must be bool.")
        if self.source_reference is not None:
            object.__setattr__(self, "source_reference", _identity(self.source_reference, "source_reference"))


    def to_dict(self) -> dict[str, object]:
        return {
            "connection_id": self.connection_id,
            "kind": self.kind.value,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "impedance_ohm": {"real": self.impedance_ohm.real, "imag": self.impedance_ohm.imag},
            "in_service": self.in_service,
            "source_reference": self.source_reference,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "PhaseDomainConnection":
        if not isinstance(data, Mapping):
            raise TypeError("Persisted phase-domain connection must be an object.")
        allowed = {"connection_id", "kind", "from_node_id", "to_node_id", "impedance_ohm", "in_service", "source_reference"}
        if set(data) != allowed:
            raise ValueError("Persisted phase-domain connection fields are incomplete or unsupported.")
        raw = data["impedance_ohm"]
        if not isinstance(raw, Mapping) or set(raw) != {"real", "imag"}:
            raise ValueError("Persisted connection impedance must contain exactly real and imag.")
        values = dict(data)
        values["impedance_ohm"] = complex(float(raw["real"]), float(raw["imag"]))
        return cls(**values)


@dataclass(frozen=True, slots=True)
class PhaseDomainConductorNetwork:
    """Immutable graph snapshot for one activated project's physical conductors."""

    project_id: str
    activation_generation: int
    topology_revision: int
    nodes: tuple[PhaseDomainConductorNode, ...]
    connections: tuple[PhaseDomainConnection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _identity(self.project_id, "project_id"))
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")
        nodes, connections = tuple(self.nodes), tuple(self.connections)
        if any(not isinstance(x, PhaseDomainConductorNode) for x in nodes):
            raise TypeError("nodes must contain PhaseDomainConductorNode records.")
        if any(not isinstance(x, PhaseDomainConnection) for x in connections):
            raise TypeError("connections must contain PhaseDomainConnection records.")
        node_ids = [x.node_id for x in nodes]
        if sum(x.kind is PhaseDomainNodeKind.EARTH_REFERENCE for x in nodes) > 1:
            raise ValueError("A phase-domain graph may declare only one global EARTH_REFERENCE node.")
        connection_ids = [x.connection_id for x in connections]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Phase-domain graph contains duplicate node identities.")
        if len(connection_ids) != len(set(connection_ids)):
            raise ValueError("Phase-domain graph contains duplicate connection identities.")
        by_id = {x.node_id: x for x in nodes}
        for edge in connections:
            if edge.from_node_id not in by_id or edge.to_node_id not in by_id:
                raise ValueError(f"Connection {edge.connection_id!r} references an unknown node.")
            if not edge.in_service:
                continue
            left, right = by_id[edge.from_node_id], by_id[edge.to_node_id]
            if edge.kind is PhaseDomainConnectionKind.GROUND_ELECTRODE:
                if PhaseDomainNodeKind.EARTH_NODE not in {left.kind, right.kind}:
                    raise ValueError("GROUND_ELECTRODE must connect a conductor to an explicit local EARTH_NODE.")
            if edge.kind is PhaseDomainConnectionKind.EARTH_RETURN:
                earth_kinds = {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}
                if left.kind not in earth_kinds or right.kind not in earth_kinds or PhaseDomainNodeKind.EARTH_NODE not in {left.kind, right.kind}:
                    raise ValueError("EARTH_RETURN must connect an explicit local EARTH_NODE to another earth-domain node.")
            if edge.kind is PhaseDomainConnectionKind.SCREEN_BOND:
                if "SHIELD" not in {left.conductor_role, right.conductor_role}:
                    raise ValueError("SCREEN_BOND must include an explicitly identified SHIELD conductor.")
            if edge.kind is PhaseDomainConnectionKind.EQUIPMENT_BOND:
                if "PE" not in {left.conductor_role, right.conductor_role}:
                    raise ValueError("EQUIPMENT_BOND must include an explicitly identified PE conductor.")
        if nodes != tuple(sorted(nodes, key=lambda x: x.node_id)):
            raise ValueError("Phase-domain nodes must use deterministic node_id ordering.")
        if connections != tuple(sorted(connections, key=lambda x: x.connection_id)):
            raise ValueError("Phase-domain connections must use deterministic connection_id ordering.")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "connections", connections)

    @property
    def node_index(self) -> Mapping[str, int]:
        return MappingProxyType({node.node_id: index for index, node in enumerate(self.nodes)})

    def node(self, node_id: str) -> PhaseDomainConductorNode:
        for item in self.nodes:
            if item.node_id == node_id:
                return item
        raise KeyError(node_id)

    def connections_for_node(self, node_id: str) -> tuple[PhaseDomainConnection, ...]:
        self.node(node_id)
        return tuple(x for x in self.connections if x.in_service and node_id in {x.from_node_id, x.to_node_id})

    def earth_reachable(self, node_id: str) -> bool:
        """Return graph reachability to an explicit earth reference; no impedance shortcut."""
        self.node(node_id)
        earth = {x.node_id for x in self.nodes if x.kind is PhaseDomainNodeKind.EARTH_REFERENCE}
        adjacency: dict[str, set[str]] = {x.node_id: set() for x in self.nodes}
        for edge in self.connections:
            if edge.in_service:
                adjacency[edge.from_node_id].add(edge.to_node_id)
                adjacency[edge.to_node_id].add(edge.from_node_id)
        seen, pending = {node_id}, [node_id]
        while pending:
            current = pending.pop()
            if current in earth:
                return True
            for nxt in adjacency[current] - seen:
                seen.add(nxt)
                pending.append(nxt)
        return False


def build_phase_domain_conductor_network(
    *,
    project_id: str,
    activation_generation: int,
    topology_revision: int,
    nodes: Iterable[PhaseDomainConductorNode],
    connections: Iterable[PhaseDomainConnection],
) -> PhaseDomainConductorNetwork:
    """Freeze explicitly configured graph data in deterministic order."""
    return PhaseDomainConductorNetwork(
        project_id=project_id,
        activation_generation=activation_generation,
        topology_revision=topology_revision,
        nodes=tuple(sorted(tuple(nodes), key=lambda x: x.node_id)),
        connections=tuple(sorted(tuple(connections), key=lambda x: x.connection_id)),
    )


__all__ = [
    "PhaseDomainNodeKind",
    "PhaseDomainConnectionKind",
    "PhaseDomainConductorNode",
    "PhaseDomainConnection",
    "PhaseDomainConductorNetwork",
    "build_phase_domain_conductor_network",
]
