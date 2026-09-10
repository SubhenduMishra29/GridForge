# ============================================================
# File: tests/core/model/test_cable_engineering_contract.py
# GridForge V2 — Cable Engineering Contract Tests
# Author: Subhendu Mishra
# ============================================================

from core.model.cable import Cable


def test_cable_application_contract_accepts_engineering_quantities() -> None:
    cable = Cable(
        id="C1",
        length_km=2.0,
        rated_voltage_kv=33.0,
        rated_current_a=400.0,
        r1_ohm_per_km=0.10,
        x1_ohm_per_km=0.20,
        b1_us_per_km=5.0,
        r0_ohm_per_km=0.30,
        x0_ohm_per_km=0.60,
        b0_us_per_km=2.0,
    )

    assert cable.r1_ohm_per_km == 0.10
    assert cable.x1_ohm_per_km == 0.20
    assert cable.b1_us_per_km == 5.0
    assert cable.length_km == 2.0


def test_cable_engineering_values_are_not_double_converted() -> None:
    cable = Cable(
        id="C2",
        length_km=3.0,
        r1_ohm_per_km=0.10,
        x1_ohm_per_km=0.20,
        b1_us_per_km=4.0,
        r0_ohm_per_km=0.30,
        x0_ohm_per_km=0.60,
        b0_us_per_km=2.0,
    )

    assert cable.resistance_ohm == 0.30
    assert cable.reactance_ohm == 0.60
    assert cable.shunt_susceptance_siemens == 12.0e-6
    assert cable.zero_sequence_resistance_ohm == 0.90
    assert cable.zero_sequence_reactance_ohm == 1.80
    assert cable.zero_sequence_shunt_susceptance_siemens == 6.0e-6

    # Cable must not expose its engineering quantities as Branch PU values.
    assert cable.r == 0.0
    assert cable.x == 0.0
    assert cable.b == 0.0
