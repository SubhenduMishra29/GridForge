"""Three-phase short-circuit calculation from prepared numerical data."""

from __future__ import annotations

import cmath
import math
from typing import Any

import numpy as np

from .fault_types import FaultType


class SymmetricalFault:
    """Three-phase fault engine with no live-Core dependency."""

    def __init__(self, thevenin_impedance: Any) -> None:
        self.thevenin_impedance = self._validate_complex(thevenin_impedance, "Thevenin impedance")

    @staticmethod
    def _validate_complex(value: Any, name: str) -> complex:
        try:
            value = complex(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"{name} must be a real or complex number.") from exc
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError(f"{name} must be finite.")
        return value

    @staticmethod
    def _validate_bus_index(bus_index: Any) -> int:
        if isinstance(bus_index, bool) or not isinstance(bus_index, (int, np.integer)):
            raise TypeError("bus_index must be an integer.")
        index = int(bus_index)
        if index < 0:
            raise ValueError("bus_index cannot be negative.")
        return index

    @staticmethod
    def _validate_fault_impedance(Zf: Any) -> complex:
        Zf = SymmetricalFault._validate_complex(Zf, "Zf")
        if Zf.real < 0.0:
            raise ValueError("Fault impedance real part cannot be negative.")
        return Zf

    def get_thevenin_impedance(self, bus_index: int | None = None) -> complex:
        """Return the prepared positive-sequence Thevenin impedance."""
        if bus_index is not None:
            self._validate_bus_index(bus_index)
        return self.thevenin_impedance

    def calculate_three_phase_fault(self, bus_index: int, Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        bus_index = self._validate_bus_index(bus_index)
        Vprefault = self._validate_complex(Vprefault, "Vprefault")
        Zf = self._validate_fault_impedance(Zf)
        Z1 = self.thevenin_impedance
        Z_total = self._validate_complex(Z1 + Zf, "total fault impedance")
        if abs(Z_total) <= np.finfo(float).eps:
            raise ValueError("Total fault impedance is zero; three-phase fault current is undefined.")
        fault_current = self._validate_complex(Vprefault / Z_total, "fault current")
        return {
            "fault_type": FaultType.THREE_PHASE.value,
            "bus_index": bus_index,
            "Vprefault": Vprefault,
            "Z1": Z1,
            "Zf": Zf,
            "Z_total": Z_total,
            "fault_current": fault_current,
            "fault_current_magnitude": float(abs(fault_current)),
            "fault_current_angle_deg": float(math.degrees(cmath.phase(fault_current))),
            "balanced": True,
        }

    def calculate(self, bus_index: int, Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        return self.calculate_three_phase_fault(bus_index, Vprefault, Zf)

    def summary(self) -> dict:
        return {
            "calculator": "SymmetricalFault", "version": "2.0",
            "supported_faults": [FaultType.THREE_PHASE.value],
            "method": "Positive-sequence Thevenin impedance",
            "returns_complex_current": True,
        }

    def __repr__(self) -> str:
        return "SymmetricalFault(thevenin_impedance=prepared)"


__all__ = ["SymmetricalFault"]
