from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

@dataclass(frozen=True, slots=True)
class EquipmentBusAttachment:
    equipment_id: str
    terminal_role: str
    bus_id: str

@dataclass(frozen=True, slots=True)
class ConductiveEdge:
    """Conductive edge for switching equipment only.

    This structure deliberately models switching conductive state
    (Breaker/Switch/Disconnector/Fuse). It is not the numerical branch
    representation: Line/Cable/Transformer boundaries remain separate in
    equipment_bus_attachments and numerical preparation.
    """
    equipment_id: str
    equipment_type: str
    from_bus_id: str
    to_bus_id: str
    from_terminal_role: str
    to_terminal_role: str

@dataclass(frozen=True, slots=True)
class TopologyProvenance:
    project_id: str
    activation_generation: int
    topology_revision: int

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
        if not self.project_id.strip():
            raise ValueError("project_id must be non-empty.")
        if self.activation_generation < 1:
            raise ValueError("activation_generation must be positive.")
        if self.topology_revision < 0:
            raise ValueError("topology_revision must be non-negative.")
        if self.normalization_status != "VALID":
            raise ValueError("Only valid normalized topology can become a snapshot.")
        buses = tuple(sorted(self.bus_ids))
        if len(buses) != len(set(buses)):
            raise ValueError("bus_ids must be unique.")
        object.__setattr__(self, "bus_ids", buses)
        adjacency = {str(k): tuple(sorted(str(v) for v in values)) for k, values in self.bus_adjacency.items()}
        if set(adjacency) != set(buses):
            raise ValueError("bus_adjacency must contain every Bus.")
        for bus_id, neighbours in adjacency.items():
            if bus_id in neighbours or len(neighbours) != len(set(neighbours)):
                raise ValueError("bus_adjacency contains an invalid self/duplicate edge.")
            if any(neighbour not in buses for neighbour in neighbours):
                raise ValueError("bus_adjacency references an unknown Bus.")
            if any(bus_id not in adjacency.get(neighbour, ()) for neighbour in neighbours):
                raise ValueError("bus_adjacency must be symmetric.")
        object.__setattr__(self, "bus_adjacency", MappingProxyType(adjacency))
        object.__setattr__(self, "equipment_bus_attachments", tuple(sorted(self.equipment_bus_attachments, key=lambda x:(x.equipment_id,x.terminal_role,x.bus_id))))
        object.__setattr__(self, "conductive_edges", tuple(sorted(self.conductive_edges, key=lambda x:(x.equipment_id,x.from_bus_id,x.to_bus_id))))
        normalized = tuple(sorted(tuple(sorted(set(island))) for island in self.islands))
        flattened = [bus for island in normalized for bus in island]
        if tuple(sorted(flattened)) != buses or len(flattened) != len(set(flattened)):
            raise ValueError("islands must be a complete duplicate-free Bus-ID partition.")
        object.__setattr__(self, "islands", normalized)

    @property
    def provenance(self) -> TopologyProvenance:
        return TopologyProvenance(self.project_id, self.activation_generation, self.topology_revision)

    def neighbours(self, bus_id: str) -> tuple[str, ...]:
        return self.bus_adjacency.get(bus_id, ())

__all__=["ConductiveEdge","EquipmentBusAttachment","TopologyProvenance","TopologySnapshot"]
