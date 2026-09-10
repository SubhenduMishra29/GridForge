"""Immutable engineering result contracts for short-circuit studies."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .fault_types import FaultType


def _freeze_complex_mapping(values: Mapping[str, complex]) -> Mapping[str, complex]:
    return MappingProxyType({str(key): complex(value) for key, value in values.items()})


def _validate_current(value: Any, name: str) -> complex:
    try:
        current = complex(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a complex-valued current.") from exc
    if not math.isfinite(current.real) or not math.isfinite(current.imag):
        raise ValueError(f"{name} must be finite.")
    return current


def _validate_identity(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty engineering identifier.")
    return value


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
    """Current injected into the prepared network by one source."""

    source_id: str
    source_type: str
    bus_id: str
    current: complex
    magnitude: float
    angle_deg: float
    sequence_currents: Mapping[str, complex] = field(default_factory=dict)
    phase_currents: Mapping[str, complex] = field(default_factory=dict)

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
class ShortCircuitResult:
    """Completed short-circuit result detached from all live Core objects."""

    fault_type: FaultType
    fault_bus_index: int
    fault_bus_id: Any
    success: bool
    values: Mapping[str, Any]
    source_contributions: Mapping[str, ShortCircuitSourceContribution] = field(default_factory=dict)
    equipment_currents: Mapping[str, ShortCircuitEquipmentCurrent] = field(default_factory=dict)
    branch_currents: Mapping[str, ShortCircuitBranchCurrent] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        if isinstance(self.fault_bus_index, bool) or not isinstance(self.fault_bus_index, int):
            raise TypeError("fault_bus_index must be an integer.")
        object.__setattr__(self, "source_contributions", self._freeze_records(self.source_contributions, ShortCircuitSourceContribution, "source_contributions"))
        object.__setattr__(self, "equipment_currents", self._freeze_records(self.equipment_currents, ShortCircuitEquipmentCurrent, "equipment_currents"))
        object.__setattr__(self, "branch_currents", self._freeze_records(self.branch_currents, ShortCircuitBranchCurrent, "branch_currents"))

    @staticmethod
    def _freeze_records(values: Mapping[str, Any], expected_type: type, name: str) -> Mapping[str, Any]:
        frozen: dict[str, Any] = {}
        for key, value in values.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"{name} keys must be non-empty engineering identifiers.")
            if not isinstance(value, expected_type):
                raise TypeError(f"{name} values must be {expected_type.__name__} records.")
            if key != getattr(value, "source_id", getattr(value, "equipment_id", getattr(value, "branch_id", None))):
                raise ValueError(f"{name} key must match the record engineering identifier.")
            frozen[key] = value
        return MappingProxyType(frozen)

    @property
    def fault_current(self) -> complex | None:
        return self._complex_value("fault_current")

    @property
    def fault_current_magnitude(self) -> float | None:
        value = self.values.get("fault_current_magnitude")
        return None if value is None else float(value)

    @property
    def fault_current_angle_deg(self) -> float | None:
        value = self.values.get("fault_current_angle_deg")
        return None if value is None else float(value)

    @staticmethod
    def _as_complex(value: Any) -> complex | None:
        if value is None:
            return None
        return _validate_current(value, "fault_current")

    def _complex_value(self, key: str) -> complex | None:
        return self._as_complex(self.values.get(key))

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        result = dict(self.values)
        result.setdefault("fault_type", self.fault_type)
        result.setdefault("bus_index", self.fault_bus_index)
        result.setdefault("bus_id", self.fault_bus_id)
        result.setdefault("success", self.success)
        result["source_contributions"] = dict(self.source_contributions)
        result["equipment_currents"] = dict(self.equipment_currents)
        result["branch_currents"] = dict(self.branch_currents)
        return result


__all__ = [
    "ShortCircuitSourceContribution",
    "ShortCircuitBranchCurrent",
    "ShortCircuitEquipmentCurrent",
    "ShortCircuitResult",
]
