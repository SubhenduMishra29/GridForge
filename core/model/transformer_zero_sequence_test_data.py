"""Explicit three-test data contract for grounded-wye/grounded-wye transformer Z0.

All three measured driving-point impedances are stored as physical ohms
referred to the HV winding and on the declared common test MVA basis.
The LV open-circuit measurement must already be referred to HV using the
documented turns ratio; no ratio is inferred here. Neutral 3Zn is excluded
from every measurement and is added separately by network preparation.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class TransformerZeroSequenceTwoWindingTestData:
    """Three IEEE-style zero-sequence tests needed to identify a Yg-Yg T model.

    Z1: HV open-circuit test, HV-referred ohms.
    Z2: LV open-circuit test, explicitly referred to HV, ohms.
    Z3: HV short-circuit test, HV-referred ohms.

    Values must share one test MVA basis. The contract deliberately records
    the measured test quantities rather than accepting an inferred Z0.
    """

    hv_open_circuit_z0_ohm: complex
    lv_open_circuit_z0_hv_referred_ohm: complex
    hv_short_circuit_z0_ohm: complex
    test_mva_base: float
    hv_test_voltage_kv: float
    lv_test_voltage_kv: float
    lv_open_circuit_referred_to_hv: bool
    neutral_return_excluded: bool
    source_reference: str

    def __post_init__(self) -> None:
        for name in (
            "hv_open_circuit_z0_ohm",
            "lv_open_circuit_z0_hv_referred_ohm",
            "hv_short_circuit_z0_ohm",
        ):
            value = complex(getattr(self, name))
            if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value) == 0.0:
                raise ValueError(f"{name} must be finite and non-zero.")
            if value.real < 0.0:
                raise ValueError(f"{name} measured resistance must not be negative.")
            object.__setattr__(self, name, value)
        for name in ("test_mva_base", "hv_test_voltage_kv", "lv_test_voltage_kv"):
            value = getattr(self, name)
            if isinstance(value, bool):
                raise TypeError(f"{name} must be a finite positive number.")
            value = float(value)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be a finite positive number.")
            object.__setattr__(self, name, value)
        if type(self.lv_open_circuit_referred_to_hv) is not bool or not self.lv_open_circuit_referred_to_hv:
            raise ValueError("LV open-circuit Z0 must be explicitly referred to the HV winding.")
        if type(self.neutral_return_excluded) is not bool or not self.neutral_return_excluded:
            raise ValueError("All transformer Z0 test values must exclude neutral return impedance.")
        if not isinstance(self.source_reference, str) or not self.source_reference.strip():
            raise ValueError("source_reference must identify the test report or manufacturer data source.")
        object.__setattr__(self, "source_reference", self.source_reference.strip())


__all__ = ["TransformerZeroSequenceTwoWindingTestData"]
