"""Immutable numerical input contract for short-circuit execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .fault_types import FaultType
from .sequence_snapshot import SequenceNetworkSnapshot


@dataclass(frozen=True, slots=True)
class ShortCircuitInput:
    """Prepared, immutable data consumed by ``ShortCircuitSolver``.

    All Core reads occur before construction.  The solver receives this
    value object and therefore has no live ``Network``, ``Bus`` or mutable
    ``SequenceNetwork`` dependency.
    """

    fault_type: FaultType
    fault_bus_index: int
    fault_bus_id: Any
    prefault_voltage: complex
    fault_impedance: complex
    bus_ids: tuple[Any, ...]
    thevenin_impedance: complex | None = None
    zbus: tuple[tuple[complex, ...], ...] | None = None
    sequence_snapshot: SequenceNetworkSnapshot | None = None
    sequence_elements: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.fault_bus_index, bool) or not isinstance(self.fault_bus_index, int):
            raise TypeError("fault_bus_index must be an integer.")
        if not self.bus_ids:
            raise ValueError("bus_ids cannot be empty.")
        if not 0 <= self.fault_bus_index < len(self.bus_ids):
            raise IndexError("fault_bus_index is outside bus_ids.")
        if self.bus_ids[self.fault_bus_index] != self.fault_bus_id:
            raise ValueError("fault_bus_id must match bus_ids[fault_bus_index].")
        object.__setattr__(self, "prefault_voltage", complex(self.prefault_voltage))
        object.__setattr__(self, "fault_impedance", complex(self.fault_impedance))
        object.__setattr__(self, "bus_ids", tuple(self.bus_ids))
        object.__setattr__(self, "sequence_elements", tuple(self.sequence_elements))
        if self.zbus is not None:
            zbus = tuple(tuple(complex(value) for value in row) for row in self.zbus)
            if len(zbus) != len(self.bus_ids) or any(len(row) != len(self.bus_ids) for row in zbus):
                raise ValueError("zbus dimensions must match bus_ids.")
            object.__setattr__(self, "zbus", zbus)
        if self.thevenin_impedance is not None:
            object.__setattr__(self, "thevenin_impedance", complex(self.thevenin_impedance))
