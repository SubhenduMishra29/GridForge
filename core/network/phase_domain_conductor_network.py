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

from .topology_endpoint_reference import TopologyEndpointReference


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
    topology_reference: TopologyEndpointReference | None = None

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
        if self.topology_reference is not None:
            if not isinstance(self.topology_reference, TopologyEndpointReference):
                raise TypeError("topology_reference must be a canonical TopologyEndpointReference.")
            if kind is PhaseDomainNodeKind.BUS_CONDUCTOR:
                if not self.topology_reference.is_bus or self.topology_reference.bus_reference.object_id != self.bus_id:
                    raise ValueError("Bus-conductor topology_reference must identify its canonical Bus.")
            elif kind in {PhaseDomainNodeKind.BRANCH_TERMINAL, PhaseDomainNodeKind.EQUIPMENT_TERMINAL}:
                if not self.topology_reference.is_terminal:
                    raise ValueError("Equipment conductor topology_reference must identify a canonical Terminal.")
                endpoint = self.topology_reference.terminal_reference
                if endpoint.equipment_id != self.equipment_id or endpoint.terminal_role != self.terminal_role:
                    raise ValueError("Topology reference equipment identity/terminal role must match the conductor node.")
            else:
                raise ValueError("Earth and fault nodes cannot claim SLD topology endpoint references.")


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
            "topology_reference": None if self.topology_reference is None else dict(self.topology_reference.to_mapping()),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "PhaseDomainConductorNode":
        if not isinstance(data, Mapping):
            raise TypeError("Persisted phase-domain node must be an object.")
        allowed = {"node_id", "kind", "conductor_role", "conductor_id", "equipment_id", "terminal_role", "bus_id", "source_reference", "topology_reference"}
        legacy_allowed = allowed - {"topology_reference"}
        if frozenset(data) not in {frozenset(allowed), frozenset(legacy_allowed)}:
            raise ValueError("Persisted phase-domain node fields are incomplete or unsupported.")
        values = dict(data)
        raw_reference = values.get("topology_reference")
        if raw_reference is not None:
            values["topology_reference"] = TopologyEndpointReference.from_mapping(raw_reference)
        return cls(**values)


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
        bus_conductor_keys: set[tuple[str, str]] = set()
        equipment_terminal_keys: set[tuple[str, str, str]] = set()
        branch_terminal_keys: set[tuple[str, str, str]] = set()
        for node in nodes:
            if node.kind is PhaseDomainNodeKind.BUS_CONDUCTOR:
                key = (str(node.bus_id), str(node.conductor_id))
                if key in bus_conductor_keys:
                    raise ValueError(f"Duplicate Bus conductor identity {key!r}.")
                bus_conductor_keys.add(key)
            elif node.kind is PhaseDomainNodeKind.BRANCH_TERMINAL:
                key = (str(node.equipment_id), str(node.terminal_role), str(node.conductor_id))
                if key in branch_terminal_keys:
                    raise ValueError(f"Duplicate branch terminal conductor identity {key!r}.")
                branch_terminal_keys.add(key)
            elif node.kind is PhaseDomainNodeKind.EQUIPMENT_TERMINAL:
                key = (str(node.equipment_id), str(node.terminal_role), str(node.conductor_id))
                if key in equipment_terminal_keys:
                    raise ValueError(f"Duplicate equipment terminal conductor identity {key!r}.")
                equipment_terminal_keys.add(key)
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
            if PhaseDomainNodeKind.FAULT_NODE in {left.kind, right.kind}:
                raise ValueError("FAULT_NODE is reserved for explicit fault connections and cannot join the ordinary conductor graph.")
            if edge.kind is PhaseDomainConnectionKind.CONTINUITY:
                earth_kinds = {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}
                if left.kind in earth_kinds or right.kind in earth_kinds:
                    raise ValueError("CONTINUITY cannot replace an explicit earth bond or earth-return connection.")
                if left.conductor_role != right.conductor_role:
                    raise ValueError("CONTINUITY must join the same physical conductor role.")
            if edge.kind is PhaseDomainConnectionKind.GROUND_ELECTRODE:
                if (
                    (left.kind is PhaseDomainNodeKind.EARTH_NODE) == (right.kind is PhaseDomainNodeKind.EARTH_NODE)
                    or PhaseDomainNodeKind.EARTH_REFERENCE in {left.kind, right.kind}
                    or PhaseDomainNodeKind.FAULT_NODE in {left.kind, right.kind}
                ):
                    raise ValueError("GROUND_ELECTRODE must join one physical conductor node to one local EARTH_NODE.")
                conductor = right if left.kind is PhaseDomainNodeKind.EARTH_NODE else left
                if conductor.conductor_role not in {"N", "PE", "SHIELD", "OTHER"}:
                    raise ValueError("GROUND_ELECTRODE cannot permanently ground a phase or pilot conductor; use an explicit fault connection for fault paths.")
            if edge.kind is PhaseDomainConnectionKind.BOND:
                roles = {left.conductor_role, right.conductor_role}
                earth_kinds = {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}
                if roles & {"A", "B", "C", "PILOT", "SHIELD"}:
                    raise ValueError("BOND cannot join phase, pilot, or screen conductors; use explicit fault, screen-bond, or grounding connection kinds.")
                if left.kind in earth_kinds and right.kind in earth_kinds:
                    raise ValueError("Earth-domain nodes must use an explicit EARTH_RETURN connection.")
            if edge.kind is PhaseDomainConnectionKind.EARTH_RETURN:
                earth_kinds = {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}
                if left.kind not in earth_kinds or right.kind not in earth_kinds or PhaseDomainNodeKind.EARTH_NODE not in {left.kind, right.kind}:
                    raise ValueError("EARTH_RETURN must connect an explicit local EARTH_NODE to another earth-domain node.")
            if edge.kind is PhaseDomainConnectionKind.SCREEN_BOND:
                if "SHIELD" not in {left.conductor_role, right.conductor_role}:
                    raise ValueError("SCREEN_BOND must include an explicitly identified SHIELD conductor.")
                other_role = right.conductor_role if left.conductor_role == "SHIELD" else left.conductor_role
                other_kind = right.kind if left.conductor_role == "SHIELD" else left.kind
                if other_role != "SHIELD" and other_kind not in {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}:
                    raise ValueError("SCREEN_BOND must join a SHIELD conductor to another SHIELD conductor or explicit earth node.")
            if edge.kind is PhaseDomainConnectionKind.EQUIPMENT_BOND:
                if "PE" not in {left.conductor_role, right.conductor_role}:
                    raise ValueError("EQUIPMENT_BOND must include an explicitly identified PE conductor.")
                other_role = right.conductor_role if left.conductor_role == "PE" else left.conductor_role
                other_kind = right.kind if left.conductor_role == "PE" else left.kind
                if other_role not in {"PE", "OTHER", "EARTH"} and other_kind not in {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}:
                    raise ValueError("EQUIPMENT_BOND must join PE to PE, an equipment case (OTHER), or explicit earth.")
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

    def nodes_for_topology_reference(
        self,
        reference: TopologyEndpointReference,
        *,
        conductor_role: str,
    ) -> tuple[PhaseDomainConductorNode, ...]:
        """Resolve exact SLD endpoint/conductor matches; never infer missing mappings."""
        if not isinstance(reference, TopologyEndpointReference):
            raise TypeError("reference must be a canonical TopologyEndpointReference.")
        role = _identity(conductor_role, "conductor_role").upper()
        if role not in {"A", "B", "C", "N", "PE", "SHIELD", "PILOT", "OTHER"}:
            raise ValueError("Unsupported physical conductor role.")
        return tuple(
            node for node in self.nodes
            if node.topology_reference == reference and node.conductor_role == role
        )

    def require_unique_topology_node(
        self,
        reference: TopologyEndpointReference,
        *,
        conductor_role: str,
    ) -> PhaseDomainConductorNode:
        """Require exactly one endpoint/role match for measurement association."""
        matches = self.nodes_for_topology_reference(reference, conductor_role=conductor_role)
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one phase-domain node for topology endpoint "
                f"{reference!s} and conductor role {conductor_role!r}; found {len(matches)}."
            )
        return matches[0]

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


