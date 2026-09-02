"""Core-independent numerical helpers for short-circuit studies."""

from __future__ import annotations

import cmath
from typing import Any

import numpy as np


class FaultCalculator:
    """Numerical helper operating only on prepared prefault data."""

    def __init__(self, prefault_voltages: dict[Any, complex] | None = None) -> None:
        self._prefault_voltages = {
            key: complex(value) for key, value in (prefault_voltages or {}).items()
        }

    def get_prefault_voltage(self, bus_id: Any) -> complex:
        if bus_id not in self._prefault_voltages:
            raise ValueError(f"Prefault voltage for bus {bus_id!r} was not prepared.")
        return self._prefault_voltages[bus_id]

    @staticmethod
    def complex_voltage(magnitude: Any, angle_rad: Any) -> complex:
        try:
            magnitude = float(magnitude)
            angle_rad = float(angle_rad)
        except (TypeError, ValueError) as exc:
            raise ValueError("Voltage magnitude and angle must be numerical.") from exc
        if not np.isfinite(magnitude) or not np.isfinite(angle_rad) or magnitude < 0.0:
            raise ValueError("Voltage magnitude and angle must be finite and magnitude non-negative.")
        return magnitude * cmath.exp(1j * angle_rad)

    @staticmethod
    def _validate_complex(value: Any, name: str) -> complex:
        try:
            result = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a numerical complex value.") from exc
        if not np.isfinite(result.real) or not np.isfinite(result.imag):
            raise ValueError(f"{name} must be finite.")
        return result

    @staticmethod
    def _validate_fault_impedance(Z_fault: Any) -> complex:
        return FaultCalculator._validate_complex(Z_fault, "Fault impedance")

    def calculate_current(self, V_prefault: Any, Z_fault: Any) -> complex:
        V_prefault = self._validate_complex(V_prefault, "Prefault voltage")
        Z_fault = self._validate_fault_impedance(Z_fault)
        if abs(Z_fault) == 0.0:
            raise ZeroDivisionError("Total fault impedance cannot be zero.")
        return self._validate_complex(V_prefault / Z_fault, "Fault current")

    @staticmethod
    def fault_mva(voltage_kv: Any, current_ka: Any) -> float:
        try:
            voltage_kv = float(voltage_kv)
            current_ka = float(current_ka)
        except (TypeError, ValueError) as exc:
            raise ValueError("Voltage and current must be real numerical values.") from exc
        if not np.isfinite(voltage_kv) or not np.isfinite(current_ka):
            raise ValueError("Voltage and current must be finite.")
        if voltage_kv < 0.0 or current_ka < 0.0:
            raise ValueError("Voltage and current cannot be negative.")
        return float(np.sqrt(3.0) * voltage_kv * current_ka)

    def result(
        self,
        bus_id: Any,
        fault_type: Any,
        current: Any,
        impedance: Any,
        *,
        prefault_voltage: Any | None = None,
        fault_mva: float | None = None,
    ) -> dict:
        current = self._validate_complex(current, "Fault current")
        impedance = self._validate_complex(impedance, "Fault impedance")
        result = {
            "bus": bus_id,
            "fault_type": fault_type,
            "fault_current": current,
            "fault_current_magnitude": float(abs(current)),
            "fault_impedance": impedance,
        }
        if prefault_voltage is not None:
            result["prefault_voltage"] = self._validate_complex(prefault_voltage, "Prefault voltage")
        if fault_mva is not None:
            result["fault_mva"] = float(fault_mva)
        return result

    def summary(self) -> dict:
        return {"component": "FaultCalculator", "version": "2.0", "status": "READY"}

    def __repr__(self) -> str:
        return f"FaultCalculator(prefault_buses={len(self._prefault_voltages)})"


__all__ = ["FaultCalculator"]
