"""Explicit-source phase-domain short-circuit execution.

The solver consumes a fully assembled SI-unit conductor admittance matrix.
Sources and fault connections are explicit. Zero-ohm ideal source/fault
constraints use a saddle-point formulation; no epsilon impedance, inferred
earth, or sequence-current substitution is introduced.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from core.analysis.phase_domain_network_preparation import PhaseDomainAdmittanceSnapshot
from core.analysis.physical_conductor_preparation import PhysicalConductorImpedanceSnapshot
from core.network.phase_domain_conductor_network import PhaseDomainConductorNetwork, PhaseDomainNodeKind, PhaseDomainConnectionKind
from .result import ShortCircuitConductorCurrent


def _name(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty.")
    return value.strip()


def _finite_complex(value: complex, field: str) -> complex:
    result = complex(value)
    if not math.isfinite(result.real) or not math.isfinite(result.imag):
        raise ValueError(f"{field} must be finite.")
    return result


@dataclass(frozen=True, slots=True)
class PhaseDomainSourceEquivalent:
    source_id: str
    node_id: str
    internal_voltage_v: complex
    impedance_ohm: complex

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _name(self.source_id, "source_id"))
        object.__setattr__(self, "node_id", _name(self.node_id, "node_id"))
        object.__setattr__(self, "internal_voltage_v", _finite_complex(self.internal_voltage_v, "internal_voltage_v"))
        z = _finite_complex(self.impedance_ohm, "source impedance")
        if z.real < 0.0 or z == 0j:
            raise ValueError("Source impedance must be finite, non-zero, and have non-negative resistance.")
        object.__setattr__(self, "impedance_ohm", z)


@dataclass(frozen=True, slots=True)
class PhaseDomainMultiConductorSource:
    """Explicit coupled Norton source with one impedance matrix for many conductors."""

    source_id: str
    node_ids: tuple[str, ...]
    internal_voltage_v: tuple[complex, ...]
    impedance_matrix_ohm: tuple[tuple[complex, ...], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _name(self.source_id, "source_id"))
        nodes = tuple(_name(x, "source node_id") for x in self.node_ids)
        voltages = tuple(_finite_complex(x, "source internal voltage") for x in self.internal_voltage_v)
        matrix = tuple(tuple(_finite_complex(x, "source impedance matrix") for x in row) for row in self.impedance_matrix_ohm)
        size = len(nodes)
        if not size or len(set(nodes)) != size or len(voltages) != size:
            raise ValueError("Multi-conductor source requires unique nodes and one internal voltage per conductor.")
        if len(matrix) != size or any(len(row) != size for row in matrix):
            raise ValueError("Multi-conductor source impedance matrix must match its node vector.")
        for i in range(size):
            for j in range(size):
                if not math.isclose(matrix[i][j].real, matrix[j][i].real, rel_tol=1e-9, abs_tol=1e-12) or not math.isclose(matrix[i][j].imag, matrix[j][i].imag, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError("Multi-conductor source impedance matrix must be reciprocal.")
        z = np.asarray(matrix, dtype=complex)
        resistance_eigenvalues = np.linalg.eigvalsh((z.real + z.real.T) * 0.5)
        if not np.all(np.isfinite(resistance_eigenvalues)) or float(np.min(resistance_eigenvalues)) <= 1.0e-12:
            raise ValueError("Multi-conductor source resistance matrix must be positive definite.")
        try:
            condition = float(np.linalg.cond(z))
            if not math.isfinite(condition) or condition > 1.0e12:
                raise ValueError("Multi-conductor source impedance matrix is singular or ill-conditioned.")
            np.linalg.inv(z)
        except np.linalg.LinAlgError as exc:
            raise ValueError("Multi-conductor source impedance matrix is singular.") from exc
        object.__setattr__(self, "node_ids", nodes)
        object.__setattr__(self, "internal_voltage_v", voltages)
        object.__setattr__(self, "impedance_matrix_ohm", matrix)


@dataclass(frozen=True, slots=True)
class PhaseDomainGroundedMultiConductorSource:
    """Three phase source with a distinct physical neutral terminal."""
    source_id: str
    phase_node_ids: tuple[str, str, str]
    neutral_node_id: str
    internal_phase_voltage_v: tuple[complex, complex, complex]
    phase_impedance_matrix_ohm: tuple[tuple[complex, ...], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _name(self.source_id, "source_id"))
        phases = tuple(_name(x, "source phase node_id") for x in self.phase_node_ids)
        neutral = _name(self.neutral_node_id, "source neutral node_id")
        voltages = tuple(_finite_complex(x, "source internal phase voltage") for x in self.internal_phase_voltage_v)
        matrix = tuple(tuple(_finite_complex(x, "source phase impedance matrix") for x in row) for row in self.phase_impedance_matrix_ohm)
        if len(phases) != 3 or len(set(phases + (neutral,))) != 4 or len(voltages) != 3:
            raise ValueError("Grounded source requires unique A/B/C and neutral nodes and three phase voltages.")
        if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
            raise ValueError("Grounded source phase impedance matrix must be 3x3.")
        for i in range(3):
            for j in range(3):
                if not math.isclose(matrix[i][j].real, matrix[j][i].real, rel_tol=1e-9, abs_tol=1e-12) or not math.isclose(matrix[i][j].imag, matrix[j][i].imag, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError("Grounded source phase impedance matrix must be reciprocal.")
        z = np.asarray(matrix, dtype=complex)
        eigenvalues = np.linalg.eigvalsh((z.real + z.real.T) * 0.5)
        if not np.all(np.isfinite(eigenvalues)) or float(np.min(eigenvalues)) <= 1e-12:
            raise ValueError("Grounded source phase resistance matrix must be positive definite.")
        if not math.isfinite(float(np.linalg.cond(z))) or float(np.linalg.cond(z)) > 1e12:
            raise ValueError("Grounded source phase impedance matrix is singular or ill-conditioned.")
        object.__setattr__(self, "phase_node_ids", phases)
        object.__setattr__(self, "neutral_node_id", neutral)
        object.__setattr__(self, "internal_phase_voltage_v", voltages)
        object.__setattr__(self, "phase_impedance_matrix_ohm", matrix)

    @property
    def node_ids(self) -> tuple[str, ...]:
        return self.phase_node_ids + (self.neutral_node_id,)

@dataclass(frozen=True, slots=True)
class PhaseDomainTransformerMultiport:
    """Reciprocal passive transformer terminal admittance multiport in SI units.

    The supplied matrix must already encode winding incidence, turns ratio,
    phase displacement, leakage, and any included magnetizing/core branches.
    The solver does not infer these from scalar transformer r/x fields.
    """
    transformer_id: str
    node_ids: tuple[str, ...]
    terminal_labels: tuple[str, ...]
    admittance_siemens: tuple[tuple[complex, ...], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "transformer_id", _name(self.transformer_id, "transformer_id"))
        nodes = tuple(_name(x, "transformer terminal node_id") for x in self.node_ids)
        labels = tuple(_name(x, "transformer terminal label") for x in self.terminal_labels)
        matrix = tuple(tuple(_finite_complex(x, "transformer terminal admittance") for x in row) for row in self.admittance_siemens)
        size = len(nodes)
        if size < 6 or len(set(nodes)) != size or len(labels) != size or len(set(labels)) != size:
            raise ValueError("Transformer multiport requires at least six unique nodes and labels in matching order.")
        if len(matrix) != size or any(len(row) != size for row in matrix):
            raise ValueError("Transformer terminal admittance matrix must be square and match node_ids.")
        values = np.asarray(matrix, dtype=complex)
        if not np.allclose(values, values.T, rtol=1e-9, atol=1e-12):
            raise ValueError("Transformer terminal admittance matrix must be reciprocal (complex symmetric).")
        conductance = (values.real + values.real.T) * 0.5
        eigenvalues = np.linalg.eigvalsh(conductance)
        scale = max(1.0, float(np.max(np.abs(eigenvalues))))
        if not np.all(np.isfinite(eigenvalues)) or float(np.min(eigenvalues)) < -1e-10 * scale:
            raise ValueError("Transformer terminal conductance matrix must be positive semidefinite.")
        object.__setattr__(self, "node_ids", nodes)
        object.__setattr__(self, "terminal_labels", labels)
        object.__setattr__(self, "admittance_siemens", matrix)


@dataclass(frozen=True, slots=True)
class PhaseDomainFaultConnection:
    connection_id: str
    from_node_id: str
    to_node_id: str
    impedance_ohm: complex = 0j

    def __post_init__(self) -> None:
        for field in ("connection_id", "from_node_id", "to_node_id"):
            object.__setattr__(self, field, _name(getattr(self, field), field))
        if self.from_node_id == self.to_node_id:
            raise ValueError("Fault connection must join distinct nodes.")
        z = _finite_complex(self.impedance_ohm, "fault impedance")
        if z.real < 0.0:
            raise ValueError("Fault resistance cannot be negative.")
        object.__setattr__(self, "impedance_ohm", z)


@dataclass(frozen=True, slots=True)
class PhaseDomainShortCircuitCase:
    graph: PhaseDomainConductorNetwork
    admittance: PhaseDomainAdmittanceSnapshot
    impedances: PhysicalConductorImpedanceSnapshot
    sources: tuple[PhaseDomainSourceEquivalent | PhaseDomainMultiConductorSource | PhaseDomainGroundedMultiConductorSource, ...]
    faults: tuple[PhaseDomainFaultConnection, ...]
    base_mva: float
    transformer_primitives: tuple[PhaseDomainTransformerMultiport, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.graph, PhaseDomainConductorNetwork):
            raise TypeError("graph must be PhaseDomainConductorNetwork.")
        if not isinstance(self.admittance, PhaseDomainAdmittanceSnapshot):
            raise TypeError("admittance must be PhaseDomainAdmittanceSnapshot.")
        if not isinstance(self.impedances, PhysicalConductorImpedanceSnapshot):
            raise TypeError("impedances must be PhysicalConductorImpedanceSnapshot.")
        provenance = (self.graph.project_id, self.graph.activation_generation, self.graph.topology_revision)
        if provenance != (self.admittance.project_id, self.admittance.activation_generation, self.admittance.topology_revision):
            raise ValueError("Phase-domain graph and admittance provenance mismatch.")
        if provenance != (self.impedances.project_id, self.impedances.activation_generation, self.impedances.topology_revision):
            raise ValueError("Phase-domain graph and impedance provenance mismatch.")
        from core.analysis.phase_domain_network_preparation import assemble_phase_domain_admittance
        rebuilt_admittance = assemble_phase_domain_admittance(self.graph, self.impedances)
        if rebuilt_admittance != self.admittance:
            raise ValueError("Phase-domain admittance does not match its authoritative graph and physical impedance snapshot.")
        sources, faults = tuple(self.sources), tuple(self.faults)
        transformer_primitives = tuple(self.transformer_primitives)
        if any(not isinstance(x, PhaseDomainTransformerMultiport) for x in transformer_primitives):
            raise TypeError("transformer_primitives must contain PhaseDomainTransformerMultiport records.")
        if len({x.transformer_id for x in transformer_primitives}) != len(transformer_primitives):
            raise ValueError("Duplicate transformer multiport identity.")
        known_nodes = set(self.graph.node_index)
        for primitive in transformer_primitives:
            if any(node_id not in known_nodes for node_id in primitive.node_ids):
                raise ValueError(f"Transformer {primitive.transformer_id!r} references an unknown graph node.")
            terminal_nodes = tuple(self.graph.node(node_id) for node_id in primitive.node_ids)
            if any(node.kind is not PhaseDomainNodeKind.EQUIPMENT_TERMINAL or node.equipment_id != primitive.transformer_id for node in terminal_nodes):
                raise ValueError(f"Transformer {primitive.transformer_id!r} multiport nodes must be its own equipment-terminal nodes.")
            if len({(node.terminal_role.casefold(), node.conductor_role) for node in terminal_nodes}) != len(terminal_nodes):
                raise ValueError(f"Transformer {primitive.transformer_id!r} contains duplicate terminal/conductor mappings.")
        if not sources:
            raise ValueError("Phase-domain short-circuit case requires explicit source equivalents.")
        if not faults:
            raise ValueError("Phase-domain short-circuit case requires explicit fault connections.")
        if any(not isinstance(x, (PhaseDomainSourceEquivalent, PhaseDomainMultiConductorSource, PhaseDomainGroundedMultiConductorSource)) for x in sources):
            raise TypeError("sources must contain explicit scalar or multi-conductor source equivalents.")
        if any(not isinstance(x, PhaseDomainFaultConnection) for x in faults):
            raise TypeError("faults must contain PhaseDomainFaultConnection records.")
        if len({x.source_id for x in sources}) != len(sources):
            raise ValueError("Duplicate phase-domain source identity.")
        if len({x.connection_id for x in faults}) != len(faults):
            raise ValueError("Duplicate phase-domain fault connection identity.")
        base = float(self.base_mva)
        if not math.isfinite(base) or base <= 0.0:
            raise ValueError("base_mva must be finite and positive.")
        if not self.impedances.branches:
            raise ValueError("Phase-domain short-circuit case requires at least one prepared physical conductor branch.")
        if not math.isclose(base, self.impedances.base_mva, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("Phase-domain case base_mva does not match its physical conductor impedance snapshot.")
        branch_ids = {item.equipment_id for item in self.impedances.branches}
        connection_ids = {item.connection_id for item in self.graph.connections}
        collisions = branch_ids & connection_ids
        if collisions:
            raise ValueError(f"Phase-domain connection IDs collide with branch equipment IDs: {sorted(collisions)!r}.")
        known = set(self.graph.node_index)
        for item in sources:
            source_nodes = (item.node_id,) if isinstance(item, PhaseDomainSourceEquivalent) else item.node_ids
            for node_id in source_nodes:
                if node_id not in known or self.graph.node(node_id).kind in {
                    PhaseDomainNodeKind.EARTH_NODE,
                    PhaseDomainNodeKind.EARTH_REFERENCE,
                    PhaseDomainNodeKind.FAULT_NODE,
                }:
                    raise ValueError(f"Source {item.source_id!r} references an invalid, earth-reference, or fault-star node.")
            source_terminals = tuple(self.graph.node(node_id) for node_id in source_nodes)
            if any(node.kind is not PhaseDomainNodeKind.EQUIPMENT_TERMINAL for node in source_terminals):
                raise ValueError(
                    f"Source {item.source_id!r} must inject at explicitly modeled equipment-terminal nodes; "
                    "direct Bus-conductor injection is not accepted as an equipment source."
                )
            equipment_ids = {node.equipment_id for node in source_terminals}
            if len(equipment_ids) != 1:
                raise ValueError(f"Multi-conductor source {item.source_id!r} spans multiple equipment identities.")
            equipment_id = next(iter(equipment_ids))
            if item.source_id != equipment_id:
                raise ValueError(
                    f"Phase-domain source identity {item.source_id!r} must equal its canonical equipment owner "
                    f"identity {equipment_id!r}; source_reference metadata cannot alias equipment ownership."
                )
            if any(node.source_reference not in (None, item.source_id) for node in source_terminals):
                raise ValueError(
                    f"Phase-domain source {item.source_id!r} contains conflicting source_reference metadata."
                )
            roles = [node.conductor_role for node in source_terminals]
            if len(set(roles)) != len(roles):
                raise ValueError(f"Source {item.source_id!r} contains duplicate physical conductor roles.")
            if isinstance(item, PhaseDomainGroundedMultiConductorSource) and roles != ["A", "B", "C", "N"]:
                raise ValueError(f"Grounded source {item.source_id!r} node order must be exactly A, B, C, N.")
        for item in faults:
            if item.from_node_id not in known or item.to_node_id not in known:
                raise ValueError(f"Fault {item.connection_id!r} references an unknown graph node.")
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "faults", faults)
        object.__setattr__(self, "transformer_primitives", transformer_primitives)
        object.__setattr__(self, "base_mva", base)


@dataclass(frozen=True, slots=True)
class PhaseDomainShortCircuitSolution:
    node_voltages_v: Mapping[str, complex]
    conductor_currents: Mapping[str, ShortCircuitConductorCurrent]
    source_currents_a: Mapping[str, Any]
    fault_currents_a: Mapping[str, complex]
    connection_currents_a: Mapping[str, complex]
    topology_revision: int
    source_return_reconciliation: Mapping[str, Mapping[str, Any]] | None = None
    kcl_residual_a: float = 0.0
    diagnostics: tuple[str, ...] = ()
    transformer_terminal_currents_a: Mapping[str, Mapping[str, complex]] | None = None

    def __post_init__(self) -> None:
        residual = float(self.kcl_residual_a)
        if not math.isfinite(residual) or residual < 0.0:
            raise ValueError("kcl_residual_a must be finite and non-negative.")
        object.__setattr__(self, "kcl_residual_a", residual)
        object.__setattr__(self, "node_voltages_v", MappingProxyType(dict(self.node_voltages_v)))
        object.__setattr__(self, "conductor_currents", MappingProxyType(dict(self.conductor_currents)))
        object.__setattr__(self, "source_currents_a", MappingProxyType(dict(self.source_currents_a)))
        object.__setattr__(self, "fault_currents_a", MappingProxyType(dict(self.fault_currents_a)))
        object.__setattr__(self, "connection_currents_a", MappingProxyType(dict(self.connection_currents_a)))
        reconciliation = self.source_return_reconciliation or {}
        object.__setattr__(self, "source_return_reconciliation", MappingProxyType({key: MappingProxyType(dict(value)) for key, value in reconciliation.items()}))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        transformer_currents = self.transformer_terminal_currents_a or {}
        object.__setattr__(self, "transformer_terminal_currents_a", MappingProxyType({key: MappingProxyType(dict(value)) for key, value in transformer_currents.items()}))


def _reconcile_source_returns(case: PhaseDomainShortCircuitCase, source_currents: Mapping[str, Any], connection_currents: Mapping[str, complex]) -> dict[str, dict[str, Any]]:
    """Validate source-neutral/electrode equality and local earth-node KCL."""
    results: dict[str, dict[str, Any]] = {}
    scale = max((abs(value) for value in connection_currents.values()), default=0.0)
    tolerance = 1.0e-8 * max(scale, 1.0e-9)
    for source in case.sources:
        if not isinstance(source, PhaseDomainGroundedMultiConductorSource):
            continue
        neutral_current = complex(source_currents[source.source_id][3])
        edges = [edge for edge in case.graph.connections if edge.in_service and edge.kind is PhaseDomainConnectionKind.GROUND_ELECTRODE and edge.source_reference == source.source_id and source.neutral_node_id in {edge.from_node_id, edge.to_node_id}]
        if len(edges) != 1:
            raise ValueError(f"Source {source.source_id!r} requires exactly one source-neutral electrode.")
        edge = edges[0]
        if edge.impedance_ohm == 0j or edge.connection_id not in connection_currents:
            raise ValueError(f"Source {source.source_id!r} has an ideal or unresolved neutral electrode current.")
        edge_current = connection_currents[edge.connection_id]
        leaving_neutral = edge_current if edge.from_node_id == source.neutral_node_id else -edge_current
        residual = abs(neutral_current - leaving_neutral)
        if residual > tolerance:
            raise ValueError(f"Source {source.source_id!r} neutral/electrode current mismatch: {residual:.9g} A.")
        results[source.source_id] = {"status": "RECONCILED", "neutral_current_a": neutral_current, "electrode_connection_id": edge.connection_id, "electrode_current_leaving_neutral_a": leaving_neutral, "residual_a": residual, "tolerance_a": tolerance}
    for node in (item for item in case.graph.nodes if item.kind is PhaseDomainNodeKind.EARTH_NODE):
        edges = [edge for edge in case.graph.connections if edge.in_service and node.node_id in {edge.from_node_id, edge.to_node_id}]
        if not edges:
            continue
        if any(edge.impedance_ohm == 0j or edge.connection_id not in connection_currents for edge in edges):
            raise ValueError(f"Earth node {node.node_id!r} contains an ideal or unresolved path; current division is indeterminate.")
        net = sum(connection_currents[edge.connection_id] if edge.from_node_id == node.node_id else -connection_currents[edge.connection_id] for edge in edges)
        residual = abs(net)
        if residual > tolerance:
            raise ValueError(f"Earth node {node.node_id!r} violates current continuity: {residual:.9g} A.")
        results[f"EARTH_NODE:{node.node_id}"] = {"status": "RECONCILED", "net_outgoing_current_a": net, "residual_a": residual, "tolerance_a": tolerance, "incident_connection_ids": tuple(edge.connection_id for edge in edges)}
    return results

class PhaseDomainShortCircuitSolver:
    """Solve one phase-domain fault using explicit source and fault primitives."""

    def solve(self, case: PhaseDomainShortCircuitCase) -> PhaseDomainShortCircuitSolution:
        if not isinstance(case, PhaseDomainShortCircuitCase):
            raise TypeError("case must be PhaseDomainShortCircuitCase.")
        snapshot = case.admittance
        ids = snapshot.node_ids
        y = np.asarray(snapshot.admittance_siemens, dtype=complex).copy()
        rhs = np.zeros(len(ids), dtype=complex)
        constraints: list[np.ndarray] = []
        constraint_values: list[complex] = []

        for source in case.sources:
            if isinstance(source, PhaseDomainSourceEquivalent):
                i = snapshot.source_node_to_index[source.node_id]
                if i is None:
                    raise ValueError(f"Source {source.source_id!r} is connected to the fixed earth reference.")
                admittance = 1.0 / source.impedance_ohm
                y[i, i] += admittance
                rhs[i] += source.internal_voltage_v * admittance
            elif isinstance(source, PhaseDomainGroundedMultiConductorSource):
                indices = [snapshot.source_node_to_index[node_id] for node_id in source.node_ids]
                if any(index is None for index in indices) or len(set(indices)) != 4:
                    raise ValueError(f"Grounded source {source.source_id!r} has fixed-earth or ideally contracted terminals.")
                incidence = np.zeros((3, 4), dtype=complex)
                incidence[0, 0], incidence[0, 3] = 1.0, -1.0
                incidence[1, 1], incidence[1, 3] = 1.0, -1.0
                incidence[2, 2], incidence[2, 3] = 1.0, -1.0
                phase_y = np.linalg.inv(np.asarray(source.phase_impedance_matrix_ohm, dtype=complex))
                source_y = incidence.conjugate().T @ phase_y @ incidence
                source_rhs = incidence.conjugate().T @ phase_y @ np.asarray(source.internal_phase_voltage_v, dtype=complex)
                for row, global_row in enumerate(indices):
                    rhs[global_row] += source_rhs[row]
                    for column, global_column in enumerate(indices):
                        y[global_row, global_column] += source_y[row, column]
            else:
                indices = [snapshot.source_node_to_index[node_id] for node_id in source.node_ids]
                if any(index is None for index in indices):
                    raise ValueError(f"Multi-conductor source {source.source_id!r} is connected to a fixed earth node.")
                if len(set(indices)) != len(indices):
                    raise ValueError(f"Multi-conductor source {source.source_id!r} has terminals contracted by an ideal conductor bond.")
                source_y = np.linalg.inv(np.asarray(source.impedance_matrix_ohm, dtype=complex))
                source_rhs = source_y @ np.asarray(source.internal_voltage_v, dtype=complex)
                for row, global_row in enumerate(indices):
                    rhs[global_row] += source_rhs[row]
                    for column, global_column in enumerate(indices):
                        y[global_row, global_column] += source_y[row, column]

        # Stamp explicit reciprocal transformer terminal-domain primitives.
        for primitive in case.transformer_primitives:
            indices = [snapshot.source_node_to_index[node_id] for node_id in primitive.node_ids]
            if any(index is None for index in indices) or len(set(indices)) != len(indices):
                raise ValueError(f"Transformer {primitive.transformer_id!r} has fixed-earth or contracted multiport terminals.")
            block = np.asarray(primitive.admittance_siemens, dtype=complex)
            for row, global_row in enumerate(indices):
                for column, global_column in enumerate(indices):
                    y[global_row, global_column] += block[row, column]

        for fault in case.faults:
            i = snapshot.source_node_to_index[fault.from_node_id]
            j = snapshot.source_node_to_index[fault.to_node_id]
            if fault.impedance_ohm == 0j:
                row = np.zeros(len(ids), dtype=complex)
                if i is not None:
                    row[i] += 1.0
                if j is not None:
                    row[j] -= 1.0
                if not np.any(row):
                    raise ValueError(f"Fault {fault.connection_id!r} collapses only fixed earth nodes.")
                constraints.append(row)
                constraint_values.append(0j)
            else:
                admittance = 1.0 / fault.impedance_ohm
                if i is not None:
                    y[i, i] += admittance
                if j is not None:
                    y[j, j] += admittance
                if i is not None and j is not None:
                    y[i, j] -= admittance
                    y[j, i] -= admittance

        multipliers = np.zeros(0, dtype=complex)
        constraint_reaction = np.zeros(len(ids), dtype=complex)
        if constraints:
            c = np.vstack(constraints)
            saddle = np.block([
                [y, c.conjugate().T],
                [c, np.zeros((len(constraints), len(constraints)), dtype=complex)],
            ])
            augmented_rhs = np.concatenate((rhs, np.asarray(constraint_values, dtype=complex)))
            augmented_solution = np.linalg.solve(saddle, augmented_rhs)
            solution = augmented_solution[:len(ids)]
            multipliers = augmented_solution[len(ids):]
            constraint_reaction = c.conjugate().T @ multipliers
        else:
            solution = np.linalg.solve(y, rhs)
        if (
            not np.all(np.isfinite(solution.real))
            or not np.all(np.isfinite(solution.imag))
            or not np.all(np.isfinite(multipliers.real))
            or not np.all(np.isfinite(multipliers.imag))
        ):
            raise ValueError("Phase-domain fault solution contains non-finite voltages or ideal-constraint currents.")
        # Verify KCL on every solved (non-reference) node. The saddle-point
        # reaction term is the exact current through ideal fault constraints.
        network_injection = y @ solution
        residual_vector = network_injection + constraint_reaction - rhs
        kcl_residual_a = float(np.max(np.abs(residual_vector)))
        residual_scale = max(
            1.0,
            float(np.max(np.abs(rhs))),
            float(np.max(np.abs(network_injection))),
            float(np.max(np.abs(constraint_reaction))),
        )
        if not math.isfinite(kcl_residual_a) or kcl_residual_a > 1.0e-8 * residual_scale:
            raise ValueError(
                f"Phase-domain solution violates nodal KCL: residual={kcl_residual_a:.6g} A, "
                f"scale={residual_scale:.6g} A."
            )
        voltage_by_node = {
            node_id: (0j if mapped is None else complex(solution[mapped]))
            for node_id, mapped in snapshot.source_node_to_index.items()
        }

        source_currents = {}
        for source in case.sources:
            if isinstance(source, PhaseDomainSourceEquivalent):
                source_currents[source.source_id] = (source.internal_voltage_v - voltage_by_node[source.node_id]) / source.impedance_ohm
            elif isinstance(source, PhaseDomainGroundedMultiConductorSource):
                incidence = np.zeros((3, 4), dtype=complex)
                incidence[0, 0], incidence[0, 3] = 1.0, -1.0
                incidence[1, 1], incidence[1, 3] = 1.0, -1.0
                incidence[2, 2], incidence[2, 3] = 1.0, -1.0
                solved_voltage = np.asarray([voltage_by_node[node_id] for node_id in source.node_ids], dtype=complex)
                phase_current = np.linalg.solve(np.asarray(source.phase_impedance_matrix_ohm, dtype=complex), np.asarray(source.internal_phase_voltage_v, dtype=complex) - incidence @ solved_voltage)
                source_currents[source.source_id] = tuple(complex(value) for value in phase_current.tolist()) + (-complex(np.sum(phase_current)),)
            else:
                source_voltage = np.asarray(source.internal_voltage_v, dtype=complex)
                solved_voltage = np.asarray([voltage_by_node[node_id] for node_id in source.node_ids], dtype=complex)
                source_current = np.linalg.solve(np.asarray(source.impedance_matrix_ohm, dtype=complex), source_voltage - solved_voltage)
                source_currents[source.source_id] = tuple(complex(value) for value in source_current.tolist())
        fault_currents: dict[str, complex] = {}
        for fault in case.faults:
            delta = voltage_by_node[fault.from_node_id] - voltage_by_node[fault.to_node_id]
            if fault.impedance_ohm == 0j:
                # The Lagrange multiplier is the exact ideal-constraint current.
                # It is populated below from the saddle-point multiplier.
                fault_currents[fault.connection_id] = 0j
            else:
                fault_currents[fault.connection_id] = delta / fault.impedance_ohm

        # Lagrange multipliers are the exact currents through bolted-fault constraints.
        if constraints:
            zero_fault_ids = [x.connection_id for x in case.faults if x.impedance_ohm == 0j]
            for fault_id, current in zip(zero_fault_ids, multipliers):
                fault_currents[fault_id] = complex(current)

        connection_currents: dict[str, complex] = {}
        connection_diagnostics: list[str] = []
        for edge in case.graph.connections:
            if not edge.in_service:
                continue
            if edge.impedance_ohm == 0j:
                connection_diagnostics.append(
                    f"Connection {edge.connection_id!r} is an ideal zero-ohm bond; its individual current is indeterminate in an ideal parallel network."
                )
                continue
            delta = voltage_by_node[edge.from_node_id] - voltage_by_node[edge.to_node_id]
            connection_currents[edge.connection_id] = delta / edge.impedance_ohm

        source_return_reconciliation = _reconcile_source_returns(case, source_currents, connection_currents)

        conductor_records: dict[str, ShortCircuitConductorCurrent] = {}
        for branch in case.impedances.branches:
            order = branch.matrix_conductor_ids
            from_nodes = {}
            to_nodes = {}
            for conductor_id in order:
                f = [
                    node for node in case.graph.nodes
                    if node.kind is PhaseDomainNodeKind.BRANCH_TERMINAL
                    and node.equipment_id == branch.equipment_id
                    and node.terminal_role.upper() == "FROM"
                    and node.conductor_id == conductor_id
                ]
                t = [
                    node for node in case.graph.nodes
                    if node.kind is PhaseDomainNodeKind.BRANCH_TERMINAL
                    and node.equipment_id == branch.equipment_id
                    and node.terminal_role.upper() == "TO"
                    and node.conductor_id == conductor_id
                ]
                if len(f) != 1 or len(t) != 1:
                    raise ValueError(f"Branch {branch.equipment_id!r} has incomplete terminal-node mapping for {conductor_id!r}.")
                from_nodes[conductor_id], to_nodes[conductor_id] = f[0], t[0]
            vf = np.asarray([voltage_by_node[from_nodes[x].node_id] for x in order], dtype=complex)
            vt = np.asarray([voltage_by_node[to_nodes[x].node_id] for x in order], dtype=complex)
            z = np.asarray(branch.series_impedance_ohm, dtype=complex)
            series = np.linalg.solve(z, vf - vt)
            from_current = series.copy()
            to_current = -series.copy()
            if branch.shunt_admittance_siemens is not None:
                shunt = np.asarray(branch.shunt_admittance_siemens, dtype=complex)
                from_current += 0.5 * shunt @ vf
                to_current += 0.5 * shunt @ vt
            conductor_by_id = {
                node.conductor_id: node for node in case.graph.nodes
                if node.kind is PhaseDomainNodeKind.BRANCH_TERMINAL and node.equipment_id == branch.equipment_id
            }
            for side, terminal_nodes, vector in (
                ("FROM", from_nodes, from_current),
                ("TO", to_nodes, to_current),
            ):
                for conductor_id, current_a in zip(order, vector):
                    node = terminal_nodes[conductor_id]
                    role = node.conductor_role
                    if node.bus_id is None:
                        raise ValueError(f"Branch terminal node {node.node_id!r} requires bus_id for result provenance.")
                    current_base_a = case.base_mva * 1e6 / (math.sqrt(3.0) * branch.base_voltage_kv * 1e3)
                    current_pu = current_a / current_base_a
                    record = ShortCircuitConductorCurrent(
                        conductor_id=conductor_id,
                        equipment_id=branch.equipment_id,
                        equipment_type=branch.equipment_type,
                        terminal_role=side,
                        bus_id=node.bus_id,
                        phase_or_sequence=role,
                        current=current_pu,
                        topology_revision=case.graph.topology_revision,
                        base_mva=case.base_mva,
                        voltage_base_kv=branch.base_voltage_kv,
                        reference_direction="INTO_EQUIPMENT",
                        current_units="per_unit",
                        provenance={
                            "domain": "PHASE_DOMAIN",
                            "current_a": complex(current_a),
                            "conductor_role": role,
                            "physical_node_id": node.node_id,
                            "branch_matrix_order": order,
                            "project_id": case.graph.project_id,
                            "activation_generation": case.graph.activation_generation,
                        },
                    )
                    conductor_records[record.record_id] = record
        # Emit signed currents at explicitly modeled equipment terminals as well
        # as at Line/Cable branch terminals. An equipment-terminal current is
        # defined only when every incident physical path has a finite, known
        # impedance; ideal-bond current division is not fabricated.
        for node in case.graph.nodes:
            if node.kind is not PhaseDomainNodeKind.EQUIPMENT_TERMINAL:
                continue
            if not node.bus_id:
                connection_diagnostics.append(
                    f"Equipment terminal {node.equipment_id}:{node.terminal_role}:{node.conductor_id} "
                    "has no explicit Bus voltage-base reference; terminal current omitted."
                )
                continue
            incident = [
                edge for edge in case.graph.connections
                if edge.in_service and node.node_id in {edge.from_node_id, edge.to_node_id}
            ]
            if len(incident) != 1 or incident[0].impedance_ohm == 0j:
                connection_diagnostics.append(
                    f"Equipment terminal {node.equipment_id}:{node.terminal_role}:{node.conductor_id} "
                    "does not have exactly one finite-impedance terminal-current cut; "
                    "multi-path or ideal-bond current division is not inferred."
                )
                continue
            base_candidates = {
                branch.base_voltage_kv for branch in case.impedances.branches
                if node.bus_id in {branch.from_bus_id, branch.to_bus_id}
            }
            if len(base_candidates) != 1:
                connection_diagnostics.append(
                    f"Equipment terminal {node.equipment_id}:{node.terminal_role}:{node.conductor_id} "
                    "has no unique voltage base; terminal current omitted."
                )
                continue
            current_into_terminal_a = 0j
            for edge in incident:
                edge_current = connection_currents[edge.connection_id]
                current_into_terminal_a += (
                    edge_current if edge.to_node_id == node.node_id else -edge_current
                )
            voltage_base_kv = next(iter(base_candidates))
            current_base_a = case.base_mva * 1e6 / (math.sqrt(3.0) * voltage_base_kv * 1e3)
            record = ShortCircuitConductorCurrent(
                conductor_id=node.conductor_id,
                equipment_id=node.equipment_id,
                equipment_type="EQUIPMENT_TERMINAL",
                terminal_role=node.terminal_role,
                bus_id=node.bus_id,
                phase_or_sequence=node.conductor_role,
                current=current_into_terminal_a / current_base_a,
                topology_revision=case.graph.topology_revision,
                base_mva=case.base_mva,
                voltage_base_kv=voltage_base_kv,
                reference_direction="INTO_EQUIPMENT",
                current_units="per_unit",
                provenance={
                    "domain": "PHASE_DOMAIN_EQUIPMENT_TERMINAL",
                    "current_a": complex(current_into_terminal_a),
                    "conductor_role": node.conductor_role,
                    "physical_node_id": node.node_id,
                    "incident_connection_ids": tuple(edge.connection_id for edge in incident),
                    "project_id": case.graph.project_id,
                    "activation_generation": case.graph.activation_generation,
                },
            )
            conductor_records[record.record_id] = record

        for edge in case.graph.connections:
            if not edge.in_service or edge.impedance_ohm == 0j:
                continue
            current_a = connection_currents[edge.connection_id]
            for side, node_id, signed_current in (
                ("FROM", edge.from_node_id, current_a),
                ("TO", edge.to_node_id, -current_a),
            ):
                node = case.graph.node(node_id)
                if node.kind in {PhaseDomainNodeKind.EARTH_NODE, PhaseDomainNodeKind.EARTH_REFERENCE}:
                    continue
                if node.conductor_id is None or node.bus_id is None:
                    connection_diagnostics.append(
                        f"Connection {edge.connection_id!r} endpoint {node_id!r} lacks conductor or Bus identity; terminal current record omitted."
                    )
                    continue
                base_candidates = {
                    branch.base_voltage_kv for branch in case.impedances.branches
                    if node.bus_id in {branch.from_bus_id, branch.to_bus_id}
                }
                if len(base_candidates) != 1:
                    connection_diagnostics.append(
                        f"Connection {edge.connection_id!r} endpoint {node_id!r} has no unique voltage base; terminal current record omitted."
                    )
                    continue
                voltage_base_kv = next(iter(base_candidates))
                current_base_a = case.base_mva * 1e6 / (math.sqrt(3.0) * voltage_base_kv * 1e3)
                record = ShortCircuitConductorCurrent(
                    conductor_id=node.conductor_id,
                    equipment_id=edge.connection_id,
                    equipment_type=edge.kind.value,
                    terminal_role=side,
                    bus_id=node.bus_id,
                    phase_or_sequence=node.conductor_role,
                    current=signed_current / current_base_a,
                    topology_revision=case.graph.topology_revision,
                    base_mva=case.base_mva,
                    voltage_base_kv=voltage_base_kv,
                    reference_direction="INTO_EQUIPMENT",
                    current_units="per_unit",
                    provenance={
                        "domain": "PHASE_DOMAIN_CONNECTION",
                        "connection_kind": edge.kind.value,
                        "physical_node_id": node.node_id,
                        "connection_impedance_ohm": edge.impedance_ohm,
                        "current_a": complex(signed_current),
                        "project_id": case.graph.project_id,
                        "activation_generation": case.graph.activation_generation,
                    },
                )
                conductor_records[record.record_id] = record

        transformer_terminal_currents = {}
        for primitive in case.transformer_primitives:
            terminal_voltages = np.asarray([voltage_by_node[node_id] for node_id in primitive.node_ids], dtype=complex)
            terminal_currents = np.asarray(primitive.admittance_siemens, dtype=complex) @ terminal_voltages
            transformer_terminal_currents[primitive.transformer_id] = {
                label: complex(current) for label, current in zip(primitive.terminal_labels, terminal_currents)
            }

        # A grounded winding's neutral port current must balance its
        # physical neutral electrode current. Earth-node KCL alone cannot
        # prove that the multiport and grounding branch agree at the port.
        return_scale = max(
            (abs(value) for value in connection_currents.values()),
            default=0.0,
        )
        return_tolerance = 1.0e-8 * max(return_scale, 1.0e-9)
        for primitive in case.transformer_primitives:
            terminal_map = transformer_terminal_currents[primitive.transformer_id]
            for label, terminal_current in terminal_map.items():
                if not label.endswith(":N"):
                    continue
                neutral_node = next(
                    node_id for node_id, node_label in zip(primitive.node_ids, primitive.terminal_labels)
                    if node_label == label
                )
                edges = tuple(
                    edge for edge in case.graph.connections
                    if edge.in_service
                    and edge.kind is PhaseDomainConnectionKind.GROUND_ELECTRODE
                    and edge.source_reference == primitive.transformer_id
                    and neutral_node in {edge.from_node_id, edge.to_node_id}
                )
                if len(edges) != 1:
                    raise ValueError(
                        f"Transformer {primitive.transformer_id!r} neutral port {label!r} "
                        "requires exactly one physical grounding electrode."
                    )
                edge = edges[0]
                if edge.impedance_ohm == 0j or edge.connection_id not in connection_currents:
                    raise ValueError(
                        f"Transformer {primitive.transformer_id!r} neutral port {label!r} "
                        "has an ideal or unresolved electrode current."
                    )
                edge_current = connection_currents[edge.connection_id]
                leaving_neutral = edge_current if edge.from_node_id == neutral_node else -edge_current
                residual = abs(complex(terminal_current) + leaving_neutral)
                if residual > return_tolerance:
                    raise ValueError(
                        f"Transformer {primitive.transformer_id!r} neutral/electrode current "
                        f"mismatch at {label!r}: {residual:.9g} A."
                    )
                source_return_reconciliation[
                    f"TRANSFORMER:{primitive.transformer_id}:{label}"
                ] = {
                    "status": "RECONCILED",
                    "terminal_current_into_transformer_a": complex(terminal_current),
                    "electrode_current_leaving_neutral_a": leaving_neutral,
                    "electrode_connection_id": edge.connection_id,
                    "residual_a": residual,
                    "tolerance_a": return_tolerance,
                }

        return PhaseDomainShortCircuitSolution(
            node_voltages_v=voltage_by_node,
            conductor_currents=conductor_records,
            source_currents_a=source_currents,
            fault_currents_a=fault_currents,
            connection_currents_a=connection_currents,
            topology_revision=case.graph.topology_revision,
            source_return_reconciliation=source_return_reconciliation,
            kcl_residual_a=kcl_residual_a,
            diagnostics=tuple(connection_diagnostics),
            transformer_terminal_currents_a=transformer_terminal_currents,
        )


__all__ = [
    "PhaseDomainSourceEquivalent",
    "PhaseDomainMultiConductorSource",
    "PhaseDomainGroundedMultiConductorSource",
    "PhaseDomainFaultConnection",
    "PhaseDomainTransformerMultiport",
    "PhaseDomainShortCircuitCase",
    "PhaseDomainShortCircuitSolution",
    "PhaseDomainShortCircuitSolver",
]
