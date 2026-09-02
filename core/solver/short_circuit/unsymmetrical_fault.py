"""Unsymmetrical short-circuit calculation engine using frozen sequence data."""

from __future__ import annotations

import cmath
import math
from typing import Any, Iterable

import numpy as np

from .fault_types import FaultType
from .sequence_snapshot import SequenceNetworkSnapshot


class UnsymmetricalFault:
    """Calculate LG, LL and LLG faults from an immutable sequence snapshot."""

    def __init__(self, sequence_snapshot: SequenceNetworkSnapshot) -> None:
        if sequence_snapshot is None:
            raise ValueError("Sequence snapshot cannot be None.")
        self.sequence_snapshot = sequence_snapshot

    @staticmethod
    def _validate_elements(elements: Iterable[Any]) -> list[Any]:
        if elements is None:
            raise ValueError("elements cannot be None.")
        try:
            result = list(elements)
        except TypeError as exc:
            raise TypeError("elements must be an iterable.") from exc
        if not result:
            raise ValueError("At least one sequence-network element is required.")
        return result

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
    def _validate_fault_impedance(Zf: Any) -> complex:
        Zf = UnsymmetricalFault._validate_complex(Zf, "Zf")
        if Zf.real < 0.0:
            raise ValueError("Fault impedance real part cannot be negative.")
        return Zf

    @staticmethod
    def _validate_total_impedance(Z: complex, name: str) -> complex:
        Z = UnsymmetricalFault._validate_complex(Z, name)
        if abs(Z) <= np.finfo(float).eps:
            raise ValueError(f"{name} is zero; fault current is undefined.")
        return Z

    def _get_sequence_impedances(self, elements: Iterable[Any]) -> tuple[complex, complex, complex]:
        elements = self._validate_elements(elements)
        try:
            return (
                self.sequence_snapshot.total_impedance(elements, "positive"),
                self.sequence_snapshot.total_impedance(elements, "negative"),
                self.sequence_snapshot.total_impedance(elements, "zero"),
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to obtain sequence impedances: {exc}") from exc

    @staticmethod
    def _polar(value: complex) -> tuple[float, float]:
        return float(abs(value)), float(math.degrees(cmath.phase(value)))

    @staticmethod
    def _result_sequence_quantities(I1: complex, I2: complex, I0: complex) -> dict:
        I1_mag, I1_ang = UnsymmetricalFault._polar(I1)
        I2_mag, I2_ang = UnsymmetricalFault._polar(I2)
        I0_mag, I0_ang = UnsymmetricalFault._polar(I0)
        return {
            "sequence_currents": {"I1": I1, "I2": I2, "I0": I0},
            "sequence_current_magnitudes": {"I1": I1_mag, "I2": I2_mag, "I0": I0_mag},
            "sequence_current_angles_deg": {"I1": I1_ang, "I2": I2_ang, "I0": I0_ang},
        }

    def calculate_lg_fault(self, elements: Iterable[Any], Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        Vprefault = self._validate_complex(Vprefault, "Vprefault")
        Zf = self._validate_fault_impedance(Zf)
        Z1, Z2, Z0 = self._get_sequence_impedances(elements)
        Z_total = self._validate_total_impedance(Z1 + Z2 + Z0 + 3.0 * Zf, "LG total sequence impedance")
        I1 = Vprefault / Z_total
        I2 = I1
        I0 = I1
        If = 3.0 * I0
        If_mag, If_ang = self._polar(If)
        result = {
            "fault_type": FaultType.SINGLE_LINE_GROUND.value,
            "Vprefault": Vprefault, "Z1": Z1, "Z2": Z2, "Z0": Z0, "Zf": Zf,
            "Z_total": Z_total, "fault_current": If,
            "fault_current_magnitude": If_mag, "fault_current_angle_deg": If_ang,
            "ground_current": If, "ground_current_magnitude": If_mag,
        }
        result.update(self._result_sequence_quantities(I1, I2, I0))
        return result

    def calculate_ll_fault(self, elements: Iterable[Any], Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        Vprefault = self._validate_complex(Vprefault, "Vprefault")
        Zf = self._validate_fault_impedance(Zf)
        Z1, Z2, Z0 = self._get_sequence_impedances(elements)
        Z_total = self._validate_total_impedance(Z1 + Z2 + Zf, "LL total sequence impedance")
        I1 = Vprefault / Z_total
        I2 = -I1
        I0 = 0.0 + 0.0j
        a = cmath.exp(1j * 2.0 * math.pi / 3.0)
        Ia = I0 + I1 + I2
        Ib = I0 + (a ** 2) * I1 + a * I2
        Ic = I0 + a * I1 + (a ** 2) * I2
        If = Ib
        If_mag, If_ang = self._polar(If)
        result = {
            "fault_type": FaultType.LINE_LINE.value,
            "Vprefault": Vprefault, "Z1": Z1, "Z2": Z2, "Z0": Z0, "Zf": Zf,
            "Z_total": Z_total, "fault_current": If,
            "fault_current_magnitude": If_mag, "fault_current_angle_deg": If_ang,
            "phase_currents": {"Ia": Ia, "Ib": Ib, "Ic": Ic},
            "phase_current_magnitudes": {"Ia": float(abs(Ia)), "Ib": float(abs(Ib)), "Ic": float(abs(Ic))},
        }
        result.update(self._result_sequence_quantities(I1, I2, I0))
        return result

    def calculate_llg_fault(self, elements: Iterable[Any], Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        Vprefault = self._validate_complex(Vprefault, "Vprefault")
        Zf = self._validate_fault_impedance(Zf)
        Z1, Z2, Z0 = self._get_sequence_impedances(elements)
        Zg = Z0 + 3.0 * Zf
        denominator = self._validate_total_impedance(Z2 + Zg, "LLG negative/zero-sequence coupling impedance")
        Zparallel = Z2 * Zg / denominator
        Z_total = self._validate_total_impedance(Z1 + Zparallel, "LLG total sequence impedance")
        I1 = Vprefault / Z_total
        I2 = -I1 * Zg / denominator
        I0 = -I1 * Z2 / denominator
        a = cmath.exp(1j * 2.0 * math.pi / 3.0)
        Ia = I0 + I1 + I2
        Ib = I0 + (a ** 2) * I1 + a * I2
        Ic = I0 + a * I1 + (a ** 2) * I2
        Ig = Ia + Ib + Ic
        If_mag, If_ang = self._polar(Ia)
        result = {
            "fault_type": FaultType.DOUBLE_LINE_GROUND.value,
            "Vprefault": Vprefault, "Z1": Z1, "Z2": Z2, "Z0": Z0, "Zf": Zf,
            "Zg": Zg, "Zparallel": Zparallel, "Z_total": Z_total,
            "fault_current": Ia, "fault_current_magnitude": If_mag,
            "fault_current_angle_deg": If_ang,
            "phase_currents": {"Ia": Ia, "Ib": Ib, "Ic": Ic},
            "phase_current_magnitudes": {"Ia": float(abs(Ia)), "Ib": float(abs(Ib)), "Ic": float(abs(Ic))},
            "ground_current": Ig, "ground_current_magnitude": float(abs(Ig)),
        }
        result.update(self._result_sequence_quantities(I1, I2, I0))
        return result

    def calculate(self, fault_type: FaultType | str, elements: Iterable[Any], Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        value = fault_type.value if isinstance(fault_type, FaultType) else fault_type.upper() if isinstance(fault_type, str) else None
        if value == FaultType.SINGLE_LINE_GROUND.value:
            return self.calculate_lg_fault(elements, Vprefault, Zf)
        if value == FaultType.LINE_LINE.value:
            return self.calculate_ll_fault(elements, Vprefault, Zf)
        if value == FaultType.DOUBLE_LINE_GROUND.value:
            return self.calculate_llg_fault(elements, Vprefault, Zf)
        raise ValueError(f"Unsupported unsymmetrical fault type: {fault_type}")

    def summary(self) -> dict:
        return {
            "calculator": "UnsymmetricalFault", "version": "2.0",
            "supported_faults": [FaultType.SINGLE_LINE_GROUND.value, FaultType.LINE_LINE.value, FaultType.DOUBLE_LINE_GROUND.value],
            "sequence_networks": ["positive", "negative", "zero"],
            "returns_sequence_currents": True, "returns_phase_currents": True,
        }

    def __repr__(self) -> str:
        return "UnsymmetricalFault(sequence_snapshot=SequenceNetworkSnapshot)"


__all__ = ["UnsymmetricalFault"]
