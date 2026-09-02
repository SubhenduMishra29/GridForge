"""Immutable standalone result contract for AC power flow."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping


def _tuple_floats(values):
    result = tuple(float(value) for value in values)
    if not all(isfinite(value) for value in result):
        raise ValueError("Numerical result values must be finite.")
    return result


def _immutable_records(values):
    return tuple(MappingProxyType(dict(item)) for item in values)


@dataclass(frozen=True, slots=True)
class PowerFlowResult:
    """Completed numerical result with no reference to Core objects."""

    success: bool
    iterations: int
    error: float
    pv_to_pq: tuple[Mapping[str, Any], ...]
    history: tuple[float, ...]
    message: str
    voltage_magnitudes: tuple[float, ...]
    voltage_angles: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pv_to_pq", _immutable_records(self.pv_to_pq))
        object.__setattr__(self, "history", _tuple_floats(self.history))
        object.__setattr__(self, "voltage_magnitudes", _tuple_floats(self.voltage_magnitudes))
        object.__setattr__(self, "voltage_angles", _tuple_floats(self.voltage_angles))
        if len(self.voltage_magnitudes) != len(self.voltage_angles):
            raise ValueError("Voltage magnitude and angle result lengths must match.")
        if self.iterations < 0:
            raise ValueError("iterations cannot be negative.")
        if not isfinite(float(self.error)) and float(self.error) != float("inf"):
            raise ValueError("error must be finite or positive infinity.")
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def voltages(self) -> dict[str, tuple[float, ...]]:
        return {"Vm": self.voltage_magnitudes, "Va": self.voltage_angles}

    def as_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "iterations": self.iterations,
            "error": self.error,
            "pv_to_pq": tuple(dict(item) for item in self.pv_to_pq),
            "history": self.history,
            "message": self.message,
            "voltages": self.voltages,
        }


__all__ = ["PowerFlowResult"]
