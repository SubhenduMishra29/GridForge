from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from core.model.endpoint_reference import EquipmentType


_SWITCHING_EQUIPMENT_TYPES = frozenset(
    equipment_type.value
    for equipment_type in EquipmentType
    if equipment_type.value in {"breaker", "switch", "disconnector", "fuse"}
)
_CANONICAL_EQUIPMENT_TYPES = frozenset(equipment_type.value for equipment_type in EquipmentType)


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value


def _require_string_sequence(values: object, field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
        raise TypeError(f"{field_name} must be an iterable of strings.")
    result = tuple(values)
    for value in result:
        _require_non_empty_string(value, field_name)
    return result


@dataclass(frozen=True, slots=True)
class EquipmentBusAttachment:
    equipment_id: str
    equipment_type: str
    terminal_role: str
    bus_id: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.equipment_id, "equipment_id")
        _require_non_empty_string(self.equipment_type, "equipment_type")
        _require_non_empty_string(self.terminal_role, "terminal_role")
        _require_non_empty_string(self.bus_id, "bus_id")
        if self.equipment_type not in _CANONICAL_EQUIPMENT_TYPES:
            raise ValueError(
                f"equipment_type must be a canonical EquipmentType value; "
                f"got {self.equipment_type!r}."
            )


@dataclass(frozen=True, slots=True)
class ConductiveEdge:
    """Resolved conductive relationship for switching equipment only.

    This structure deliberately models an already-resolved switching
    relationship. It is not a numerical branch representation: Line/Cable/
    Transformer boundaries remain separate in equipment_bus_attachments and
    numerical preparation.
    """

    equipment_id: str
    equipment_type: str
    from_bus_id: str
    to_bus_id: str
    from_terminal_role: str
    to_terminal_role: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.equipment_id, "equipment_id")
        _require_non_empty_string(self.equipment_type, "equipment_type")
        _require_non_empty_string(self.from_bus_id, "from_bus_id")
        _require_non_empty_string(self.to_bus_id, "to_bus_id")
        _require_non_empty_string(self.from_terminal_role, "from_terminal_role")
        _require_non_empty_string(self.to_terminal_role, "to_terminal_role")
        if self.equipment_type not in _SWITCHING_EQUIPMENT_TYPES:
            raise ValueError(
                "ConductiveEdge equipment_type must identify canonical switching equipment; "
                f"got {self.equipment_type!r}."
            )
        if self.from_bus_id == self.to_bus_id:
            raise ValueError("ConductiveEdge cannot connect a Bus to itself.")
        if self.from_terminal_role == self.to_terminal_role:
            raise ValueError(
                "ConductiveEdge terminal roles must identify distinct endpoints."
            )

    @property
    def edge_identity(self) -> tuple[str, str, str, str, str, str]:
        """Return the deterministic identity of this resolved physical edge."""
        first_bus, second_bus = sorted((self.from_bus_id, self.to_bus_id))
        first_role, second_role = (
            (self.from_terminal_role, self.to_terminal_role)
            if self.from_bus_id <= self.to_bus_id
            else (self.to_terminal_role, self.from_terminal_role)
        )
        return (
            self.equipment_id,
            self.equipment_type,
            first_bus,
            second_bus,
            first_role,
            second_role,
        )


