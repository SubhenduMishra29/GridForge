"""Standalone numerical result contract for short-circuit studies."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .fault_types import FaultType


@dataclass(frozen=True, slots=True)
class ShortCircuitResult:
    """Completed short-circuit result detached from all live Core objects.

    ``values`` preserves the calculation engines' existing result keys without
    introducing a second speculative result schema during the boundary move.
    """

    fault_type: FaultType
    fault_bus_index: int
    fault_bus_id: Any
    success: bool
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        if isinstance(self.fault_bus_index, bool) or not isinstance(self.fault_bus_index, int):
            raise TypeError("fault_bus_index must be an integer.")

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        result = dict(self.values)
        result.setdefault("fault_type", self.fault_type)
        result.setdefault("bus_index", self.fault_bus_index)
        result.setdefault("bus_id", self.fault_bus_id)
        result.setdefault("success", self.success)
        return result
