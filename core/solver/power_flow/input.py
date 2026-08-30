# ============================================================
# File: core/solver/power_flow/input.py
# GridForge V2 — Power Flow Input Contract
# Author: Subhendu Mishra
# ============================================================

"""
Power Flow numerical input contract.

This module defines the immutable study-specific input boundary between
the authoritative electrical Network and the Power Flow numerical solver.

Responsibilities
----------------
PowerFlowInput represents the numerical interpretation of a prepared
Network for one Power Flow execution.

It contains only solver-relevant values:

    - stable bus IDs
    - bus types
    - specified active power
    - specified reactive power
    - reactive-power limits
    - initial voltage magnitudes
    - initial voltage angles

It deliberately does NOT contain:

    - Bus objects
    - Network objects
    - NetworkRegistry
    - TopologyManager
    - BusIndex
    - YBus objects
    - UI/SLD objects
    - solver instances
    - mutable iterative solver state

The authoritative Model/Network remains outside the solver runtime.

The iterative numerical state belongs to the numerical execution layer
and is represented separately by BusState or equivalent solver-local
arrays.

Ordering
--------
All per-bus arrays use one explicit ordering:

    bus_ids[index]

The caller responsible for constructing PowerFlowInput must obtain the
ordering from the prepared Network/BusIndex/YBus contract and must not
silently reorder buses during solver execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from numbers import Real
from typing import Sequence


class PowerFlowBusType(str, Enum):
    """Bus classification used by the Power Flow study."""

    PQ = "PQ"
    PV = "PV"
    SLACK = "SLACK"


def _validate_finite_real(value: Real, name: str) -> float:
    """Validate and normalize a finite real number."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number.")

    value = float(value)

    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")

    return value


