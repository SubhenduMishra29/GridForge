"""Test-derived zero-sequence T equivalent for grounded-wye/grounded-wye transformers.

The three test values are HV-referred physical ohms. This module derives
network parameters only; it does not mutate a Transformer or stamp a Ybus.
"""
from __future__ import annotations

from dataclasses import dataclass
import cmath
import math

from core.model.transformer_zero_sequence_test_data import TransformerZeroSequenceTwoWindingTestData


@dataclass(frozen=True, slots=True)
class TransformerZeroSequenceTEquivalent:
    """HV-referred zero-sequence T-network series/shunt parameters."""

    hv_series_ohm: complex
    lv_series_hv_referred_ohm: complex
    magnetizing_shunt_ohm: complex
    test_data: TransformerZeroSequenceTwoWindingTestData


def derive_transformer_zero_sequence_t_equivalent(
    test_data: TransformerZeroSequenceTwoWindingTestData,
) -> TransformerZeroSequenceTEquivalent:
    """Derive the T model from HV-open, LV-open and HV-short Z0 tests.

    Let Z1 = ZH + ZM, Z2' = ZX' + ZM and
    Z3 = ZH + (ZM || ZX'). Then
      ZM = sqrt(Z2' * (Z1 - Z3)),
      ZH = Z1 - ZM,
      ZX' = Z2' - ZM.

    The square-root sign is selected deterministically with non-negative real
    part. Negative real parts in an individual T leg are not independently
    rejected: they can occur in a valid fitted equivalent. The measured
    driving-point impedances themselves must be passive (enforced by input).
    """
    if not isinstance(test_data, TransformerZeroSequenceTwoWindingTestData):
        raise TypeError("Explicit TransformerZeroSequenceTwoWindingTestData is required.")
    z1 = complex(test_data.hv_open_circuit_z0_ohm)
    z2 = complex(test_data.lv_open_circuit_z0_hv_referred_ohm)
    z3 = complex(test_data.hv_short_circuit_z0_ohm)
    radicand = z2 * (z1 - z3)
    if abs(radicand) == 0.0:
        raise ValueError("The three zero-sequence tests do not identify a finite magnetizing branch.")
    zm = cmath.sqrt(radicand)
    alternate = -zm
    if alternate.real > zm.real or (math.isclose(alternate.real, zm.real, abs_tol=1e-12) and alternate.imag > zm.imag):
        zm = alternate
    zh = z1 - zm
    zx = z2 - zm
    for label, value in (("HV series", zh), ("LV series referred to HV", zx), ("magnetizing", zm)):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError(f"Derived transformer {label} impedance is non-finite.")
    if abs(zm) == 0.0 or abs(zx + zm) == 0.0:
        raise ValueError("Derived transformer T equivalent is singular.")
    reconstructed_z3 = zh + (zm * zx / (zm + zx))
    scale = max(1.0, abs(z1), abs(z2), abs(z3))
    if abs((zh + zm) - z1) > 1e-9 * scale:
        raise ValueError("Derived T equivalent does not reproduce the HV open-circuit test.")
    if abs((zx + zm) - z2) > 1e-9 * scale:
        raise ValueError("Derived T equivalent does not reproduce the LV open-circuit test.")
    if abs(reconstructed_z3 - z3) > 1e-7 * scale:
        raise ValueError("The three measured zero-sequence tests are mutually inconsistent with a T equivalent.")
    return TransformerZeroSequenceTEquivalent(
        hv_series_ohm=zh,
        lv_series_hv_referred_ohm=zx,
        magnetizing_shunt_ohm=zm,
        test_data=test_data,
    )


__all__ = ["TransformerZeroSequenceTEquivalent", "derive_transformer_zero_sequence_t_equivalent"]
