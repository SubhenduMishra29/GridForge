# ============================================================
# File: tests/core/test_gf_aud_210_line_contract.py
# GridForge V2 — GF-AUD-210 Line Contract Tests
# Author: Subhendu Mishra
# ============================================================

from core.model.line import Line


def test_line_exposes_explicit_engineering_electrical_parameters():
    line = Line(
        id="L1",
        resistance_ohm=1.0,
        reactance_ohm=2.0,
        shunt_susceptance_siemens=0.001,
    )

    assert line.resistance_ohm == 1.0
    assert line.reactance_ohm == 2.0
    assert line.shunt_susceptance_siemens == 0.001


def test_line_engineering_values_are_not_named_as_per_unit():
    line = Line(
        id="L1",
        resistance_ohm=10.0,
        reactance_ohm=20.0,
    )

    assert line.resistance_ohm == 10.0
    assert line.reactance_ohm == 20.0


def test_line_series_and_shunt_properties_use_engineering_contract():
    line = Line(
        id="L1",
        resistance_ohm=1.0,
        reactance_ohm=2.0,
        shunt_susceptance_siemens=0.004,
    )

    assert line.series_impedance == complex(1.0, 2.0)
    assert line.total_shunt_admittance == complex(0.0, 0.004)
    assert line.half_shunt_admittance == complex(0.0, 0.002)