def _validate_bus_id(value: str, name: str) -> str:
    """Validate a stable bus identifier."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")

    value = value.strip()

    if not value:
        raise ValueError(f"{name} must not be empty.")

    return value


def _validate_sequence_length(
    values: Sequence[object],
    expected: int,
    name: str,
) -> None:
    """Validate that a per-bus sequence has the expected length."""
    if len(values) != expected:
        raise ValueError(
            f"{name} length must be {expected}; "
            f"received {len(values)}."
        )


@dataclass(frozen=True, slots=True)
class PowerFlowInput:
    """
    Immutable numerical input for one Power Flow study.

    Every per-bus sequence is aligned with ``bus_ids``.

    No physical Model or Network object is retained by this class.
    """

    bus_ids: tuple[str, ...]
    bus_types: tuple[PowerFlowBusType, ...]
    p_spec: tuple[float, ...]
    q_spec: tuple[float, ...]
    q_min: tuple[float | None, ...]
    q_max: tuple[float | None, ...]
    initial_vm: tuple[float, ...]
    initial_va: tuple[float, ...]

    def __post_init__(self) -> None:
        """Validate the complete immutable input contract."""

        bus_ids = tuple(
            _validate_bus_id(bus_id, "bus_id")
            for bus_id in self.bus_ids
        )

        bus_types = tuple(
            self._normalize_bus_type(bus_type)
            for bus_type in self.bus_types
        )

        p_spec = tuple(
            _validate_finite_real(value, "p_spec")
            for value in self.p_spec
        )

        q_spec = tuple(
            _validate_finite_real(value, "q_spec")
            for value in self.q_spec
        )

        q_min = tuple(
            self._validate_optional_finite_real(value, "q_min")
            for value in self.q_min
        )

        q_max = tuple(
            self._validate_optional_finite_real(value, "q_max")
            for value in self.q_max
        )

        initial_vm = tuple(
            _validate_finite_real(value, "initial_vm")
            for value in self.initial_vm
        )

        initial_va = tuple(
            _validate_finite_real(value, "initial_va")
            for value in self.initial_va
        )

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
    def _normalize_bus_type(
        value: PowerFlowBusType | str,
    ) -> PowerFlowBusType:
        """Normalize a bus type to PowerFlowBusType."""
        if isinstance(value, PowerFlowBusType):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "bus_type must be a PowerFlowBusType or string."
            )

        try:
            return PowerFlowBusType(value.upper().strip())
        except ValueError as exc:
            raise ValueError(
                f"Unsupported Power Flow bus type: {value!r}."
            ) from exc

    @staticmethod
    def _validate_optional_finite_real(
        value: Real | None,
        name: str,
    ) -> float | None:
        """Validate an optional finite real number."""
        if value is None:
            return None

        return _validate_finite_real(value, name)

    def _validate_contract(self) -> None:
        """Validate cross-field Power Flow invariants."""

        count = len(self.bus_ids)

        if count == 0:
            raise ValueError(
                "PowerFlowInput must contain at least one bus."
            )

        if len(set(self.bus_ids)) != count:
            raise ValueError(
                "PowerFlowInput contains duplicate bus IDs."
            )

        _validate_sequence_length(
            self.bus_types,
            count,
            "bus_types",
        )
        _validate_sequence_length(
            self.p_spec,
            count,
            "p_spec",
        )
        _validate_sequence_length(
            self.q_spec,
            count,
            "q_spec",
        )
        _validate_sequence_length(
            self.q_min,
            count,
            "q_min",
        )
        _validate_sequence_length(
            self.q_max,
            count,
            "q_max",
        )
        _validate_sequence_length(
            self.initial_vm,
            count,
            "initial_vm",
        )
        _validate_sequence_length(
            self.initial_va,
            count,
            "initial_va",
        )

        slack_count = sum(
            bus_type is PowerFlowBusType.SLACK
            for bus_type in self.bus_types
        )

        if slack_count != 1:
            raise ValueError(
                "PowerFlowInput must contain exactly one SLACK bus."
            )

        for index, bus_type in enumerate(self.bus_types):
            q_min = self.q_min[index]
            q_max = self.q_max[index]

            if (
                q_min is not None
                and q_max is not None
                and q_min > q_max
            ):
                raise ValueError(
                    "q_min must not exceed q_max for bus "
                    f"{self.bus_ids[index]!r}."
                )

            if self.initial_vm[index] <= 0.0:
                raise ValueError(
                    "initial_vm must be greater than zero for bus "
                    f"{self.bus_ids[index]!r}."
                )

            if bus_type is PowerFlowBusType.SLACK:
                if (
                    self.q_min[index] is not None
                    or self.q_max[index] is not None
                ):
                    # Q limits may exist in the source model, but they are
                    # not solver-enforced as PV-limit switching data for the
                    # slack equation.
                    pass

    @property
    def bus_count(self) -> int:
        """Return the number of buses."""
        return len(self.bus_ids)

    @property
    def slack_indices(self) -> tuple[int, ...]:
        """Return indices of SLACK buses."""
        return tuple(
            index
            for index, bus_type in enumerate(self.bus_types)
            if bus_type is PowerFlowBusType.SLACK
        )

    @property
    def pv_indices(self) -> tuple[int, ...]:
        """Return indices of PV buses."""
        return tuple(
            index
            for index, bus_type in enumerate(self.bus_types)
            if bus_type is PowerFlowBusType.PV
        )

    @property
    def pq_indices(self) -> tuple[int, ...]:
        """Return indices of PQ buses."""
        return tuple(
            index
            for index, bus_type in enumerate(self.bus_types)
            if bus_type is PowerFlowBusType.PQ
        )

    @property
    def non_slack_indices(self) -> tuple[int, ...]:
        """Return indices of all non-SLACK buses."""
        return tuple(
            index
            for index, bus_type in enumerate(self.bus_types)
            if bus_type is not PowerFlowBusType.SLACK
        )

    def index_of(self, bus_id: str) -> int:
        """Return the numerical index associated with a bus ID."""
        bus_id = _validate_bus_id(bus_id, "bus_id")

        try:
            return self.bus_ids.index(bus_id)
        except ValueError as exc:
            raise KeyError(bus_id) from exc

    def type_of(self, bus_id: str) -> PowerFlowBusType:
        """Return the Power Flow type of a bus."""
        return self.bus_types[self.index_of(bus_id)]

    def as_dict(self) -> dict[str, object]:
        """Return a backend-neutral immutable-input representation."""
        return {
            "bus_ids": self.bus_ids,
            "bus_types": tuple(
                bus_type.value
                for bus_type in self.bus_types
            ),
            "p_spec": self.p_spec,
            "q_spec": self.q_spec,
            "q_min": self.q_min,
            "q_max": self.q_max,
            "initial_vm": self.initial_vm,
            "initial_va": self.initial_va,
        }


__all__ = [
    "PowerFlowBusType",
    "PowerFlowInput",
]
