# ============================================================
# File: core/analysis/short_circuit_configuration.py
# GridForge V2 — Short Circuit Study Configuration
# Author: Subhendu Mishra
# ============================================================
"""Immutable Short-Circuit study configuration boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping

from core.solver.short_circuit.fault_types import FaultType


def _freeze_metadata_value(value: Any) -> Any:
    """Recursively freeze built-in metadata containers without coercing typed objects."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_metadata_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_metadata_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_metadata_value(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ShortCircuitStudyConfiguration:
    """Immutable study intent independent of live Core objects."""

    fault_type: FaultType
    fault_bus_id: str
    fault_impedance: complex = 0.0j
    element_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    base_mva: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "fault_type", FaultType.from_value(self.fault_type))
        if not isinstance(self.fault_bus_id, str) or not self.fault_bus_id.strip():
            raise ValueError("fault_bus_id must be a non-empty string.")
        object.__setattr__(self, "fault_bus_id", self.fault_bus_id.strip())
        impedance = complex(self.fault_impedance)
        if not math.isfinite(impedance.real) or not math.isfinite(impedance.imag):
            raise ValueError("fault_impedance real and imaginary components must be finite.")
        object.__setattr__(self, "fault_impedance", impedance)
        ids = tuple(str(item).strip() for item in self.element_ids)
        if any(not item for item in ids):
            raise ValueError("element_ids must contain only non-empty identifiers.")
        if len(set(ids)) != len(ids):
            raise ValueError("element_ids must not contain duplicate identifiers.")
        object.__setattr__(self, "element_ids", ids)
        if self.base_mva is not None:
            if isinstance(self.base_mva, bool):
                raise TypeError("base_mva must be numeric, not boolean.")
            base_mva = float(self.base_mva)
            if not math.isfinite(base_mva) or base_mva <= 0.0:
                raise ValueError("base_mva must be finite and greater than zero when supplied.")
            object.__setattr__(self, "base_mva", base_mva)
        object.__setattr__(self, "metadata", _freeze_metadata_value(self.metadata))


__all__ = ["ShortCircuitStudyConfiguration"]
