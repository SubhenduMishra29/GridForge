# ============================================================
# File: core/solver/power_flow/input.py
# GridForge V2 — Power Flow Input Contract
# ============================================================

"""Immutable numerical input boundary for one Power Flow study.

The input is a prepared snapshot. Numerical execution never obtains live
Core objects; Network/Model data must cross the boundary through this
contract and the separately prepared YBus representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Real
from typing import Sequence


class PowerFlowBusType(str, Enum):
    PQ = "PQ"
    PV = "PV"
    SLACK = "SLACK"


def _validate_finite_real(value: Real, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number.")
    value = float(value)
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def _validate_bus_id(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty.")
    return value


def _validate_sequence_length(values: Sequence[object], expected: int, name: str) -> None:
    if len(values) != expected:
        raise ValueError(f"{name} length must be {expected}; received {len(values)}.")


@dataclass(frozen=True, slots=True)
class PowerFlowInput:
    """Immutable numerical problem specification with no Core references."""

    bus_ids: tuple[str, ...]
    bus_types: tuple[PowerFlowBusType, ...]
    p_spec: tuple[float, ...]
    q_spec: tuple[float, ...]
    q_min: tuple[float | None, ...]
    q_max: tuple[float | None, ...]
    initial_vm: tuple[float, ...]
    initial_va: tuple[float, ...]

    def __post_init__(self) -> None:
        bus_ids = tuple(_validate_bus_id(value, "bus_id") for value in self.bus_ids)
        bus_types = tuple(self._normalize_bus_type(value) for value in self.bus_types)
        p_spec = tuple(_validate_finite_real(value, "p_spec") for value in self.p_spec)
        q_spec = tuple(_validate_finite_real(value, "q_spec") for value in self.q_spec)
        q_min = tuple(self._validate_optional(value, "q_min") for value in self.q_min)
        q_max = tuple(self._validate_optional(value, "q_max") for value in self.q_max)
        initial_vm = tuple(_validate_finite_real(value, "initial_vm") for value in self.initial_vm)
        initial_va = tuple(_validate_finite_real(value, "initial_va") for value in self.initial_va)
        object.__setattr__(self, "bus_ids", bus_ids)
        object.__setattr__(self, "bus_types", bus_types)
        object.__setattr__(self, "p_spec", p_spec)
        object.__setattr__(self, "q_spec", q_spec)
        object.__setattr__(self, "q_min", q_min)
        object.__setattr__(self, "q_max", q_max)
        object.__setattr__(self, "initial_vm", initial_vm)
        object.__setattr__(self, "initial_va", initial_va)
        self._validate_contract()

    @staticmethod
    def _normalize_bus_type(value: PowerFlowBusType | str) -> PowerFlowBusType:
        if isinstance(value, PowerFlowBusType):
            return value
        if not isinstance(value, str):
            raise TypeError("bus_type must be a PowerFlowBusType or string.")
        try:
            return PowerFlowBusType(value.upper().strip())
        except ValueError as exc:
            raise ValueError(f"Unsupported Power Flow bus type: {value!r}.") from exc

    @staticmethod
    def _validate_optional(value: Real | None, name: str) -> float | None:
        return None if value is None else _validate_finite_real(value, name)

    def _validate_contract(self) -> None:
        count = len(self.bus_ids)
        if count == 0:
            raise ValueError("PowerFlowInput must contain at least one bus.")
        if len(set(self.bus_ids)) != count:
            raise ValueError("PowerFlowInput contains duplicate bus IDs.")
        for values, name in ((self.bus_types, "bus_types"), (self.p_spec, "p_spec"), (self.q_spec, "q_spec"), (self.q_min, "q_min"), (self.q_max, "q_max"), (self.initial_vm, "initial_vm"), (self.initial_va, "initial_va")):
            _validate_sequence_length(values, count, name)
        if sum(value is PowerFlowBusType.SLACK for value in self.bus_types) != 1:
            raise ValueError("PowerFlowInput must contain exactly one SLACK bus.")
        for i in range(count):
            if self.q_min[i] is not None and self.q_max[i] is not None and self.q_min[i] > self.q_max[i]:
                raise ValueError(f"q_min must not exceed q_max for bus {self.bus_ids[i]!r}.")
            if self.initial_vm[i] <= 0.0:
                raise ValueError(f"initial_vm must be greater than zero for bus {self.bus_ids[i]!r}.")

    @property
    def bus_count(self) -> int:
        return len(self.bus_ids)

    @property
    def slack_indices(self) -> tuple[int, ...]:
        return tuple(i for i, t in enumerate(self.bus_types) if t is PowerFlowBusType.SLACK)

    @property
    def pv_indices(self) -> tuple[int, ...]:
        return tuple(i for i, t in enumerate(self.bus_types) if t is PowerFlowBusType.PV)

    @property
    def pq_indices(self) -> tuple[int, ...]:
        return tuple(i for i, t in enumerate(self.bus_types) if t is PowerFlowBusType.PQ)

    @property
    def non_slack_indices(self) -> tuple[int, ...]:
        return tuple(i for i, t in enumerate(self.bus_types) if t is not PowerFlowBusType.SLACK)

    def index_of(self, bus_id: str) -> int:
        bus_id = _validate_bus_id(bus_id, "bus_id")
        try:
            return self.bus_ids.index(bus_id)
        except ValueError as exc:
            raise KeyError(bus_id) from exc

    def type_of(self, bus_id: str) -> PowerFlowBusType:
        return self.bus_types[self.index_of(bus_id)]

    def as_dict(self) -> dict[str, object]:
        return {"bus_ids": self.bus_ids, "bus_types": tuple(t.value for t in self.bus_types), "p_spec": self.p_spec, "q_spec": self.q_spec, "q_min": self.q_min, "q_max": self.q_max, "initial_vm": self.initial_vm, "initial_va": self.initial_va}


__all__ = ["PowerFlowBusType", "PowerFlowInput"]
