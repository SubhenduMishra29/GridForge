"""Immutable engineering result contracts for short-circuit studies."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .fault_types import FaultType


class ShortCircuitStatus(str, Enum):
    """Status of the fault calculation itself."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"


class ContributionStatus(str, Enum):
    """Independent status of source/branch/equipment contribution data."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"


def _validate_current(value: Any, name: str) -> complex:
    try:
        current = complex(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a complex-valued current.") from exc
    if not math.isfinite(current.real) or not math.isfinite(current.imag):
        raise ValueError(f"{name} must be finite.")
    return current


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _freeze_complex_mapping(values: Mapping[str, complex]) -> Mapping[str, complex]:
    return MappingProxyType({str(key): _validate_current(value, f"current[{key!r}]") for key, value in values.items()})


def _validate_identity(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty engineering identifier.")
    return value.strip()


def _validate_polar(current: complex, magnitude: Any, angle_deg: Any, name: str) -> tuple[float, float]:
    expected_magnitude = float(abs(current))
    supplied_magnitude = float(magnitude)
    supplied_angle = float(angle_deg)
    if not math.isfinite(supplied_magnitude) or supplied_magnitude < 0.0:
        raise ValueError(f"{name}.magnitude must be finite and non-negative.")
    if not math.isfinite(supplied_angle):
        raise ValueError(f"{name}.angle_deg must be finite.")
    if not math.isclose(supplied_magnitude, expected_magnitude, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError(f"{name}.magnitude is inconsistent with the complex current.")
    return supplied_magnitude, supplied_angle


@dataclass(frozen=True, slots=True)
class ShortCircuitSourceContribution:
    """Current injected by one explicitly identified short-circuit source."""

    source_id: str
    source_type: str
    bus_id: str
    current: complex
    magnitude: float
    angle_deg: float
    sequence_currents: Mapping[str, complex] = field(default_factory=dict)
    phase_currents: Mapping[str, complex] = field(default_factory=dict)
    Z1: complex | None = None
    Z2: complex | None = None
    Z0: complex | None = None
    internal_voltage: complex | None = None
    operating_state: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _validate_identity(self.source_id, "source_id"))
        object.__setattr__(self, "source_type", _validate_identity(self.source_type, "source_type"))
        object.__setattr__(self, "bus_id", _validate_identity(self.bus_id, "bus_id"))
        current = _validate_current(self.current, "current")
        magnitude, angle = _validate_polar(current, self.magnitude, self.angle_deg, "source contribution")
        object.__setattr__(self, "current", current)
        object.__setattr__(self, "magnitude", magnitude)
        object.__setattr__(self, "angle_deg", angle)
        object.__setattr__(self, "sequence_currents", _freeze_complex_mapping(self.sequence_currents))
        object.__setattr__(self, "phase_currents", _freeze_complex_mapping(self.phase_currents))
        for name in ("Z1", "Z2", "Z0", "internal_voltage"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, complex(value))
        if not isinstance(self.operating_state, str):
            raise TypeError("operating_state must be a string.")
        object.__setattr__(self, "operating_state", self.operating_state.strip())


@dataclass(frozen=True, slots=True)
class ShortCircuitBranchCurrent:
    """Current through one prepared network branch."""

    branch_id: str
    from_bus_id: str
    to_bus_id: str
    current: complex
    magnitude: float
    angle_deg: float
    sequence_currents: Mapping[str, complex] = field(default_factory=dict)
    phase_currents: Mapping[str, complex] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_id", _validate_identity(self.branch_id, "branch_id"))
        object.__setattr__(self, "from_bus_id", _validate_identity(self.from_bus_id, "from_bus_id"))
        object.__setattr__(self, "to_bus_id", _validate_identity(self.to_bus_id, "to_bus_id"))
        if self.from_bus_id == self.to_bus_id:
            raise ValueError("A branch current requires distinct from/to bus identities.")
        current = _validate_current(self.current, "current")
        magnitude, angle = _validate_polar(current, self.magnitude, self.angle_deg, "branch current")
        object.__setattr__(self, "current", current)
        object.__setattr__(self, "magnitude", magnitude)
        object.__setattr__(self, "angle_deg", angle)
        object.__setattr__(self, "sequence_currents", _freeze_complex_mapping(self.sequence_currents))
        object.__setattr__(self, "phase_currents", _freeze_complex_mapping(self.phase_currents))


@dataclass(frozen=True, slots=True)
class ShortCircuitEquipmentCurrent:
    """Current associated with one prepared equipment identity."""

    equipment_id: str
    equipment_type: str
    current: complex
    magnitude: float
    angle_deg: float
    bus_id: str | None = None
    sequence_currents: Mapping[str, complex] = field(default_factory=dict)
    phase_currents: Mapping[str, complex] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "equipment_id", _validate_identity(self.equipment_id, "equipment_id"))
        object.__setattr__(self, "equipment_type", _validate_identity(self.equipment_type, "equipment_type"))
        if self.bus_id is not None:
            object.__setattr__(self, "bus_id", _validate_identity(self.bus_id, "bus_id"))
        current = _validate_current(self.current, "current")
        magnitude, angle = _validate_polar(current, self.magnitude, self.angle_deg, "equipment current")
        object.__setattr__(self, "current", current)
        object.__setattr__(self, "magnitude", magnitude)
        object.__setattr__(self, "angle_deg", angle)
        object.__setattr__(self, "sequence_currents", _freeze_complex_mapping(self.sequence_currents))
        object.__setattr__(self, "phase_currents", _freeze_complex_mapping(self.phase_currents))


@dataclass(frozen=True, slots=True)
class ShortCircuitTerminalCurrent:
    """Current at one physical equipment terminal, positive INTO equipment."""

    equipment_id: str
    equipment_type: str
    terminal_role: str
    bus_id: str
    current: complex
    sequence_currents: Mapping[str, complex] = field(default_factory=dict)
    phase_currents: Mapping[str, complex] = field(default_factory=dict)
    reference_direction: str = "INTO_EQUIPMENT"
    current_units: str = "per_unit"
    sequence_provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("equipment_id", "equipment_type", "terminal_role", "bus_id"):
            object.__setattr__(self, name, _validate_identity(getattr(self, name), name))
        object.__setattr__(self, "current", _validate_current(self.current, "terminal current"))
        object.__setattr__(self, "sequence_currents", _freeze_complex_mapping(self.sequence_currents))
        object.__setattr__(self, "phase_currents", _freeze_complex_mapping(self.phase_currents))
        if not isinstance(self.sequence_provenance, Mapping):
            raise TypeError("sequence_provenance must be a mapping.")
        object.__setattr__(self, "sequence_provenance", _freeze_value(self.sequence_provenance))
        if self.reference_direction != "INTO_EQUIPMENT":
            raise ValueError("Terminal current reference_direction must be INTO_EQUIPMENT.")
        if self.current_units != "per_unit":
            raise ValueError("Terminal current current_units must be per_unit.")


@dataclass(frozen=True, slots=True)
class ShortCircuitConductorCurrent:
    """Immutable current through one explicitly identified physical conductor.

    The record is terminal-scoped: the same physical conductor has a distinct
    current record at each equipment terminal. Positive direction is explicit
    relative to the owning equipment, never inferred from list ordering.
    """

    conductor_id: str
    equipment_id: str
    equipment_type: str
    terminal_role: str
    bus_id: str
    phase_or_sequence: str
    current: complex
    topology_revision: int
    base_mva: float
    voltage_base_kv: float
    reference_direction: str = "INTO_EQUIPMENT"
    current_units: str = "per_unit"
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("conductor_id", "equipment_id", "equipment_type", "terminal_role", "bus_id"):
            object.__setattr__(self, name, _validate_identity(getattr(self, name), name))
        phase = _validate_identity(self.phase_or_sequence, "phase_or_sequence").upper()
        if phase not in {"A", "B", "C", "N", "PE", "SHIELD", "PILOT", "OTHER"}:
            raise ValueError("Conductor current phase_or_sequence must identify a declared physical conductor role.")
        object.__setattr__(self, "phase_or_sequence", phase)
        object.__setattr__(self, "current", _validate_current(self.current, "conductor current"))
        if isinstance(self.topology_revision, bool) or not isinstance(self.topology_revision, int) or self.topology_revision < 0:
            raise ValueError("Conductor current topology_revision must be a non-negative integer.")
        for name in ("base_mva", "voltage_base_kv"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError("Conductor current {} must be finite and positive.".format(name))
            object.__setattr__(self, name, value)
        if self.reference_direction not in {"INTO_EQUIPMENT", "OUT_OF_EQUIPMENT"}:
            raise ValueError("Conductor current reference_direction must be explicit.")
        if self.current_units != "per_unit":
            raise ValueError("Conductor current current_units must be per_unit.")
        if not isinstance(self.provenance, Mapping):
            raise TypeError("Conductor current provenance must be a mapping.")
        object.__setattr__(self, "provenance", _freeze_value(self.provenance))

    @property
    def record_id(self) -> str:
        return "{}:{}:{}".format(self.equipment_id, self.terminal_role, self.conductor_id)


@dataclass(frozen=True, slots=True)
class ShortCircuitResult:
    """Completed short-circuit result detached from all live Core objects."""

    fault_type: FaultType
    fault_bus_index: int
    fault_bus_id: Any
    success: bool
    values: Mapping[str, Any]
    fault_current: complex | None = None
    fault_current_magnitude: float | None = None
    fault_current_angle_deg: float | None = None
    sequence_currents: Mapping[str, complex] = field(default_factory=dict)
    phase_currents: Mapping[str, complex] = field(default_factory=dict)
    ground_current: complex | None = None
    ground_current_magnitude: float | None = None
    source_contributions: Mapping[str, ShortCircuitSourceContribution] = field(default_factory=dict)
    equipment_currents: Mapping[str, ShortCircuitEquipmentCurrent] = field(default_factory=dict)
    branch_currents: Mapping[str, ShortCircuitBranchCurrent] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    status: ShortCircuitStatus | str | None = None
    contribution_status: ContributionStatus | str = ContributionStatus.UNAVAILABLE
    diagnostics: tuple[str, ...] = ()
    terminal_currents: Mapping[str, ShortCircuitTerminalCurrent] = field(default_factory=dict)
    terminal_current_status: ContributionStatus | str = ContributionStatus.UNAVAILABLE
    terminal_current_diagnostics: tuple[str, ...] = ()
    conductor_currents: Mapping[str, ShortCircuitConductorCurrent] = field(default_factory=dict)
    conductor_current_status: ContributionStatus | str = ContributionStatus.UNAVAILABLE
    conductor_current_diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _freeze_value(self.values))
        if isinstance(self.fault_bus_index, bool) or not isinstance(self.fault_bus_index, int):
            raise TypeError("fault_bus_index must be an integer.")
        if self.fault_current is not None:
            object.__setattr__(self, "fault_current", _validate_current(self.fault_current, "fault_current"))
        if self.ground_current is not None:
            object.__setattr__(self, "ground_current", _validate_current(self.ground_current, "ground_current"))
        if self.fault_current is not None and self.fault_current_magnitude is not None:
            magnitude, _ = _validate_polar(self.fault_current, self.fault_current_magnitude, self.fault_current_angle_deg if self.fault_current_angle_deg is not None else math.degrees(math.atan2(self.fault_current.imag, self.fault_current.real)), "fault current")
            object.__setattr__(self, "fault_current_magnitude", magnitude)
        if self.ground_current is not None and self.ground_current_magnitude is not None:
            supplied = float(self.ground_current_magnitude)
            if not math.isfinite(supplied) or not math.isclose(supplied, abs(self.ground_current), rel_tol=1e-9, abs_tol=1e-12):
                raise ValueError("ground_current_magnitude is inconsistent with ground_current.")
        object.__setattr__(self, "sequence_currents", _freeze_complex_mapping(self.sequence_currents))
        object.__setattr__(self, "phase_currents", _freeze_complex_mapping(self.phase_currents))
        object.__setattr__(self, "source_contributions", self._freeze_records(self.source_contributions, ShortCircuitSourceContribution, "source_contributions"))
        object.__setattr__(self, "equipment_currents", self._freeze_records(self.equipment_currents, ShortCircuitEquipmentCurrent, "equipment_currents"))
        object.__setattr__(self, "branch_currents", self._freeze_records(self.branch_currents, ShortCircuitBranchCurrent, "branch_currents"))
        object.__setattr__(self, "terminal_currents", self._freeze_terminal_records(self.terminal_currents))
        object.__setattr__(self, "conductor_currents", self._freeze_conductor_records(self.conductor_currents))
        try:
            terminal_status = ContributionStatus(self.terminal_current_status)
        except ValueError as exc:
            raise ValueError(f"Unsupported terminal current status: {self.terminal_current_status!r}.") from exc
        object.__setattr__(self, "terminal_current_status", terminal_status)
        object.__setattr__(self, "terminal_current_diagnostics", tuple(str(item) for item in self.terminal_current_diagnostics))
        try:
            conductor_status = ContributionStatus(self.conductor_current_status)
        except ValueError as exc:
            raise ValueError(f"Unsupported conductor current status: {self.conductor_current_status!r}.") from exc
        object.__setattr__(self, "conductor_current_status", conductor_status)
        object.__setattr__(self, "conductor_current_diagnostics", tuple(str(item) for item in self.conductor_current_diagnostics))
        if self.conductor_currents and conductor_status is ContributionStatus.UNAVAILABLE:
            raise ValueError("Conductor-current records cannot be marked UNAVAILABLE.")
        if not self.conductor_currents and conductor_status is ContributionStatus.COMPLETE:
            raise ValueError("Conductor-current coverage cannot be COMPLETE without records.")

        object.__setattr__(self, "provenance", _freeze_value(self.provenance))
        status = self.status
        if status is None:
            status = ShortCircuitStatus.COMPLETE if self.success else ShortCircuitStatus.FAILED
        try:
            status = ShortCircuitStatus(status)
        except ValueError as exc:
            raise ValueError(f"Unsupported short-circuit status: {status!r}.") from exc
        object.__setattr__(self, "status", status)
        try:
            contribution_status = ContributionStatus(self.contribution_status)
        except ValueError as exc:
            raise ValueError(f"Unsupported contribution status: {self.contribution_status!r}.") from exc
        object.__setattr__(self, "contribution_status", contribution_status)
        diagnostics = tuple(str(item) for item in self.diagnostics)
        object.__setattr__(self, "diagnostics", diagnostics)

    @staticmethod
    def _freeze_records(values: Mapping[str, Any], expected_type: type, name: str) -> Mapping[str, Any]:
        frozen: dict[str, Any] = {}
        for key, value in values.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"{name} keys must be non-empty engineering identifiers.")
            if not isinstance(value, expected_type):
                raise TypeError(f"{name} values must be {expected_type.__name__} records.")
            identity = getattr(value, "source_id", None) or getattr(value, "equipment_id", None) or getattr(value, "branch_id", None)
            if key != identity:
                raise ValueError(f"{name} key must match the record engineering identifier.")
            frozen[key] = value
        return MappingProxyType(frozen)

    @staticmethod
    def _freeze_terminal_records(values: Mapping[str, ShortCircuitTerminalCurrent]) -> Mapping[str, ShortCircuitTerminalCurrent]:
        frozen: dict[str, ShortCircuitTerminalCurrent] = {}
        for key, value in values.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("terminal_currents keys must be non-empty identifiers.")
            if not isinstance(value, ShortCircuitTerminalCurrent):
                raise TypeError("terminal_currents values must be ShortCircuitTerminalCurrent records.")
            if key != f"{value.equipment_id}:{value.terminal_role}":
                raise ValueError("terminal current key must match equipment ID and terminal role.")
            frozen[key] = value
        return MappingProxyType(frozen)

    @staticmethod
    def _freeze_conductor_records(values: Mapping[str, ShortCircuitConductorCurrent]) -> Mapping[str, ShortCircuitConductorCurrent]:
        frozen: dict[str, ShortCircuitConductorCurrent] = {}
        for key, value in values.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("conductor_currents keys must be non-empty identifiers.")
            if not isinstance(value, ShortCircuitConductorCurrent):
                raise TypeError("conductor_currents values must be ShortCircuitConductorCurrent records.")
            if key != value.record_id:
                raise ValueError("Conductor current key must match equipment, terminal and conductor identity.")
            frozen[key] = value
        return MappingProxyType(frozen)

    def get_conductor_current(self, *, equipment_id: str, terminal_role: str, conductor_id: str) -> ShortCircuitConductorCurrent:
        key = "{}:{}:{}".format(equipment_id, terminal_role, conductor_id)
        try:
            return self.conductor_currents[key]
        except KeyError as exc:
            raise KeyError("No conductor-current record exists for {!r}.".format(key)) from exc

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        result = dict(self.values)
        result.update({
            "fault_type": self.fault_type,
            "bus_index": self.fault_bus_index,
            "bus_id": self.fault_bus_id,
            "success": self.success,
            "status": self.status,
            "contribution_status": self.contribution_status,
            "diagnostics": self.diagnostics,
            "fault_current": self.fault_current,
            "fault_current_magnitude": self.fault_current_magnitude,
            "fault_current_angle_deg": self.fault_current_angle_deg,
            "sequence_currents": dict(self.sequence_currents),
            "phase_currents": dict(self.phase_currents),
            "ground_current": self.ground_current,
            "ground_current_magnitude": self.ground_current_magnitude,
            "source_contributions": dict(self.source_contributions),
            "equipment_currents": dict(self.equipment_currents),
            "branch_currents": dict(self.branch_currents),
            "terminal_currents": dict(self.terminal_currents),
            "terminal_current_status": self.terminal_current_status,
            "terminal_current_diagnostics": self.terminal_current_diagnostics,
            "conductor_currents": dict(self.conductor_currents),
            "conductor_current_status": self.conductor_current_status,
            "conductor_current_diagnostics": self.conductor_current_diagnostics,
            "provenance": dict(self.provenance),
        })
        return result


__all__ = [
    "ShortCircuitStatus",
    "ContributionStatus",
    "ShortCircuitSourceContribution",
    "ShortCircuitBranchCurrent",
    "ShortCircuitEquipmentCurrent",
    "ShortCircuitTerminalCurrent",
    "ShortCircuitConductorCurrent",
    "ShortCircuitResult",
]
