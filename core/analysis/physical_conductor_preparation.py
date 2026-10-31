"""Physical multi-conductor impedance preparation and branch-local current solution.

D15E converts explicit Core BranchConductorSystem data into immutable,
base-aware numerical snapshots. It solves the coupled series matrix only when
the caller supplies a complete conductor-voltage vector at both terminals.
It does not invent conductor potentials, return paths, neutral bonds, earth
connections, or screen terminations, and it does not stamp the scalar sequence
Ybus with a phase-domain primitive.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from core.network.physical_conductor_topology import PhysicalConductorTopologySnapshot


ComplexMatrix = tuple[tuple[complex, ...], ...]


def _matrix(value: Any, name: str, *, size: int) -> ComplexMatrix:
    array = np.asarray(value, dtype=complex)
    if array.shape != (size, size):
        raise ValueError(f"{name} must be a {size}x{size} matrix.")
    if not np.all(np.isfinite(array.real)) or not np.all(np.isfinite(array.imag)):
        raise ValueError(f"{name} must contain only finite complex values.")
    return tuple(tuple(complex(item) for item in row) for row in array.tolist())


def _freeze_vector(values: Sequence[Any], name: str, size: int) -> tuple[complex, ...]:
    array = np.asarray(tuple(values), dtype=complex)
    if array.ndim != 1 or array.size != size:
        raise ValueError(f"{name} must contain exactly {size} conductor voltages.")
    if not np.all(np.isfinite(array.real)) or not np.all(np.isfinite(array.imag)):
        raise ValueError(f"{name} must contain only finite complex values.")
    return tuple(complex(item) for item in array.tolist())


@dataclass(frozen=True, slots=True)
class PreparedPhysicalConductorBranch:
    """Detached, total-length conductor impedance primitive for one Line/Cable."""

    equipment_id: str
    equipment_type: str
    from_bus_id: str
    to_bus_id: str
    conductor_ids: tuple[str, ...]
    conductor_roles: tuple[str, ...]
    matrix_conductor_ids: tuple[str, ...]
    length_km: float
    base_mva: float
    base_voltage_kv: float
    z_base_ohm: float
    series_impedance_ohm: ComplexMatrix
    series_impedance_pu: ComplexMatrix
    series_admittance_pu: ComplexMatrix
    shunt_admittance_siemens: ComplexMatrix | None
    shunt_admittance_pu: ComplexMatrix | None
    project_id: str
    activation_generation: int
    topology_revision: int
    source_reference: str | None = None

    def __post_init__(self) -> None:
        for name in ("equipment_id", "equipment_type", "from_bus_id", "to_bus_id", "project_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty identifier.")
            object.__setattr__(self, name, value.strip())
        if self.equipment_type not in {"line", "cable"}:
            raise ValueError("Physical conductor primitive supports only Line and Cable.")
        if self.from_bus_id == self.to_bus_id:
            raise ValueError("Physical conductor branch must connect distinct Buses.")
        ids = tuple(self.conductor_ids)
        roles = tuple(self.conductor_roles)
        order = tuple(self.matrix_conductor_ids)
        if not ids or len(ids) != len(set(ids)) or len(roles) != len(ids):
            raise ValueError("Conductor identities and roles must be complete and unique.")
        if len(order) != len(ids) or set(order) != set(ids) or len(order) != len(set(order)):
            raise ValueError("Matrix ordering must identify every conductor exactly once.")
        object.__setattr__(self, "conductor_ids", ids)
        object.__setattr__(self, "conductor_roles", roles)
        object.__setattr__(self, "matrix_conductor_ids", order)
        size = len(order)
        for name in ("length_km", "base_mva", "base_voltage_kv", "z_base_ohm"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive.")
            object.__setattr__(self, name, value)
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")
        for name in ("series_impedance_ohm", "series_impedance_pu", "series_admittance_pu"):
            object.__setattr__(self, name, _matrix(getattr(self, name), name, size=size))
        if (self.shunt_admittance_siemens is None) != (self.shunt_admittance_pu is None):
            raise ValueError("Physical shunt matrices must be supplied together.")
        if self.shunt_admittance_siemens is not None:
            object.__setattr__(self, "shunt_admittance_siemens", _matrix(self.shunt_admittance_siemens, "shunt_admittance_siemens", size=size))
            object.__setattr__(self, "shunt_admittance_pu", _matrix(self.shunt_admittance_pu, "shunt_admittance_pu", size=size))
        if self.source_reference is not None:
            if not isinstance(self.source_reference, str) or not self.source_reference.strip():
                raise ValueError("source_reference must be non-empty when supplied.")
            object.__setattr__(self, "source_reference", self.source_reference.strip())

    @property
    def shunt_available(self) -> bool:
        return self.shunt_admittance_siemens is not None


@dataclass(frozen=True, slots=True)
class PhysicalConductorImpedanceSnapshot:
    """Immutable collection of prepared branch primitives with topology provenance."""

    project_id: str
    activation_generation: int
    topology_revision: int
    branches: tuple[PreparedPhysicalConductorBranch, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be non-empty.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        if isinstance(self.activation_generation, bool) or not isinstance(self.activation_generation, int) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")
        branches = tuple(self.branches)
        if any(not isinstance(item, PreparedPhysicalConductorBranch) for item in branches):
            raise TypeError("branches must contain PreparedPhysicalConductorBranch records.")
        ids = tuple(item.equipment_id for item in branches)
        if len(ids) != len(set(ids)):
            raise ValueError("Physical conductor impedance snapshot contains duplicate branch identities.")
        if branches != tuple(sorted(branches, key=lambda item: (item.equipment_type, item.equipment_id))):
            raise ValueError("Physical conductor impedance branches must be deterministically ordered.")
        for item in branches:
            if (item.project_id, item.activation_generation, item.topology_revision) != (
                self.project_id, self.activation_generation, self.topology_revision
            ):
                raise ValueError("Physical conductor impedance branch provenance does not match its snapshot.")
        object.__setattr__(self, "branches", branches)

    def branch(self, equipment_id: str) -> PreparedPhysicalConductorBranch:
        for item in self.branches:
            if item.equipment_id == equipment_id:
                return item
        raise KeyError(f"No prepared physical conductor impedance exists for {equipment_id!r}.")


@dataclass(frozen=True, slots=True)
class PhysicalConductorBranchCurrentSolution:
    """Branch-local conductor current solution; current vectors follow matrix order."""

    equipment_id: str
    conductor_ids: tuple[str, ...]
    series_current_a: tuple[complex, ...]
    from_terminal_current_a: tuple[complex, ...] | None
    to_terminal_current_a: tuple[complex, ...] | None
    shunt_current_available: bool
    project_id: str
    activation_generation: int
    topology_revision: int

    def __post_init__(self) -> None:
        size = len(self.conductor_ids)
        if not size or len(set(self.conductor_ids)) != size:
            raise ValueError("Current solution requires unique conductor identities.")
        for name in ("series_current_a", "from_terminal_current_a", "to_terminal_current_a"):
            value = getattr(self, name)
            if value is not None:
                vector = tuple(complex(item) for item in value)
                if len(vector) != size or any(not math.isfinite(x.real) or not math.isfinite(x.imag) for x in vector):
                    raise ValueError(f"{name} must be a finite vector matching the conductor inventory.")
                object.__setattr__(self, name, vector)
        if self.shunt_current_available != (self.from_terminal_current_a is not None and self.to_terminal_current_a is not None):
            raise ValueError("Terminal current availability must match explicit shunt-matrix availability.")


def prepare_physical_conductor_impedance_snapshot(
    network: Any,
    topology: PhysicalConductorTopologySnapshot,
    *,
    base_mva: float,
) -> PhysicalConductorImpedanceSnapshot:
    """Convert explicit ohm/km and S/km matrices to total ohms and study pu.

    A single common three-phase MVA and line-line kV base is used for every
    conductor in the branch vector. FROM/TO Bus voltage bases must agree;
    voltage-level conversion belongs to a transformer model, not a Line/Cable.
    """
    if network is None or not hasattr(network, "get_by_identity"):
        raise TypeError("An authoritative Network is required.")
    if not isinstance(topology, PhysicalConductorTopologySnapshot):
        raise TypeError("topology must be PhysicalConductorTopologySnapshot.")
    base_mva = float(base_mva)
    if not math.isfinite(base_mva) or base_mva <= 0.0:
        raise ValueError("base_mva must be finite and positive.")
    if str(getattr(network, "project_id", "UNSCOPED")) != topology.project_id:
        raise ValueError("Physical conductor topology project provenance is stale.")
    if int(getattr(network, "activation_generation", 1)) != topology.activation_generation:
        raise ValueError("Physical conductor topology activation generation is stale.")
    state = getattr(network, "state", None)
    if getattr(state, "topology_revision", None) != topology.topology_revision or not bool(getattr(state, "topology_valid", False)):
        raise ValueError("Physical conductor topology revision is stale or invalid.")

    prepared: list[PreparedPhysicalConductorBranch] = []
    for item in topology.branches:
        if not item.in_service:
            continue
        branch = network.get_by_identity(item.equipment_id)
        if branch is None or str(getattr(branch, "id", "")) != item.equipment_id:
            raise ValueError(f"Physical conductor owner {item.equipment_id!r} is not registered.")
        if getattr(branch, "conductor_system", None) is not item.conductor_system:
            raise ValueError(f"Physical conductor inventory changed after topology preparation for {item.equipment_id!r}.")
        from_bus = network.get_by_identity(item.from_bus_id)
        to_bus = network.get_by_identity(item.to_bus_id)
        if from_bus is None or to_bus is None:
            raise ValueError(f"Physical conductor branch {item.equipment_id!r} has unresolved terminal Bus identities.")
        kv_from = float(getattr(from_bus, "nominal_voltage_kv", 0.0))
        kv_to = float(getattr(to_bus, "nominal_voltage_kv", 0.0))
        if not math.isfinite(kv_from) or kv_from <= 0.0 or not math.isfinite(kv_to) or kv_to <= 0.0:
            raise ValueError(f"Physical conductor branch {item.equipment_id!r} requires explicit positive Bus voltage bases.")
        if not math.isclose(kv_from, kv_to, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"Physical conductor branch {item.equipment_id!r} spans different Bus voltage bases; a Line/Cable base conversion is unsupported.")
        system = item.conductor_system
        order = system.matrix_conductor_ids
        length = system.length_km
        z_ohm = np.asarray(system.series_impedance_matrix_ohm_per_km, dtype=complex) * length
        z_base = kv_from * kv_from / base_mva
        z_pu = z_ohm / z_base
        try:
            condition_number = float(np.linalg.cond(z_pu))
            if not math.isfinite(condition_number) or condition_number > 1.0e12:
                raise ValueError(f"Physical conductor series impedance matrix for {item.equipment_id!r} is numerically ill-conditioned.")
            y_pu = np.linalg.inv(z_pu)
        except np.linalg.LinAlgError as exc:
            raise ValueError(f"Physical conductor series impedance matrix for {item.equipment_id!r} is singular.") from exc
        if not np.all(np.isfinite(y_pu.real)) or not np.all(np.isfinite(y_pu.imag)):
            raise ValueError(f"Physical conductor series admittance for {item.equipment_id!r} is non-finite.")
        shunt_siemens = None
        shunt_pu = None
        if system.shunt_admittance_matrix_siemens_per_km is not None:
            shunt_siemens = np.asarray(system.shunt_admittance_matrix_siemens_per_km, dtype=complex) * length
            shunt_pu = shunt_siemens * z_base
        prepared.append(PreparedPhysicalConductorBranch(
            equipment_id=item.equipment_id,
            equipment_type=item.equipment_type,
            from_bus_id=item.from_bus_id,
            to_bus_id=item.to_bus_id,
            conductor_ids=tuple(conductor.conductor_id for conductor in system.conductors),
            conductor_roles=tuple(system.conductor(conductor_id).role.value for conductor_id in order),
            matrix_conductor_ids=tuple(order),
            length_km=length,
            base_mva=base_mva,
            base_voltage_kv=kv_from,
            z_base_ohm=z_base,
            series_impedance_ohm=_matrix(z_ohm, "series_impedance_ohm", size=len(order)),
            series_impedance_pu=_matrix(z_pu, "series_impedance_pu", size=len(order)),
            series_admittance_pu=_matrix(y_pu, "series_admittance_pu", size=len(order)),
            shunt_admittance_siemens=None if shunt_siemens is None else _matrix(shunt_siemens, "shunt_admittance_siemens", size=len(order)),
            shunt_admittance_pu=None if shunt_pu is None else _matrix(shunt_pu, "shunt_admittance_pu", size=len(order)),
            project_id=topology.project_id,
            activation_generation=topology.activation_generation,
            topology_revision=topology.topology_revision,
            source_reference=system.source_reference,
        ))
    return PhysicalConductorImpedanceSnapshot(
        project_id=topology.project_id,
        activation_generation=topology.activation_generation,
        topology_revision=topology.topology_revision,
        branches=tuple(sorted(prepared, key=lambda value: (value.equipment_type, value.equipment_id))),
    )


def solve_physical_conductor_branch_currents(
    branch: PreparedPhysicalConductorBranch,
    *,
    from_terminal_voltages_v: Sequence[Any],
    to_terminal_voltages_v: Sequence[Any],
) -> PhysicalConductorBranchCurrentSolution:
    """Solve the coupled series conductor currents from explicit terminal potentials.

    Every conductor voltage is required at both ends in matrix_conductor_ids
    order. With explicit shunt data, return total terminal currents using a
    nominal pi split. Without shunt data, only series currents are returned;
    terminal totals remain None rather than treating missing shunt as zero.
    """
    if not isinstance(branch, PreparedPhysicalConductorBranch):
        raise TypeError("branch must be PreparedPhysicalConductorBranch.")
    size = len(branch.matrix_conductor_ids)
    vf = np.asarray(_freeze_vector(from_terminal_voltages_v, "from_terminal_voltages_v", size), dtype=complex)
    vt = np.asarray(_freeze_vector(to_terminal_voltages_v, "to_terminal_voltages_v", size), dtype=complex)
    z = np.asarray(branch.series_impedance_ohm, dtype=complex)
    try:
        series = np.linalg.solve(z, vf - vt)
    except np.linalg.LinAlgError as exc:
        raise ValueError("Physical conductor series impedance matrix cannot be solved.") from exc
    if not np.all(np.isfinite(series.real)) or not np.all(np.isfinite(series.imag)):
        raise ValueError("Physical conductor current solution is non-finite.")
    from_total = to_total = None
    if branch.shunt_admittance_siemens is not None:
        y_half = np.asarray(branch.shunt_admittance_siemens, dtype=complex) * 0.5
        from_total = series + y_half @ vf
        to_total = -series + y_half @ vt
        if not all(np.all(np.isfinite(value.real)) and np.all(np.isfinite(value.imag)) for value in (from_total, to_total)):
            raise ValueError("Physical conductor terminal current solution is non-finite.")
    return PhysicalConductorBranchCurrentSolution(
        equipment_id=branch.equipment_id,
        conductor_ids=branch.matrix_conductor_ids,
        series_current_a=tuple(complex(value) for value in series.tolist()),
        from_terminal_current_a=None if from_total is None else tuple(complex(value) for value in from_total.tolist()),
        to_terminal_current_a=None if to_total is None else tuple(complex(value) for value in to_total.tolist()),
        shunt_current_available=branch.shunt_admittance_siemens is not None,
        project_id=branch.project_id,
        activation_generation=branch.activation_generation,
        topology_revision=branch.topology_revision,
    )


__all__ = [
    "PreparedPhysicalConductorBranch",
    "PhysicalConductorImpedanceSnapshot",
    "PhysicalConductorBranchCurrentSolution",
    "prepare_physical_conductor_impedance_snapshot",
    "solve_physical_conductor_branch_currents",
]
