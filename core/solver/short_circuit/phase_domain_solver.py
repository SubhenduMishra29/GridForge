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
from typing import Mapping

import numpy as np

from core.analysis.phase_domain_network_preparation import PhaseDomainAdmittanceSnapshot
from core.analysis.physical_conductor_preparation import PhysicalConductorImpedanceSnapshot
from core.network.phase_domain_conductor_network import PhaseDomainConductorNetwork, PhaseDomainNodeKind
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
    sources: tuple[PhaseDomainSourceEquivalent | PhaseDomainMultiConductorSource, ...]
    faults: tuple[PhaseDomainFaultConnection, ...]
    base_mva: float

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
        sources, faults = tuple(self.sources), tuple(self.faults)
        if not sources:
            raise ValueError("Phase-domain short-circuit case requires explicit source equivalents.")
        if not faults:
            raise ValueError("Phase-domain short-circuit case requires explicit fault connections.")
        if any(not isinstance(x, (PhaseDomainSourceEquivalent, PhaseDomainMultiConductorSource)) for x in sources):
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
        known = set(self.graph.node_index)
        for item in sources:
            source_nodes = (item.node_id,) if isinstance(item, PhaseDomainSourceEquivalent) else item.node_ids
            for node_id in source_nodes:
                if node_id not in known or self.graph.node(node_id).kind is PhaseDomainNodeKind.EARTH_REFERENCE:
                    raise ValueError(f"Source {item.source_id!r} references an invalid or earth-reference node.")
        for item in faults:
            if item.from_node_id not in known or item.to_node_id not in known:
                raise ValueError(f"Fault {item.connection_id!r} references an unknown graph node.")
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "faults", faults)
        object.__setattr__(self, "base_mva", base)


@dataclass(frozen=True, slots=True)
class PhaseDomainShortCircuitSolution:
    node_voltages_v: Mapping[str, complex]
    conductor_currents: Mapping[str, ShortCircuitConductorCurrent]
    source_currents_a: Mapping[str, Any]
    fault_currents_a: Mapping[str, complex]
    connection_currents_a: Mapping[str, complex]
    topology_revision: int
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_voltages_v", MappingProxyType(dict(self.node_voltages_v)))
        object.__setattr__(self, "conductor_currents", MappingProxyType(dict(self.conductor_currents)))
        object.__setattr__(self, "source_currents_a", MappingProxyType(dict(self.source_currents_a)))
        object.__setattr__(self, "fault_currents_a", MappingProxyType(dict(self.fault_currents_a)))
        object.__setattr__(self, "connection_currents_a", MappingProxyType(dict(self.connection_currents_a)))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))


class PhaseDomainShortCircuitSolver:
    """Solve one phase-domain fault using explicit source and fault primitives."""

    def solve(self, case: PhaseDomainShortCircuitCase) -> PhaseDomainShortCircuitSolution:
        if not isinstance(case, PhaseDomainShortCircuitCase):
            raise TypeError("case must be PhaseDomainShortCircuitCase.")
        snapshot = case.admittance
        ids = snapshot.node_ids
        index = {node_id: i for i, node_id in enumerate(ids)}
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
            else:
                indices = [snapshot.source_node_to_index[node_id] for node_id in source.node_ids]
                if any(index is None for index in indices):
                    raise ValueError(f"Multi-conductor source {source.source_id!r} is connected to a fixed earth node.")
                source_y = np.linalg.inv(np.asarray(source.impedance_matrix_ohm, dtype=complex))
                source_rhs = source_y @ np.asarray(source.internal_voltage_v, dtype=complex)
                for row, global_row in enumerate(indices):
                    rhs[global_row] += source_rhs[row]
                    for column, global_column in enumerate(indices):
                        y[global_row, global_column] += source_y[row, column]

        fault_finite_admittances: dict[str, complex] = {}
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
                fault_finite_admittances[fault.connection_id] = admittance

        if constraints:
            c = np.vstack(constraints)
            saddle = np.block([
                [y, c.conjugate().T],
                [c, np.zeros((len(constraints), len(constraints)), dtype=complex)],
            ])
            augmented_rhs = np.concatenate((rhs, np.asarray(constraint_values, dtype=complex)))
            solution = np.linalg.solve(saddle, augmented_rhs)[:len(ids)]
        else:
            solution = np.linalg.solve(y, rhs)
        if not np.all(np.isfinite(solution.real)) or not np.all(np.isfinite(solution.imag)):
            raise ValueError("Phase-domain fault solution contains non-finite node voltages.")
        voltage_by_node = {
            node_id: (0j if mapped is None else complex(solution[mapped]))
            for node_id, mapped in snapshot.source_node_to_index.items()
        }

        source_currents = {}
        for source in case.sources:
            if isinstance(source, PhaseDomainSourceEquivalent):
                source_currents[source.source_id] = (source.internal_voltage_v - voltage_by_node[source.node_id]) / source.impedance_ohm
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

        # Re-solve with multipliers retained to report exact bolted-fault currents.
        if constraints:
            multipliers = np.linalg.solve(saddle, augmented_rhs)[len(ids):]
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
        for edge in case.graph.connections:
            if not edge.in_service or edge.impedance_ohm == 0j:
                continue
            current_a = connection_currents[edge.connection_id]
            for side, node_id, signed_current in (
                ("FROM", edge.from_node_id, current_a),
                ("TO", edge.to_node_id, -current_a),
            ):
                node = case.graph.node(node_id)
                if node.kind is PhaseDomainNodeKind.EARTH_REFERENCE:
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

        return PhaseDomainShortCircuitSolution(
            node_voltages_v=voltage_by_node,
            conductor_currents=conductor_records,
            source_currents_a=source_currents,
            fault_currents_a=fault_currents,
            connection_currents_a=connection_currents,
            topology_revision=case.graph.topology_revision,
            diagnostics=tuple(connection_diagnostics),
        )


__all__ = [
    "PhaseDomainSourceEquivalent",
    "PhaseDomainFaultConnection",
    "PhaseDomainShortCircuitCase",
    "PhaseDomainShortCircuitSolution",
    "PhaseDomainShortCircuitSolver",
]
