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


@dataclass(frozen=True, slots=True)
class TransformerZeroSequenceTwoBusStamp:
    """Reduced two-terminal zero-sequence admittance stamp in study per unit."""

    transformer_id: str
    hv_bus_id: str
    lv_bus_id: str
    hv_terminal_role: str
    lv_terminal_role: str
    hv_bus_index: int
    lv_bus_index: int
    y_hh_pu: complex
    y_hl_pu: complex
    y_ll_pu: complex
    hv_series_with_neutral_ohm: complex
    lv_series_with_neutral_hv_referred_ohm: complex
    magnetizing_shunt_ohm: complex
    hv_neutral_3zn_ohm: complex
    lv_neutral_3zn_ohm: complex
    lv_neutral_3zn_hv_referred_ohm: complex
    base_mva: float
    hv_base_voltage_kv: float
    lv_base_voltage_kv: float
    test_data: TransformerZeroSequenceTwoWindingTestData

    def __post_init__(self) -> None:
        if not self.transformer_id or not self.hv_bus_id or not self.lv_bus_id or self.hv_bus_id == self.lv_bus_id:
            raise ValueError("Two-Bus transformer zero-sequence stamp requires distinct Bus identities.")
        if self.hv_terminal_role not in {"FROM", "TO"} or self.lv_terminal_role not in {"FROM", "TO"} or self.hv_terminal_role == self.lv_terminal_role:
            raise ValueError("Two-Bus transformer stamp requires distinct canonical HV/LV terminal roles.")
        for name in ("hv_bus_index", "lv_bus_index"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        for name in ("y_hh_pu", "y_hl_pu", "y_ll_pu", "hv_series_with_neutral_ohm",
                     "lv_series_with_neutral_hv_referred_ohm", "magnetizing_shunt_ohm",
                     "hv_neutral_3zn_ohm", "lv_neutral_3zn_ohm", "lv_neutral_3zn_hv_referred_ohm"):
            value = complex(getattr(self, name))
            if not math.isfinite(value.real) or not math.isfinite(value.imag):
                raise ValueError(f"{name} must be finite.")
            object.__setattr__(self, name, value)
        if any(abs(getattr(self, name)) == 0.0 for name in ("y_hh_pu", "y_ll_pu")):
            raise ValueError("Two-Bus transformer diagonal admittances must be non-zero.")
        for name in ("base_mva", "hv_base_voltage_kv", "lv_base_voltage_kv"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive.")
            object.__setattr__(self, name, value)


def build_transformer_zero_sequence_two_bus_stamp(
    transformer: Any,
    hv_bus: Any,
    lv_bus: Any,
    *,
    base_mva: float,
    hv_terminal_role: str,
    lv_terminal_role: str,
    hv_bus_index: int,
    lv_bus_index: int,
) -> TransformerZeroSequenceTwoBusStamp:
    """Build a Yg-Yg T-equivalent stamp, adding each neutral 3Zn once.

    The LV open-circuit and short-circuit test model is referred to HV. The
    LV neutral return is therefore referred to HV by (V_H/V_L)^2. The common
    system per-unit base is valid only when the two Bus voltage bases match
    the explicit test winding voltage bases; no ratio is guessed.
    """
    from core.model.transformer import TransformerWindingConnection

    if transformer.hv_winding_connection is not TransformerWindingConnection.WYE_GROUNDED or transformer.lv_winding_connection is not TransformerWindingConnection.WYE_GROUNDED:
        raise ValueError("Two-Bus zero-sequence stamp requires grounded-wye on both transformer windings.")
    if transformer.zero_sequence_two_winding_test_data is None:
        raise ValueError("Explicit three-test transformer zero-sequence data is required.")
    if transformer.hv_neutral_grounding_impedance_ohm is None or transformer.lv_neutral_grounding_impedance_ohm is None:
        raise ValueError("Both grounded-wye neutral grounding impedances must be explicit.")
    if isinstance(base_mva, bool) or not math.isfinite(float(base_mva)) or float(base_mva) <= 0.0:
        raise ValueError("A finite positive study base_mva is required.")
    if transformer.hv_terminal_role != hv_terminal_role or transformer.lv_terminal_role != lv_terminal_role:
        raise ValueError("Resolved terminal roles do not match the transformer's declared HV/LV mapping.")
    data = transformer.zero_sequence_two_winding_test_data
    hv_kv = float(getattr(hv_bus, "nominal_voltage_kv", 0.0))
    lv_kv = float(getattr(lv_bus, "nominal_voltage_kv", 0.0))
    for label, actual, declared in (("HV", hv_kv, data.hv_test_voltage_kv), ("LV", lv_kv, data.lv_test_voltage_kv)):
        if not math.isfinite(actual) or actual <= 0.0:
            raise ValueError(f"Transformer '{transformer.id}' {label} Bus requires a positive nominal voltage.")
        if not math.isclose(actual, declared, rel_tol=1e-6, abs_tol=1e-9):
            raise ValueError(f"Transformer '{transformer.id}' {label} Bus base {actual} kV does not match declared test base {declared} kV.")
    if not math.isclose(hv_kv / lv_kv, data.hv_test_voltage_kv / data.lv_test_voltage_kv, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError(f"Transformer '{transformer.id}' winding voltage ratio does not match the explicit three-test bases.")
    if not (math.isclose(float(transformer.tap), 1.0, rel_tol=0.0, abs_tol=1e-12) and math.isclose(float(transformer.shift), 0.0, rel_tol=0.0, abs_tol=1e-12)):
        raise ValueError("D14I grounded-wye/grounded-wye T stamp currently requires unity tap and zero phase shift; tap-adjusted Z0 test interpretation is not enabled.")
    equivalent = derive_transformer_zero_sequence_t_equivalent(data)
    ratio_sq = (data.hv_test_voltage_kv / data.lv_test_voltage_kv) ** 2
    neutral_hv = 3.0 * complex(transformer.hv_neutral_grounding_impedance_ohm)
    neutral_lv = 3.0 * complex(transformer.lv_neutral_grounding_impedance_ohm)
    neutral_lv_hv = neutral_lv * ratio_sq
    z_h = equivalent.hv_series_ohm + neutral_hv
    z_l = equivalent.lv_series_hv_referred_ohm + neutral_lv_hv
    z_m = equivalent.magnetizing_shunt_ohm
    if any(not math.isfinite(v.real) or not math.isfinite(v.imag) or abs(v) == 0.0 for v in (z_h, z_l, z_m)):
        raise ValueError("Transformer T-equivalent branch impedance is zero or non-finite after neutral grounding is applied.")
    y_h, y_l, y_m = 1.0 / z_h, 1.0 / z_l, 1.0 / z_m
    central = y_h + y_l + y_m
    if not math.isfinite(central.real) or not math.isfinite(central.imag) or abs(central) == 0.0:
        raise ValueError("Transformer T-equivalent central-node admittance is singular.")
    y_hh_ohm = y_h - y_h * y_h / central
    y_ll_ohm = y_l - y_l * y_l / central
    y_hl_ohm = -y_h * y_l / central
    z_base_h = data.hv_test_voltage_kv ** 2 / float(base_mva)
    # HV-referred ohmic admittance is converted on HV base. With aligned
    # winding voltage bases, this is also the correct LV per-unit stamp.
    scale = z_base_h
    return TransformerZeroSequenceTwoBusStamp(
        transformer_id=str(transformer.id), hv_bus_id=str(hv_bus.id), lv_bus_id=str(lv_bus.id),
        hv_terminal_role=hv_terminal_role, lv_terminal_role=lv_terminal_role,
        hv_bus_index=hv_bus_index, lv_bus_index=lv_bus_index,
        y_hh_pu=y_hh_ohm * scale, y_hl_pu=y_hl_ohm * scale, y_ll_pu=y_ll_ohm * scale,
        hv_series_with_neutral_ohm=z_h, lv_series_with_neutral_hv_referred_ohm=z_l,
        magnetizing_shunt_ohm=z_m, hv_neutral_3zn_ohm=neutral_hv,
        lv_neutral_3zn_ohm=neutral_lv, lv_neutral_3zn_hv_referred_ohm=neutral_lv_hv,
        base_mva=float(base_mva), hv_base_voltage_kv=hv_kv, lv_base_voltage_kv=lv_kv,
        test_data=data,
    )


__all__ = ["TransformerZeroSequenceTEquivalent", "TransformerZeroSequenceTwoBusStamp", "derive_transformer_zero_sequence_t_equivalent", "build_transformer_zero_sequence_two_bus_stamp"]