@dataclass(frozen=True, slots=True)
class TopologyProvenance:
    project_id: str
    activation_generation: int
    topology_revision: int

    def __post_init__(self) -> None:
        _require_non_empty_string(self.project_id, "project_id")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int):
            raise TypeError("activation_generation must be an integer.")
        if self.activation_generation < 1:
            raise ValueError("activation_generation must be positive.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int):
            raise TypeError("topology_revision must be an integer.")
        if self.topology_revision < 0:
            raise ValueError("topology_revision must be non-negative.")


@dataclass(frozen=True, slots=True)
class TopologySnapshot:
    project_id: str
    activation_generation: int
    topology_revision: int
    bus_ids: tuple[str, ...]
    bus_adjacency: Mapping[str, tuple[str, ...]]
    equipment_bus_attachments: tuple[EquipmentBusAttachment, ...]
    conductive_edges: tuple[ConductiveEdge, ...]
    islands: tuple[tuple[str, ...], ...]
    normalization_status: str = "VALID"

    def __post_init__(self) -> None:
        _require_non_empty_string(self.project_id, "project_id")
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int):
            raise TypeError("activation_generation must be an integer.")
        if self.activation_generation < 1:
            raise ValueError("activation_generation must be positive.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int):
            raise TypeError("topology_revision must be an integer.")
        if self.topology_revision < 0:
            raise ValueError("topology_revision must be non-negative.")
        if self.normalization_status != "VALID":
            raise ValueError("Only valid normalized topology can become a snapshot.")

        raw_buses = _require_string_sequence(self.bus_ids, "bus_ids")
        if len(raw_buses) != len(set(raw_buses)):
            raise ValueError("bus_ids must be unique.")
        if tuple(sorted(raw_buses)) != raw_buses:
            raise ValueError("bus_ids must already use deterministic canonical ordering.")
        buses = raw_buses
        bus_set = frozenset(buses)
        object.__setattr__(self, "bus_ids", buses)

        if not isinstance(self.bus_adjacency, Mapping):
            raise TypeError("bus_adjacency must be a mapping.")
        raw_adjacency = dict(self.bus_adjacency)
        if set(raw_adjacency) != bus_set:
            raise ValueError("bus_adjacency must contain every canonical Bus exactly once.")
        adjacency: dict[str, tuple[str, ...]] = {}
        for bus_id, values in raw_adjacency.items():
            _require_non_empty_string(bus_id, "bus_adjacency Bus ID")
            if bus_id not in bus_set:
                raise ValueError(f"bus_adjacency references unknown Bus {bus_id!r}.")
            neighbours = _require_string_sequence(values, f"adjacency[{bus_id!r}]")
            if bus_id in neighbours:
                raise ValueError("bus_adjacency cannot contain self-adjacency.")
            if len(neighbours) != len(set(neighbours)):
                raise ValueError(f"adjacency[{bus_id!r}] contains duplicate neighbours.")
            if any(neighbour not in bus_set for neighbour in neighbours):
                raise ValueError(f"adjacency[{bus_id!r}] references an unknown Bus.")
            if neighbours != tuple(sorted(neighbours)):
                raise ValueError(f"adjacency[{bus_id!r}] must use deterministic neighbour ordering.")
            adjacency[bus_id] = neighbours

        for bus_id, neighbours in adjacency.items():
            for neighbour in neighbours:
                if bus_id not in adjacency[neighbour]:
                    raise ValueError("bus_adjacency must be symmetric.")
        object.__setattr__(self, "bus_adjacency", MappingProxyType(adjacency))

        attachments = tuple(self.equipment_bus_attachments)
        if any(not isinstance(item, EquipmentBusAttachment) for item in attachments):
            raise TypeError("equipment_bus_attachments must contain EquipmentBusAttachment values.")
        attachment_keys = [(item.equipment_id, item.terminal_role) for item in attachments]
        if len(attachment_keys) != len(set(attachment_keys)):
            raise ValueError(
                "equipment_bus_attachments contains duplicate "
                "(equipment_id, terminal_role) identities."
            )
        if any(item.bus_id not in bus_set for item in attachments):
            raise ValueError("equipment_bus_attachments references an unknown Bus.")
        attachment_order = sorted(
            attachments,
            key=lambda item: (
                item.equipment_id,
                item.equipment_type,
                item.terminal_role,
                item.bus_id,
            ),
        )
        if attachments != tuple(attachment_order):
            raise ValueError("equipment_bus_attachments must use deterministic ordering.")
        object.__setattr__(self, "equipment_bus_attachments", attachments)

        edges = tuple(self.conductive_edges)
        if any(not isinstance(edge, ConductiveEdge) for edge in edges):
            raise TypeError("conductive_edges must contain ConductiveEdge values.")
        if any(
            edge.from_bus_id not in bus_set or edge.to_bus_id not in bus_set
            for edge in edges
        ):
            raise ValueError("conductive_edges references an unknown Bus.")
        edge_identities = [edge.edge_identity for edge in edges]
        if len(edge_identities) != len(set(edge_identities)):
            raise ValueError("conductive_edges contains duplicate physical relationships.")
        edge_order = sorted(edges, key=lambda edge: edge.edge_identity)
        if edges != tuple(edge_order):
            raise ValueError("conductive_edges must use deterministic ordering.")
        object.__setattr__(self, "conductive_edges", edges)

        raw_islands = tuple(self.islands)
        normalized_islands: list[tuple[str, ...]] = []
        seen_buses: set[str] = set()
        for island in raw_islands:
            island_buses = _require_string_sequence(island, "island")
            if not island_buses:
                raise ValueError("islands cannot contain empty island records.")
            if len(island_buses) != len(set(island_buses)):
                raise ValueError("island records cannot contain duplicate Bus IDs.")
            if tuple(sorted(island_buses)) != island_buses:
                raise ValueError("island Bus IDs must use deterministic ordering.")
            if any(bus_id not in bus_set for bus_id in island_buses):
                raise ValueError("islands references an unknown Bus.")
            overlap = seen_buses.intersection(island_buses)
            if overlap:
                raise ValueError(
                    f"islands contain Bus IDs assigned to multiple islands: {sorted(overlap)!r}."
                )
            seen_buses.update(island_buses)
            normalized_islands.append(island_buses)

        if seen_buses != bus_set:
            missing = sorted(bus_set - seen_buses)
            raise ValueError(
                f"islands must contain every canonical Bus exactly once; missing={missing!r}."
            )
        ordered_islands = tuple(sorted(normalized_islands))
        if raw_islands != ordered_islands:
            raise ValueError("islands must use deterministic ordering.")
        object.__setattr__(self, "islands", raw_islands)

    @property
    def provenance(self) -> TopologyProvenance:
        return TopologyProvenance(
            self.project_id,
            self.activation_generation,
            self.topology_revision,
        )

    def neighbours(self, bus_id: str) -> tuple[str, ...]:
        return self.bus_adjacency.get(bus_id, ())


__all__ = [
    "ConductiveEdge",
    "EquipmentBusAttachment",
    "TopologyProvenance",
    "TopologySnapshot",
]
