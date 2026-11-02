"""Global nodal admittance assembly for explicit physical conductors.

All primitive stamps are assembled in SI units (siemens) so a declared
connection impedance is never silently converted on an assumed voltage base.
Earth-reference nodes are fixed at zero potential; only explicit zero-ohm
connections are contracted. Missing conductor nodes or matrix members fail
closed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from core.network.phase_domain_conductor_network import (
    PhaseDomainConductorNetwork,
    PhaseDomainNodeKind,
    PhaseDomainConnectionKind,
)
from .physical_conductor_preparation import PhysicalConductorImpedanceSnapshot


@dataclass(frozen=True, slots=True)
class PhaseDomainAdmittanceSnapshot:
    """Immutable global physical-conductor Y matrix in siemens."""

    project_id: str
    activation_generation: int
    topology_revision: int
    node_ids: tuple[str, ...]
    admittance_siemens: tuple[tuple[complex, ...], ...]
    source_node_to_index: Mapping[str, int | None]
    earth_reference_node_ids: tuple[str, ...]
    branch_ids: tuple[str, ...]
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ids = tuple(self.node_ids)
        matrix = tuple(tuple(complex(value) for value in row) for row in self.admittance_siemens)
        if len(matrix) != len(ids) or any(len(row) != len(ids) for row in matrix):
            raise ValueError("Global phase-domain admittance dimensions must match node_ids.")
        if any(not math.isfinite(x.real) or not math.isfinite(x.imag) for row in matrix for x in row):
            raise ValueError("Global phase-domain admittance matrix must be finite.")
        if len(ids) != len(set(ids)):
            raise ValueError("Collapsed phase-domain node identities must be unique.")
        object.__setattr__(self, "node_ids", ids)
        object.__setattr__(self, "admittance_siemens", matrix)
        object.__setattr__(self, "source_node_to_index", MappingProxyType(dict(self.source_node_to_index)))
        object.__setattr__(self, "earth_reference_node_ids", tuple(self.earth_reference_node_ids))
        object.__setattr__(self, "branch_ids", tuple(self.branch_ids))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))


class _DisjointSet:
    def __init__(self, values: tuple[str, ...]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            low, high = sorted((a, b))
            self.parent[high] = low


def assemble_phase_domain_admittance(
    graph: PhaseDomainConductorNetwork,
    impedances: PhysicalConductorImpedanceSnapshot,
) -> PhaseDomainAdmittanceSnapshot:
    """Stamp all coupled branch and explicit connection primitives globally.

    Line/Cable full mutual series matrices are stamped as two-terminal
    multi-conductor blocks. Explicit shunt matrices use nominal-pi half-shunts.
    Other graph connections use their declared ohmic impedance. A missing
    shunt matrix contributes no shunt stamp and remains represented as absent
    in the source impedance snapshot.
    """
    if not isinstance(graph, PhaseDomainConductorNetwork):
        raise TypeError("graph must be PhaseDomainConductorNetwork.")
    if not isinstance(impedances, PhysicalConductorImpedanceSnapshot):
        raise TypeError("impedances must be PhysicalConductorImpedanceSnapshot.")
    provenance = (graph.project_id, graph.activation_generation, graph.topology_revision)
    if provenance != (impedances.project_id, impedances.activation_generation, impedances.topology_revision):
        raise ValueError("Phase-domain graph and impedance snapshot provenance do not match.")

    nodes = {item.node_id: item for item in graph.nodes}
    earth_ids = tuple(sorted(x.node_id for x in graph.nodes if x.kind is PhaseDomainNodeKind.EARTH_REFERENCE))
    sets = _DisjointSet(tuple(sorted(nodes)))
    for edge in graph.connections:
        if edge.in_service and edge.impedance_ohm == 0j:
            sets.union(edge.from_node_id, edge.to_node_id)

    earth_roots = {sets.find(node_id) for node_id in earth_ids}
    roots = tuple(sorted({sets.find(node_id) for node_id in nodes} - earth_roots))
    root_index = {root: index for index, root in enumerate(roots)}
    matrix = np.zeros((len(roots), len(roots)), dtype=complex)
    node_map: dict[str, int | None] = {
        node_id: root_index.get(sets.find(node_id)) for node_id in nodes
    }

    def stamp_two_terminal(left: str, right: str, admittance: complex) -> None:
        i, j = node_map[left], node_map[right]
        if i is not None:
            matrix[i, i] += admittance
        if j is not None:
            matrix[j, j] += admittance
        if i is not None and j is not None:
            matrix[i, j] -= admittance
            matrix[j, i] -= admittance

    for edge in graph.connections:
        if not edge.in_service or edge.impedance_ohm == 0j:
            continue
        try:
            y = 1.0 / edge.impedance_ohm
        except ZeroDivisionError as exc:
            raise ValueError(f"Connection {edge.connection_id!r} has invalid zero impedance.") from exc
        if not math.isfinite(y.real) or not math.isfinite(y.imag):
            raise ValueError(f"Connection {edge.connection_id!r} admittance is non-finite.")
        stamp_two_terminal(edge.from_node_id, edge.to_node_id, y)

    expected_branches = {branch.equipment_id for branch in impedances.branches}
    graph_branches = {
        node.equipment_id for node in graph.nodes
        if node.kind is PhaseDomainNodeKind.BRANCH_TERMINAL
    }
    missing_branch_nodes = sorted(expected_branches - graph_branches)
    if missing_branch_nodes:
        raise ValueError(f"Physical branch terminal nodes are missing for: {missing_branch_nodes!r}.")

    for branch in impedances.branches:
        from_nodes: dict[str, str] = {}
        to_nodes: dict[str, str] = {}
        declared_roles = dict(zip(branch.conductor_ids, branch.conductor_roles))
        for conductor_id in branch.matrix_conductor_ids:
            matches_from = [
                node.node_id for node in graph.nodes
                if node.kind is PhaseDomainNodeKind.BRANCH_TERMINAL
                and node.equipment_id == branch.equipment_id
                and node.terminal_role.upper() == "FROM"
                and node.conductor_id == conductor_id
            ]
            matches_to = [
                node.node_id for node in graph.nodes
                if node.kind is PhaseDomainNodeKind.BRANCH_TERMINAL
                and node.equipment_id == branch.equipment_id
                and node.terminal_role.upper() == "TO"
                and node.conductor_id == conductor_id
            ]
            if len(matches_from) != 1 or len(matches_to) != 1:
                raise ValueError(
                    f"Branch {branch.equipment_id!r} requires exactly one FROM and TO graph node "
                    f"for conductor {conductor_id!r}; got {len(matches_from)} and {len(matches_to)}."
                )
            from_node, to_node = nodes[matches_from[0]], nodes[matches_to[0]]
            expected_role = declared_roles[conductor_id]
            if from_node.bus_id != branch.from_bus_id or to_node.bus_id != branch.to_bus_id:
                raise ValueError("Branch terminal graph nodes do not match canonical FROM/TO Bus identities.")
            if from_node.conductor_role != expected_role or to_node.conductor_role != expected_role:
                raise ValueError("Graph conductor role contradicts the owning Core branch inventory.")
            for terminal_node in (from_node, to_node):
                bus_links = [
                    edge for edge in graph.connections
                    if edge.in_service and edge.kind is PhaseDomainConnectionKind.CONTINUITY
                    and terminal_node.node_id in {edge.from_node_id, edge.to_node_id}
                    and nodes[edge.to_node_id if edge.from_node_id == terminal_node.node_id else edge.from_node_id].kind is PhaseDomainNodeKind.BUS_CONDUCTOR
                ]
                if len(bus_links) != 1:
                    raise ValueError(f"Branch terminal node {terminal_node.node_id!r} requires exactly one explicit CONTINUITY connection to a Bus conductor node.")
                edge = bus_links[0]
                other_id = edge.to_node_id if edge.from_node_id == terminal_node.node_id else edge.from_node_id
                bus_node = nodes[other_id]
                # Branch conductor IDs are scoped to their owning
                # Line/Cable. The Bus attachment conductor is a distinct
                # Bus-owned identity; continuity is established by exact
                # Bus attachment provenance and conductor role, not by
                # comparing unrelated owner-local conductor IDs.
                if (bus_node.bus_id, bus_node.conductor_role) != (
                    terminal_node.bus_id, terminal_node.conductor_role
                ):
                    raise ValueError("Branch terminal continuity reaches a contradictory Bus conductor node.")
            from_nodes[conductor_id], to_nodes[conductor_id] = matches_from[0], matches_to[0]

        y_series = np.asarray(branch.series_admittance_pu, dtype=complex) / branch.z_base_ohm
        # Convert the already-prepared per-unit admittance back to SI siemens.
        for row_id in branch.matrix_conductor_ids:
            for col_id in branch.matrix_conductor_ids:
                y = y_series[
                    branch.matrix_conductor_ids.index(row_id),
                    branch.matrix_conductor_ids.index(col_id),
                ]
                i_from, j_from = node_map[from_nodes[row_id]], node_map[from_nodes[col_id]]
                i_to, j_to = node_map[to_nodes[row_id]], node_map[to_nodes[col_id]]
                if i_from is not None and j_from is not None:
                    matrix[i_from, j_from] += y
                if i_to is not None and j_to is not None:
                    matrix[i_to, j_to] += y
                if i_from is not None and j_to is not None:
                    matrix[i_from, j_to] -= y
                if i_to is not None and j_from is not None:
                    matrix[i_to, j_from] -= y

        if branch.shunt_admittance_siemens is not None:
            shunt = np.asarray(branch.shunt_admittance_siemens, dtype=complex)
            for row, row_id in enumerate(branch.matrix_conductor_ids):
                for col, col_id in enumerate(branch.matrix_conductor_ids):
                    half = 0.5 * shunt[row, col]
                    i_from, j_from = node_map[from_nodes[row_id]], node_map[from_nodes[col_id]]
                    i_to, j_to = node_map[to_nodes[row_id]], node_map[to_nodes[col_id]]
                    if i_from is not None and j_from is not None:
                        matrix[i_from, j_from] += half
                    if i_to is not None and j_to is not None:
                        matrix[i_to, j_to] += half

    if not np.all(np.isfinite(matrix.real)) or not np.all(np.isfinite(matrix.imag)):
        raise ValueError("Assembled phase-domain admittance matrix is non-finite.")
    diagnostics: list[str] = []
    if not roots:
        diagnostics.append("No non-earth phase-domain nodes are available.")
    return PhaseDomainAdmittanceSnapshot(
        project_id=graph.project_id,
        activation_generation=graph.activation_generation,
        topology_revision=graph.topology_revision,
        node_ids=roots,
        admittance_siemens=tuple(tuple(complex(x) for x in row) for row in matrix.tolist()),
        source_node_to_index=node_map,
        earth_reference_node_ids=earth_ids,
        branch_ids=tuple(sorted(expected_branches)),
        diagnostics=tuple(diagnostics),
    )


__all__ = ["PhaseDomainAdmittanceSnapshot", "assemble_phase_domain_admittance"]
