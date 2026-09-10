"""Unsymmetrical short-circuit calculation from frozen sequence networks."""

from __future__ import annotations

import cmath
import math
from typing import Any, Iterable

import numpy as np

from .fault_types import FaultType
from .sequence_snapshot import SequenceNetworkSnapshot


class UnsymmetricalFault:
    """Calculate LG, LL and LLG faults from an immutable sequence snapshot."""

    def __init__(self, sequence_snapshot: SequenceNetworkSnapshot, fault_bus_index: int | None = None) -> None:
        if sequence_snapshot is None:
            raise ValueError("Sequence snapshot cannot be None.")
        self.sequence_snapshot = sequence_snapshot
        self.fault_bus_index = fault_bus_index

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
        value = UnsymmetricalFault._validate_complex(Zf, "Zf")
        if value.real < 0.0:
            raise ValueError("Fault impedance real part cannot be negative.")
        return value

    def _validate_bus_index(self) -> int:
        if isinstance(self.fault_bus_index, bool) or not isinstance(self.fault_bus_index, int):
            raise ValueError("A deterministic fault_bus_index is required for network sequence calculations.")
        index = int(self.fault_bus_index)
        for sequence in ("positive", "negative", "zero"):
            matrix = self.sequence_snapshot.get_matrix(sequence)
            if not 0 <= index < matrix.shape[0]:
                raise IndexError(f"fault_bus_index {index} is outside the {sequence}-sequence matrix.")
        return index

    def _get_sequence_impedances(self, elements: Iterable[Any] | None = None) -> tuple[complex, complex, complex]:
        index = self._validate_bus_index()
        return tuple(self.sequence_snapshot.get_driving_point_impedance(sequence, index) for sequence in ("positive", "negative", "zero"))  # type: ignore[return-value]

    @staticmethod
    def _polar(value: complex) -> tuple[float, float]:
        return float(abs(value)), float(math.degrees(cmath.phase(value)))

    @staticmethod
    def _result_sequence_quantities(I1: complex, I2: complex, I0: complex) -> dict:
        return {
            "sequence_currents": {"I1": I1, "I2": I2, "I0": I0},
            "sequence_current_magnitudes": {"I1": abs(I1), "I2": abs(I2), "I0": abs(I0)},
            "sequence_current_angles_deg": {"I1": math.degrees(cmath.phase(I1)), "I2": math.degrees(cmath.phase(I2)), "I0": math.degrees(cmath.phase(I0))},
        }

    def calculate_lg_fault(self, elements: Iterable[Any] = (), Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        Vprefault = self._validate_complex(Vprefault, "Vprefault")
        Zf = self._validate_fault_impedance(Zf)
        Z1, Z2, Z0 = self._get_sequence_impedances(elements)
        total = Z1 + Z2 + Z0 + 3.0 * Zf
        if abs(total) <= np.finfo(float).eps:
            raise ValueError("LG total sequence impedance is zero; fault current is undefined.")
        I1 = Vprefault / total
        If = 3.0 * I1
        mag, angle = self._polar(If)
        result = {"fault_type": FaultType.SINGLE_LINE_GROUND.value, "Vprefault": Vprefault, "Z1": Z1, "Z2": Z2, "Z0": Z0, "Zf": Zf, "Z_total": total, "fault_current": If, "fault_current_magnitude": mag, "fault_current_angle_deg": angle, "ground_current": If, "ground_current_magnitude": mag}
        result.update(self._result_sequence_quantities(I1, I1, I1))
        return result

    def calculate_ll_fault(self, elements: Iterable[Any] = (), Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        Vprefault = self._validate_complex(Vprefault, "Vprefault")
        Zf = self._validate_fault_impedance(Zf)
        Z1, Z2, Z0 = self._get_sequence_impedances(elements)
        total = Z1 + Z2 + Zf
        if abs(total) <= np.finfo(float).eps:
            raise ValueError("LL total sequence impedance is zero; fault current is undefined.")
        I1 = Vprefault / total
        I2 = -I1
        a = cmath.exp(1j * 2.0 * math.pi / 3.0)
        Ia = I1 + I2
        Ib = (a ** 2) * I1 + a * I2
        Ic = a * I1 + (a ** 2) * I2
        mag, angle = self._polar(Ib)
        result = {"fault_type": FaultType.LINE_LINE.value, "Vprefault": Vprefault, "Z1": Z1, "Z2": Z2, "Z0": Z0, "Zf": Zf, "Z_total": total, "fault_current": Ib, "fault_current_magnitude": mag, "fault_current_angle_deg": angle, "phase_currents": {"Ia": Ia, "Ib": Ib, "Ic": Ic}, "phase_current_magnitudes": {"Ia": abs(Ia), "Ib": abs(Ib), "Ic": abs(Ic)}}
        result.update(self._result_sequence_quantities(I1, I2, 0.0j))
        return result

    def calculate_llg_fault(self, elements: Iterable[Any] = (), Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        Vprefault = self._validate_complex(Vprefault, "Vprefault")
        Zf = self._validate_fault_impedance(Zf)
        Z1, Z2, Z0 = self._get_sequence_impedances(elements)
        zg = Z0 + 3.0 * Zf
        coupling = Z2 + zg
        if abs(coupling) <= np.finfo(float).eps:
            raise ValueError("LLG negative/zero-sequence coupling impedance is zero.")
        parallel = Z2 * zg / coupling
        total = Z1 + parallel
        if abs(total) <= np.finfo(float).eps:
            raise ValueError("LLG total sequence impedance is zero; fault current is undefined.")
        I1 = Vprefault / total
        I2 = -I1 * zg / coupling
        I0 = -I1 * Z2 / coupling
        a = cmath.exp(1j * 2.0 * math.pi / 3.0)
        Ia = I0 + I1 + I2
        Ib = I0 + (a ** 2) * I1 + a * I2
        Ic = I0 + a * I1 + (a ** 2) * I2
        mag, angle = self._polar(Ia)
        result = {"fault_type": FaultType.DOUBLE_LINE_GROUND.value, "Vprefault": Vprefault, "Z1": Z1, "Z2": Z2, "Z0": Z0, "Zf": Zf, "Zg": zg, "Zparallel": parallel, "Z_total": total, "fault_current": Ia, "fault_current_magnitude": mag, "fault_current_angle_deg": angle, "phase_currents": {"Ia": Ia, "Ib": Ib, "Ic": Ic}, "phase_current_magnitudes": {"Ia": abs(Ia), "Ib": abs(Ib), "Ic": abs(Ic)}, "ground_current": Ia + Ib + Ic, "ground_current_magnitude": abs(Ia + Ib + Ic)}
        result.update(self._result_sequence_quantities(I1, I2, I0))
        return result

    def calculate(self, fault_type: FaultType | str, elements: Iterable[Any] = (), Vprefault: Any = 1.0 + 0.0j, Zf: Any = 0.0 + 0.0j) -> dict:
        value = fault_type.value if isinstance(fault_type, FaultType) else fault_type.upper() if isinstance(fault_type, str) else None
        if value == FaultType.SINGLE_LINE_GROUND.value:
            return self.calculate_lg_fault(elements, Vprefault, Zf)
        if value == FaultType.LINE_LINE.value:
            return self.calculate_ll_fault(elements, Vprefault, Zf)
        if value == FaultType.DOUBLE_LINE_GROUND.value:
            return self.calculate_llg_fault(elements, Vprefault, Zf)
        raise ValueError(f"Unsupported unsymmetrical fault type: {fault_type}")

    def summary(self) -> dict:
        return {"calculator": "UnsymmetricalFault", "version": "2.0", "supported_faults": [FaultType.SINGLE_LINE_GROUND.value, FaultType.LINE_LINE.value, FaultType.DOUBLE_LINE_GROUND.value], "sequence_networks": ["positive", "negative", "zero"], "returns_sequence_currents": True, "returns_phase_currents": True}

    def __repr__(self) -> str:
        return "UnsymmetricalFault(sequence_snapshot=SequenceNetworkSnapshot)"


__all__ = ["UnsymmetricalFault"]
