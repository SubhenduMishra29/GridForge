"""Detached physical-conductor topology resolved from canonical Network topology.

This module maps explicit Line/Cable conductor inventories to their canonical
FROM/TO Bus attachments. It does not create electrical nodes, connect neutral
or protective-earth conductors to ground, or calculate conductor currents.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model.conductor import BranchConductorSystem, PhysicalConductor
from core.network.topology_snapshot import TopologySnapshot


@dataclass(frozen=True, slots=True)
class PhysicalConductorBranchTopology:
    """One branch's explicit physical conductors and canonical terminal Bus map."""

    equipment_id: str
    equipment_type: str
    from_terminal_role: str
    to_terminal_role: str
    from_bus_id: str | None
    to_bus_id: str | None
    in_service: bool
    conductor_system: BranchConductorSystem

    def __post_init__(self) -> None:
        for name in ("equipment_id", "equipment_type", "from_terminal_role", "to_terminal_role"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        if self.equipment_type not in {"line", "cable"}:
            raise ValueError("Physical conductor branch topology supports only Line and Cable.")
        if self.from_terminal_role != "FROM" or self.to_terminal_role != "TO":
            raise ValueError("Physical conductor branch requires canonical FROM and TO terminal roles.")
        for name in ("from_bus_id", "to_bus_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty Bus identity or None.")
            if value is not None:
                object.__setattr__(self, name, value.strip())
        if type(self.in_service) is not bool:
            raise TypeError("in_service must be bool.")
        if not isinstance(self.conductor_system, BranchConductorSystem):
            raise TypeError("conductor_system must be BranchConductorSystem.")
        if self.in_service:
            if self.from_bus_id is None or self.to_bus_id is None:
                raise ValueError("In-service physical conductor branch requires resolved FROM and TO Buses.")
            if self.from_bus_id == self.to_bus_id:
                raise ValueError("Physical conductor branch cannot connect a Bus to itself.")

    @property
    def conductor_ids(self) -> tuple[str, ...]:
        return tuple(item.conductor_id for item in self.conductor_system.conductors)

    @property
    def conductor_roles(self) -> tuple[str, ...]:
        return tuple(item.role.value for item in self.conductor_system.conductors)

    @property
    def conductor_associations(self) -> tuple[PhysicalConductorBranchAssociation, ...]:
        """Return one explicit branch-terminal association per conductor."""
        return tuple(
            PhysicalConductorBranchAssociation(
                equipment_id=self.equipment_id,
                conductor_id=item.conductor_id,
                conductor_role=item.role.value,
                from_bus_id=self.from_bus_id,
                to_bus_id=self.to_bus_id,
            )
            for item in self.conductor_system.conductors
        )


@dataclass(frozen=True, slots=True)
class PhysicalConductorBranchAssociation:
    """Associate one conductor identity with its owning branch terminal pair.

    The FROM/TO Bus IDs are the resolved branch-terminal attachment points.
    This is not a claim that individual phase/neutral/PE terminals or
    conductor-to-ground bonds have been modelled.
    """

    equipment_id: str
    conductor_id: str
    conductor_role: str
    from_bus_id: str | None
    to_bus_id: str | None

    def __post_init__(self) -> None:
        for name in ("equipment_id", "conductor_id", "conductor_role"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        for name in ("from_bus_id", "to_bus_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty Bus identity or None.")
            if value is not None:
                object.__setattr__(self, name, value.strip())

    @property
    def identity(self) -> tuple[str, str]:
        return self.equipment_id, self.conductor_id


@dataclass(frozen=True, slots=True)
class PhysicalConductorTopologySnapshot:
    """Immutable conductor-to-branch topology projection with source provenance."""

    project_id: str
    activation_generation: int
    topology_revision: int
    branches: tuple[PhysicalConductorBranchTopology, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")
        branches = tuple(self.branches)
        if any(not isinstance(item, PhysicalConductorBranchTopology) for item in branches):
            raise TypeError("branches must contain PhysicalConductorBranchTopology records.")
        ids = tuple(item.equipment_id for item in branches)
        if len(ids) != len(set(ids)):
            raise ValueError("Physical conductor topology contains duplicate equipment identities.")
        if branches != tuple(sorted(branches, key=lambda item: (item.equipment_type, item.equipment_id))):
            raise ValueError("Physical conductor branches must use deterministic ordering.")
        object.__setattr__(self, "branches", branches)

    def branch(self, equipment_id: str) -> PhysicalConductorBranchTopology:
        for item in self.branches:
            if item.equipment_id == equipment_id:
                return item
        raise KeyError(f"No physical conductor topology exists for branch {equipment_id!r}.")


def build_physical_conductor_topology_snapshot(
    network: Any,
    topology_snapshot: TopologySnapshot,
) -> PhysicalConductorTopologySnapshot:
    """Resolve configured Line/Cable conductor systems through canonical topology.

    Active conductor-equipped branches must resolve exactly one Bus at each
    canonical terminal. Inactive branches may retain unresolved endpoints.
    The resolver consumes TopologySnapshot attachments only; it never reads
    SLD graphics or infers Bus/neutral/earth relationships.
    """
    if network is None or not hasattr(network, "lines") or not hasattr(network, "cables"):
        raise TypeError("An authoritative Network is required.")
    if not isinstance(topology_snapshot, TopologySnapshot):
        raise TypeError("topology_snapshot must be a canonical TopologySnapshot.")
    state = getattr(network, "state", None)
    revision = getattr(state, "topology_revision", None)
    if revision != topology_snapshot.topology_revision:
        raise ValueError("TopologySnapshot revision does not match the current Network revision.")
    if not bool(getattr(state, "topology_valid", False)):
        raise ValueError("Physical conductor topology requires a valid, rebuilt Network topology.")

    attachments: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for item in topology_snapshot.equipment_bus_attachments:
        attachments.setdefault((item.equipment_id, item.terminal_role), []).append((item.equipment_type, item.bus_id))

    records: list[PhysicalConductorBranchTopology] = []
    for equipment_type, collection in (("line", network.lines), ("cable", network.cables)):
        for branch in collection:
            system = getattr(branch, "conductor_system", None)
            if system is None:
                continue
            equipment_id = getattr(branch, "id", None)
            if not isinstance(equipment_id, str) or not equipment_id.strip():
                raise ValueError("Conductor-equipped branch has no canonical equipment identity.")
            from_terminal = getattr(branch, "from_terminal", None)
            to_terminal = getattr(branch, "to_terminal", None)
            if from_terminal is None or to_terminal is None:
                raise ValueError(f"Conductor-equipped {equipment_type} '{equipment_id}' lacks canonical terminals.")
            if from_terminal.owner is not branch or to_terminal.owner is not branch:
                raise ValueError(f"Conductor-equipped {equipment_type} '{equipment_id}' has invalid terminal ownership.")
            if from_terminal.role != "FROM" or to_terminal.role != "TO":
                raise ValueError(f"Conductor-equipped {equipment_type} '{equipment_id}' has non-canonical terminal roles.")

            from_matches = attachments.get((equipment_id, "FROM"), [])
            to_matches = attachments.get((equipment_id, "TO"), [])
            active = bool(getattr(branch, "in_service", True))
            if active and (len(from_matches) != 1 or len(to_matches) != 1):
                raise ValueError(
                    f"In-service {equipment_type} '{equipment_id}' requires exactly one canonical Bus "
                    f"attachment per terminal; FROM={from_matches!r}, TO={to_matches!r}."
                )
            if len(from_matches) > 1 or len(to_matches) > 1:
                raise ValueError(f"{equipment_type} '{equipment_id}' has ambiguous physical-conductor terminal attachment.")
            for matches in (from_matches, to_matches):
                if matches and matches[0][0] != equipment_type:
                    raise ValueError(f"{equipment_type} '{equipment_id}' topology attachment has contradictory equipment type.")
            from_bus = from_matches[0][1] if from_matches else None
            to_bus = to_matches[0][1] if to_matches else None
            if active and from_bus == to_bus:
                raise ValueError(f"In-service {equipment_type} '{equipment_id}' resolves both terminals to the same Bus.")

            records.append(PhysicalConductorBranchTopology(
                equipment_id=equipment_id,
                equipment_type=equipment_type,
                from_terminal_role="FROM",
                to_terminal_role="TO",
                from_bus_id=from_bus,
                to_bus_id=to_bus,
                in_service=active,
                conductor_system=system,
            ))

    return PhysicalConductorTopologySnapshot(
        project_id=topology_snapshot.project_id,
        activation_generation=topology_snapshot.activation_generation,
        topology_revision=topology_snapshot.topology_revision,
        branches=tuple(sorted(records, key=lambda item: (item.equipment_type, item.equipment_id))),
    )


__all__ = [
    "PhysicalConductorBranchAssociation",
    "PhysicalConductorBranchTopology",
    "PhysicalConductorTopologySnapshot",
    "build_physical_conductor_topology_snapshot",
]
