# ============================================================
# File: tests/application/test_c9_final_projection_regressions.py
# GridForge V2 — C9 Final Read Projection Regression Tests
# Author: Subhendu Mishra
# ============================================================

from types import SimpleNamespace

import pytest

from core.application.read_service import NetworkReadService


def model(**values):
    defaults = {"id": "E1", "name": "Element"}
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_cable_publishes_only_canonical_engineering_unit_keys():
    values = {
        "length_km": 1.2, "rated_voltage_kv": 11.0, "rated_current_a": 500.0,
        "r1_ohm_per_km": 0.1, "x1_ohm_per_km": 0.2, "b1_us_per_km": 1.0,
        "r0_ohm_per_km": 0.3, "x0_ohm_per_km": 0.4, "b0_us_per_km": 2.0,
        "thermal_limit_mva": 8.0, "conductor_count": 3, "in_service": True,
    }
    read = NetworkReadService._to_read_model("cables", model(**values))
    canonical = {"r1_ohm_per_km", "x1_ohm_per_km", "b1_us_per_km", "r0_ohm_per_km", "x0_ohm_per_km", "b0_us_per_km"}
    assert canonical <= set(read.attributes)
    assert not ({"r1", "x1", "b1", "r0", "x0", "b0"} & set(read.attributes))
    for key, value in values.items():
        assert read.attributes[key] == value


def test_missing_required_projection_value_is_not_silently_omitted():
    with pytest.raises(ValueError, match="required Application field.*rated_voltage_kv"):
        NetworkReadService._to_read_model("cables", model(
            length_km=1.2, rated_current_a=500.0, r1_ohm_per_km=0.1,
            x1_ohm_per_km=0.2, b1_us_per_km=1.0, r0_ohm_per_km=0.3,
            x0_ohm_per_km=0.4, b0_us_per_km=2.0, thermal_limit_mva=8.0,
            conductor_count=3, in_service=True,
        ))


@pytest.mark.parametrize("element_type,values", [
    ("buses", {"nominal_voltage_kv": 11.0, "voltage_pu": 1.01, "angle_deg": 2.0, "frequency_hz": 50.0, "in_service": True}),
    ("lines", {"resistance_ohm": 0.1, "reactance_ohm": 0.2, "shunt_susceptance_siemens": 0.001, "rate_mva": 10.0, "in_service": True}),
    ("cables", {"length_km": 1.2, "rated_voltage_kv": 11.0, "rated_current_a": 500.0, "r1_ohm_per_km": 0.1, "x1_ohm_per_km": 0.2, "b1_us_per_km": 1.0, "r0_ohm_per_km": 0.3, "x0_ohm_per_km": 0.4, "b0_us_per_km": 2.0, "thermal_limit_mva": 8.0, "conductor_count": 3, "in_service": True}),
    ("transformers", {"r": 0.01, "x": 0.08, "b": 0.001, "impedance_basis": "PU", "impedance_base_mva": 10.0, "impedance_base_voltage_kv": 11.0, "rate_mva": 10.0, "tap": 1, "tap_ratio": 1.0, "turns_ratio": 10.0, "shift": 0.0, "phase_shift_rad": 0.0, "phase_shift_deg": 0.0, "in_service": True}),
    ("switches", {"closed": True, "in_service": True, "normally_closed": True, "rated_voltage_kv": 11.0, "rated_current_a": 400.0}),
    ("breakers", {"closed": True, "failed": False, "in_service": True, "voltage_kv": 11.0, "current_a": 400.0, "interrupting_ka": 25.0}),
    ("disconnectors", {"closed": True, "in_service": True, "normally_closed": False, "voltage_kv": 11.0, "rated_current_a": 400.0, "operating_time": 2.0}),
    ("fuses", {"in_service": True, "blown": False, "rated_current_a": 100.0, "rated_voltage_v": 415.0, "interrupting_rating_ka": 10.0}),
    ("loads", {"p": 2.0, "q": 0.5, "in_service": True}),
    ("generators", {"p": 5.0, "q": 1.0, "V_setpoint": 1.02, "q_min": -2.0, "q_max": 2.0, "in_service": True}),
    ("synchronous_machines", {"active_power_injection_mw": 5.0, "reactive_power_injection_mvar": 1.0, "rated_power_mva": 6.0, "rated_voltage_kv": 11.0, "frequency_hz": 50.0, "in_service": True}),
    ("motors", {"rated_mva": 2.0, "rated_kv": 11.0, "power_factor": 0.9, "p": 1.8, "q": 0.8, "efficiency": 0.95, "slip": 0.02, "starting_current_pu": 6.0, "running": True, "in_service": True}),
    ("shunts", {"g_pu": 0.01, "b_pu": 0.02, "in_service": True}),
    ("capacitors", {"reactive_power_injection_mvar": 2.0, "in_service": True}),
    ("reactors", {"reactive_power_injection_mvar": -2.0, "in_service": True}),
    ("solar", {"p_mw": 3.0, "q_mvar": 0.2, "p_min_mw": 0.0, "p_max_mw": 4.0, "q_min_mvar": -1.0, "q_max_mvar": 1.0, "in_service": True}),
    ("batteries", {"p_mw": 1.0, "q_mvar": 0.1, "max_charge_mw": 2.0, "max_discharge_mw": 2.0, "energy_capacity_mwh": 8.0, "soc": 0.5, "soc_min": 0.1, "soc_max": 0.9, "in_service": True}),
    ("grids", {"nominal_voltage_kv": 132.0, "frequency_hz": 50.0, "voltage_pu": 1.0, "angle_deg": 0.0, "p_mw": 10.0, "q_mvar": 2.0, "short_circuit_mva": 1000.0, "x_over_r": 10.0, "z1_pu": 0.01, "z2_pu": 0.01, "z0_pu": 0.02, "in_service": True, "grounded": True}),
    ("current_transformers", {"primary_rated_current_a": 400.0, "secondary_rated_current_a": 1.0, "ratio": 400.0, "burden_va": 15.0, "accuracy_class": "5P20", "frequency_hz": 50.0, "polarity": "P1-S1", "in_service": True}),
    ("potential_transformers", {"primary_voltage_kv": 132.0, "secondary_voltage_v": 110.0, "voltage_ratio": 1200.0, "accuracy_class": "0.5", "burden_va": 50.0, "phase_displacement_deg": 0.1, "in_service": True}),
    ("capacitive_voltage_transformers", {"rated_primary_voltage_kv": 132.0, "rated_secondary_voltage_v": 110.0, "voltage_ratio": 1200.0, "accuracy_class": "0.5", "rated_burden_va": 50.0, "polarity": "H1-X1", "frequency_hz": 50.0, "in_service": True}),
])
def test_all_21_network_types_project_authoritative_values(element_type, values):
    read = NetworkReadService._to_read_model(element_type, model(**values))
    assert read.object_id == "E1"
    for key, expected in values.items():
        assert read.attributes[key] == expected