def build_phase_domain_conductor_network_from_sld(
    network: object,
    topology_snapshot: object,
    *,
    additional_nodes: Iterable[PhaseDomainConductorNode] = (),
    additional_connections: Iterable[PhaseDomainConnection] = (),
) -> PhaseDomainConductorNetwork:
    """Build Line/Cable conductor endpoints from committed SLD topology.

    Branch conductor inventories are the sole source of phase/neutral/PE/
    screen roles. Each branch terminal is joined to the exact Bus attachment
    vertex preserved by TopologySnapshot. Bus attachment vertices of the same
    role are joined through an ideal Busbar node, matching the existing
    equipotential Bus model; no impedance or grounding is invented for N,
    PE, screens, or earth. Direct attachments without a canonical SLD slot
    are unavailable and fail closed.
    """
    from core.model.endpoint_reference import EndpointReference, EquipmentType
    from .physical_conductor_topology import build_physical_conductor_topology_snapshot
    from .topology_snapshot import TopologySnapshot
    from .topology_endpoint_reference import TopologyEndpointReference

    if network is None or not hasattr(network, "get_by_identity"):
        raise TypeError("An authoritative Network is required.")
    if not isinstance(topology_snapshot, TopologySnapshot):
        raise TypeError("topology_snapshot must be a canonical TopologySnapshot.")
    physical = build_physical_conductor_topology_snapshot(network, topology_snapshot)

    def stable_id(*parts: str) -> str:
        import json
        return json.dumps(parts, ensure_ascii=True, separators=(",", ":"))

    nodes: dict[str, PhaseDomainConductorNode] = {}
    connections: dict[str, PhaseDomainConnection] = {}

    def add_node(node: PhaseDomainConductorNode) -> None:
        existing = nodes.get(node.node_id)
        if existing is not None and existing != node:
            raise ValueError(f"Conflicting phase-domain node identity {node.node_id!r}.")
        nodes[node.node_id] = node

    def add_connection(edge: PhaseDomainConnection) -> None:
        existing = connections.get(edge.connection_id)
        if existing is not None and existing != edge:
            raise ValueError(f"Conflicting phase-domain connection identity {edge.connection_id!r}.")
        connections[edge.connection_id] = edge

    busbar_nodes: dict[tuple[str, str], str] = {}
    bus_attachment_nodes: dict[tuple[str, str, str], str] = {}

    for branch in physical.branches:
        if not branch.in_service:
            continue
        attachment_by_terminal: dict[str, object] = {}
        for role, bus_id in (("FROM", branch.from_bus_id), ("TO", branch.to_bus_id)):
            matches = tuple(
                item for item in topology_snapshot.equipment_bus_attachments
                if item.equipment_id == branch.equipment_id
                and item.terminal_role.upper() == role
                and item.bus_id == bus_id
            )
            if len(matches) != 1:
                raise ValueError(
                    f"Active conductor branch {branch.equipment_id!r} terminal {role} "
                    f"requires exactly one canonical topology Bus attachment; found {len(matches)}."
                )
            attachment = matches[0]
            if attachment.bus_attachment_id is None:
                raise ValueError(
                    f"Active conductor branch {branch.equipment_id!r} terminal {role} "
                    "has no canonical SLD Bus attachment slot; physical graph construction is unavailable."
                )
            attachment_by_terminal[role] = attachment

        for conductor in branch.conductor_system.conductors:
            conductor_id = conductor.conductor_id
            conductor_role = conductor.role.value
            for terminal_role in ("FROM", "TO"):
                attachment = attachment_by_terminal[terminal_role]
                terminal_ref = EndpointReference.terminal(
                    equipment_type=EquipmentType(branch.equipment_type),
                    equipment_id=branch.equipment_id,
                    terminal_role=attachment.terminal_role,
                )
                bus_ref = EndpointReference.bus(
                    bus_id=attachment.bus_id,
                    attachment_id=attachment.bus_attachment_id,
                )
                terminal_topology_ref = TopologyEndpointReference.from_terminal(terminal_ref)
                bus_topology_ref = TopologyEndpointReference.from_bus(bus_ref)

                branch_node_id = stable_id("branch-terminal", branch.equipment_id, terminal_role, conductor_id)
                branch_node = PhaseDomainConductorNode(
                    node_id=branch_node_id,
                    kind=PhaseDomainNodeKind.BRANCH_TERMINAL,
                    conductor_role=conductor_role,
                    conductor_id=conductor_id,
                    equipment_id=branch.equipment_id,
                    terminal_role=terminal_role,
                    bus_id=attachment.bus_id,
                    topology_reference=terminal_topology_ref,
                )
                add_node(branch_node)

                slot_key = (attachment.bus_id, attachment.bus_attachment_id, conductor_role)
                bus_node_id = bus_attachment_nodes.get(slot_key)
                if bus_node_id is None:
                    bus_node_id = stable_id("bus-attachment", *slot_key)
                    bus_attachment_nodes[slot_key] = bus_node_id
                    add_node(PhaseDomainConductorNode(
                        node_id=bus_node_id,
                        kind=PhaseDomainNodeKind.BUS_CONDUCTOR,
                        conductor_role=conductor_role,
                        conductor_id=stable_id("attachment-conductor", attachment.bus_attachment_id, conductor_role),
                        bus_id=attachment.bus_id,
                        topology_reference=bus_topology_ref,
                    ))

                branch_edge_id = stable_id("sld-continuity", branch.equipment_id, terminal_role, conductor_id)
                add_connection(PhaseDomainConnection(
                    connection_id=branch_edge_id,
                    kind=PhaseDomainConnectionKind.CONTINUITY,
                    from_node_id=branch_node_id,
                    to_node_id=bus_node_id,
                    impedance_ohm=0j,
                    source_reference=f"SLD:{branch.equipment_id}:{terminal_role}:{conductor_id}",
                ))

                busbar_key = (attachment.bus_id, conductor_role)
                busbar_node_id = busbar_nodes.get(busbar_key)
                if busbar_node_id is None:
                    busbar_node_id = stable_id("busbar", attachment.bus_id, conductor_role)
                    busbar_nodes[busbar_key] = busbar_node_id
                    add_node(PhaseDomainConductorNode(
                        node_id=busbar_node_id,
                        kind=PhaseDomainNodeKind.BUS_CONDUCTOR,
                        conductor_role=conductor_role,
                        conductor_id=stable_id("busbar-conductor", conductor_role),
                        bus_id=attachment.bus_id,
                    ))
                busbar_edge_id = stable_id("busbar-continuity", attachment.bus_id, attachment.bus_attachment_id, conductor_role)
                add_connection(PhaseDomainConnection(
                    connection_id=busbar_edge_id,
                    kind=PhaseDomainConnectionKind.CONTINUITY,
                    from_node_id=bus_node_id,
                    to_node_id=busbar_node_id,
                    impedance_ohm=0j,
                    source_reference=f"BUSBAR:{attachment.bus_id}:{attachment.bus_attachment_id}:{conductor_role}",
                ))


    # Switching equipment is not a wire. Only explicit physical pole
    # construction may create an internal conducting path.
    for breaker in getattr(network, "breakers", ()):
        if not getattr(breaker, "in_service", True):
            continue
        pole_states = getattr(breaker, "phase_domain_pole_states", None)
        if pole_states is None:
            raise ValueError(
                f"In-service Breaker {breaker.id!r} has no explicit "
                "phase_domain_pole_states construction."
            )
        if getattr(breaker, "failed", False):
            raise ValueError(
                f"Breaker {breaker.id!r} is failed; pole conduction is indeterminate."
            )
        terminal_attachments = {}
        for terminal in breaker.terminals:
            role = str(terminal.role).upper()
            matches = tuple(
                item for item in topology_snapshot.equipment_bus_attachments
                if item.equipment_id == breaker.id and item.terminal_role.upper() == role
            )
            if len(matches) != 1 or matches[0].bus_attachment_id is None:
                raise ValueError(
                    f"Breaker {breaker.id!r} terminal {role} requires one canonical SLD Bus attachment slot."
                )
            terminal_attachments[role] = (terminal, matches[0])
        if set(terminal_attachments) != {"FROM", "TO"}:
            raise ValueError(f"Breaker {breaker.id!r} requires exactly FROM and TO terminals.")

        for conductor_role, pole_closed in pole_states.items():
            terminal_nodes = {}
            for terminal_role in ("FROM", "TO"):
                terminal, attachment = terminal_attachments[terminal_role]
                terminal_ref = EndpointReference.terminal(
                    equipment_type=EquipmentType("breaker"),
                    equipment_id=breaker.id,
                    terminal_role=terminal.role,
                )
                equipment_node_id = stable_id("breaker-terminal", breaker.id, terminal_role, conductor_role)
                add_node(PhaseDomainConductorNode(
                    node_id=equipment_node_id,
                    kind=PhaseDomainNodeKind.EQUIPMENT_TERMINAL,
                    conductor_role=conductor_role,
                    conductor_id=stable_id("breaker-pole", breaker.id, conductor_role),
                    equipment_id=breaker.id,
                    terminal_role=terminal.role,
                    bus_id=attachment.bus_id,
                    topology_reference=TopologyEndpointReference.from_terminal(terminal_ref),
                ))
                terminal_nodes[terminal_role] = equipment_node_id
                slot_key = (attachment.bus_id, attachment.bus_attachment_id, conductor_role)
                bus_node_id = bus_attachment_nodes.get(slot_key)
                if bus_node_id is None:
                    bus_node_id = stable_id("bus-attachment", *slot_key)
                    bus_attachment_nodes[slot_key] = bus_node_id
                    add_node(PhaseDomainConductorNode(
                        node_id=bus_node_id,
                        kind=PhaseDomainNodeKind.BUS_CONDUCTOR,
                        conductor_role=conductor_role,
                        conductor_id=stable_id("attachment-conductor", attachment.bus_attachment_id, conductor_role),
                        bus_id=attachment.bus_id,
                        topology_reference=TopologyEndpointReference.from_bus(
                            EndpointReference.bus(bus_id=attachment.bus_id, attachment_id=attachment.bus_attachment_id)
                        ),
                    ))
                add_connection(PhaseDomainConnection(
                    connection_id=stable_id("breaker-terminal-continuity", breaker.id, terminal_role, conductor_role),
                    kind=PhaseDomainConnectionKind.CONTINUITY,
                    from_node_id=equipment_node_id,
                    to_node_id=bus_node_id,
                    impedance_ohm=0j,
                    source_reference=f"BREAKER-TERMINAL:{breaker.id}:{terminal_role}:{conductor_role}",
                ))
                busbar_key = (attachment.bus_id, conductor_role)
                busbar_node_id = busbar_nodes.get(busbar_key)
                if busbar_node_id is None:
                    busbar_node_id = stable_id("busbar", attachment.bus_id, conductor_role)
                    busbar_nodes[busbar_key] = busbar_node_id
                    add_node(PhaseDomainConductorNode(
                        node_id=busbar_node_id,
                        kind=PhaseDomainNodeKind.BUS_CONDUCTOR,
                        conductor_role=conductor_role,
                        conductor_id=stable_id("busbar-conductor", conductor_role),
                        bus_id=attachment.bus_id,
                    ))
                add_connection(PhaseDomainConnection(
                    connection_id=stable_id("busbar-continuity", attachment.bus_id, attachment.bus_attachment_id, conductor_role),
                    kind=PhaseDomainConnectionKind.CONTINUITY,
                    from_node_id=bus_node_id,
                    to_node_id=busbar_node_id,
                    impedance_ohm=0j,
                    source_reference=f"BUSBAR:{attachment.bus_id}:{attachment.bus_attachment_id}:{conductor_role}",
                ))
            if breaker.closed and pole_closed:
                add_connection(PhaseDomainConnection(
                    connection_id=stable_id("breaker-pole", breaker.id, conductor_role),
                    kind=PhaseDomainConnectionKind.CONTINUITY,
                    from_node_id=terminal_nodes["FROM"],
                    to_node_id=terminal_nodes["TO"],
                    impedance_ohm=0j,
                    source_reference=f"BREAKER-POLE:{breaker.id}:{conductor_role}:CLOSED",
                ))


    # Switches, disconnectors and fuses use the same explicit physical
    # conductor inventory contract. Their own Core state determines whether
    # the internal conductor path is currently continuous.
    for collection_name, equipment_type in (
        ("switches", "switch"),
        ("disconnectors", "disconnector"),
        ("fuses", "fuse"),
    ):
        for device in getattr(network, collection_name, ()):
            if not getattr(device, "in_service", True):
                continue
            roles = getattr(device, "phase_domain_conductor_roles", None)
            if roles is None:
                raise ValueError(
                    f"In-service {equipment_type.title()} {device.id!r} has no explicit "
                    "phase_domain_conductor_roles construction."
                )
            terminal_attachments = {}
            for terminal in device.terminals:
                terminal_role = str(terminal.role).upper()
                matches = tuple(
                    item for item in topology_snapshot.equipment_bus_attachments
                    if item.equipment_id == device.id
                    and item.terminal_role.upper() == terminal_role
                )
                if len(matches) != 1 or matches[0].bus_attachment_id is None:
                    raise ValueError(
                        f"{equipment_type.title()} {device.id!r} terminal {terminal_role} "
                        "requires one canonical SLD Bus attachment slot."
                    )
                terminal_attachments[terminal_role] = (terminal, matches[0])
            if set(terminal_attachments) != {"FROM", "TO"}:
                raise ValueError(
                    f"{equipment_type.title()} {device.id!r} requires exactly FROM and TO terminals."
                )

            for conductor_role in roles:
                terminal_nodes = {}
                for terminal_role in ("FROM", "TO"):
                    terminal, attachment = terminal_attachments[terminal_role]
                    terminal_ref = EndpointReference.terminal(
                        equipment_type=EquipmentType(equipment_type),
                        equipment_id=device.id,
                        terminal_role=terminal.role,
                    )
                    equipment_node_id = stable_id(
                        equipment_type + "-terminal", device.id, terminal_role, conductor_role
                    )
                    add_node(PhaseDomainConductorNode(
                        node_id=equipment_node_id,
                        kind=PhaseDomainNodeKind.EQUIPMENT_TERMINAL,
                        conductor_role=conductor_role,
                        conductor_id=stable_id(equipment_type + "-conductor", device.id, conductor_role),
                        equipment_id=device.id,
                        terminal_role=terminal.role,
                        bus_id=attachment.bus_id,
                        topology_reference=TopologyEndpointReference.from_terminal(terminal_ref),
                    ))
                    terminal_nodes[terminal_role] = equipment_node_id

                    slot_key = (attachment.bus_id, attachment.bus_attachment_id, conductor_role)
                    bus_node_id = bus_attachment_nodes.get(slot_key)
                    if bus_node_id is None:
                        bus_node_id = stable_id("bus-attachment", *slot_key)
                        bus_attachment_nodes[slot_key] = bus_node_id
                        add_node(PhaseDomainConductorNode(
                            node_id=bus_node_id,
                            kind=PhaseDomainNodeKind.BUS_CONDUCTOR,
                            conductor_role=conductor_role,
                            conductor_id=stable_id("attachment-conductor", attachment.bus_attachment_id, conductor_role),
                            bus_id=attachment.bus_id,
                            topology_reference=TopologyEndpointReference.from_bus(
                                EndpointReference.bus(
                                    bus_id=attachment.bus_id,
                                    attachment_id=attachment.bus_attachment_id,
                                )
                            ),
                        ))
                    add_connection(PhaseDomainConnection(
                        connection_id=stable_id(
                            equipment_type + "-terminal-continuity", device.id, terminal_role, conductor_role
                        ),
                        kind=PhaseDomainConnectionKind.CONTINUITY,
                        from_node_id=equipment_node_id,
                        to_node_id=bus_node_id,
                        impedance_ohm=0j,
                        source_reference=f"{equipment_type.upper()}-TERMINAL:{device.id}:{terminal_role}:{conductor_role}",
                    ))

                    busbar_key = (attachment.bus_id, conductor_role)
                    busbar_node_id = busbar_nodes.get(busbar_key)
                    if busbar_node_id is None:
                        busbar_node_id = stable_id("busbar", attachment.bus_id, conductor_role)
                        busbar_nodes[busbar_key] = busbar_node_id
                        add_node(PhaseDomainConductorNode(
                            node_id=busbar_node_id,
                            kind=PhaseDomainNodeKind.BUS_CONDUCTOR,
                            conductor_role=conductor_role,
                            conductor_id=stable_id("busbar-conductor", conductor_role),
                            bus_id=attachment.bus_id,
                        ))
                    add_connection(PhaseDomainConnection(
                        connection_id=stable_id(
                            "busbar-continuity", attachment.bus_id, attachment.bus_attachment_id, conductor_role
                        ),
                        kind=PhaseDomainConnectionKind.CONTINUITY,
                        from_node_id=bus_node_id,
                        to_node_id=busbar_node_id,
                        impedance_ohm=0j,
                        source_reference=f"BUSBAR:{attachment.bus_id}:{attachment.bus_attachment_id}:{conductor_role}",
                    ))

                conducts = (
                    bool(getattr(device, "closed", False))
                    if equipment_type in {"switch", "disconnector"}
                    else bool(getattr(device, "conducts", False))
                )
                if conducts:
                    add_connection(PhaseDomainConnection(
                        connection_id=stable_id(equipment_type + "-pole", device.id, conductor_role),
                        kind=PhaseDomainConnectionKind.CONTINUITY,
                        from_node_id=terminal_nodes["FROM"],
                        to_node_id=terminal_nodes["TO"],
                        impedance_ohm=0j,
                        source_reference=f"{equipment_type.upper()}-PATH:{device.id}:{conductor_role}:CONDUCTING",
                    ))

    for node in additional_nodes:
        add_node(node)
    for edge in additional_connections:
        add_connection(edge)

    return build_phase_domain_conductor_network(
        project_id=topology_snapshot.project_id,
        activation_generation=topology_snapshot.activation_generation,
        topology_revision=topology_snapshot.topology_revision,
        nodes=tuple(nodes.values()),
        connections=tuple(connections.values()),
    )


__all__ = [
    "PhaseDomainNodeKind",
    "PhaseDomainConnectionKind",
    "PhaseDomainConductorNode",
    "PhaseDomainConnection",
    "PhaseDomainConductorNetwork",
    "build_phase_domain_conductor_network",
    "build_phase_domain_conductor_network_from_sld",
]
