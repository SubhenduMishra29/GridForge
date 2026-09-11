# ============================================================
# File: tests/application/test_c9_application_read_contract.py
# GridForge V2 — C9 Application Read Contract Tests
# Author: Subhendu Mishra
# ============================================================

from types import MappingProxyType, SimpleNamespace

import pytest

from core.application.read_models import ElementReadModel
from core.application.read_service import NetworkReadService


class Terminal:
    def __init__(self, terminal_id, role, endpoint_id):
        self.id = terminal_id
        self.role = role
        self.endpoint = SimpleNamespace(id=endpoint_id) if endpoint_id else None


def model(**values):
    defaults = {"id": "E1", "name": "Element"}
    defaults.update(values)
    return SimpleNamespace(**defaults)


@pytest.mark.parametrize(
    ("element_type", "values", "required"),
    [
        ("buses", {"nominal_voltage_kv": 11.0, "voltage_pu": 1.01, "angle_deg": 2.0, "frequency_hz": 50.0, "in_service": True}, {"nominal_voltage_kv", "voltage_pu", "angle_deg", "frequency_hz", "in_service"}),
        ("lines", {"resistance_ohm": 0.1, "reactance_ohm": 0.2, "shunt_susceptance_siemens": 0.001, "rate_mva": 10.0, "in_service": True}, {"resistance_ohm", "reactance_ohm", "shunt_susceptance_siemens", "rate_mva", "in_service"}),
        ("cables", {"length_km": 1.2, "rated_voltage_kv": 11.0, "rated_current_a": 500.0, "r1_ohm_per_km": 0.1, "x1_ohm_per_km": 0.2, "b1_us_per_km": 1.0, "r0_ohm_per_km": 0.3, "x0_ohm_per_km": 0.4, "b0_us_per_km": 2.0, "thermal_limit_mva": 8.0, "conductor_count": 3, "in_service": True}, {"length_km", "rated_voltage_kv", "rated_current_a", "r1_ohm_per_km", "x1_ohm_per_km", "b1_us_per_km", "r0_ohm_per_km", "x0_ohm_per_km", "b0_us_per_km", "thermal_limit_mva", "conductor_count", "in_service"}),
        ("transformers", {"r": 0.01, "x": 0.08, "b": 0.001, "impedance_basis": "PU", "impedance_base_mva": 10.0, "impedance_base_voltage_kv": 11.0, "rate_mva": 10.0, "tap": 1, "tap_ratio": 1.0, "turns_ratio": 10.0, "shift": 0.0, "phase_shift_rad": 0.0, "phase_shift_deg": 0.0, "in_service": True}, {"r", "x", "b", "impedance_basis", "impedance_base_mva", "impedance_base_voltage_kv", "rate_mva", "tap", "tap_ratio", "turns_ratio", "shift", "phase_shift_rad", "phase_shift_deg", "in_service"}),
        ("switches", {"closed": True, "in_service": True, "normally_closed": True, "rated_voltage_kv": 11.0, "rated_current_a": 400.0}, {"closed", "in_service", "normally_closed", "rated_voltage_kv", "rated_current_a"}),
        ("breakers", {"closed": True, "failed": False, "in_service": True, "voltage_kv": 11.0, "current_a": 400.0, "interrupting_ka": 25.0}, {"closed", "failed", "in_service", "voltage_kv", "current_a", "interrupting_ka"}),
        ("disconnectors", {"closed": True, "in_service": True, "normally_closed": False, "voltage_kv": 11.0, "rated_current_a": 400.0, "operating_time": 2.0}, {"closed", "in_service", "normally_closed", "voltage_kv", "rated_current_a", "operating_time"}),
        ("fuses", {"in_service": True, "blown": False, "rated_current_a": 100.0, "rated_voltage_v": 415.0, "interrupting_rating_ka": 10.0}, {"in_service", "blown", "rated_current_a", "rated_voltage_v", "interrupting_rating_ka", "conducts"}),
        ("loads", {"p": 2.0, "q": 0.5, "in_service": True}, {"p", "q", "in_service"}),
        ("generators", {"p": 5.0, "q": 1.0, "V_setpoint": 1.02, "q_min": -2.0, "q_max": 2.0, "in_service": True}, {"p", "q", "V_setpoint", "q_min", "q_max", "in_service"}),
        ("synchronous_machines", {"active_power_injection_mw": 5.0, "reactive_power_injection_mvar": 1.0, "rated_power_mva": 6.0, "rated_voltage_kv": 11.0, "frequency_hz": 50.0, "in_service": True}, {"active_power_injection_mw", "reactive_power_injection_mvar", "rated_power_mva", "rated_voltage_kv", "frequency_hz", "in_service"}),
        ("motors", {"rated_mva": 2.0, "rated_kv": 11.0, "power_factor": 0.9, "p": 1.8, "q": 0.8, "efficiency": 0.95, "slip": 0.02, "starting_current_pu": 6.0, "running": True, "in_service": True}, {"rated_mva", "rated_kv", "power_factor", "p", "q", "efficiency", "slip", "starting_current_pu", "running", "in_service"}),
        ("shunts", {"g_pu": 0.01, "b_pu": 0.02, "in_service": True}, {"g_pu", "b_pu", "in_service"}),
        ("capacitors", {"reactive_power_injection_mvar": 2.0, "in_service": True}, {"reactive_power_injection_mvar", "in_service"}),
        ("reactors", {"reactive_power_injection_mvar": -2.0, "in_service": True}, {"reactive_power_injection_mvar", "in_service"}),
        ("solar", {"p_mw": 3.0, "q_mvar": 0.2, "p_min_mw": 0.0, "p_max_mw": 4.0, "q_min_mvar": -1.0, "q_max_mvar": 1.0, "in_service": True}, {"p_mw", "q_mvar", "p_min_mw", "p_max_mw", "q_min_mvar", "q_max_mvar", "in_service"}),
        ("batteries", {"p_mw": 1.0, "q_mvar": 0.1, "max_charge_mw": 2.0, "max_discharge_mw": 2.0, "energy_capacity_mwh": 8.0, "soc": 0.5, "soc_min": 0.1, "soc_max": 0.9, "in_service": True}, {"p_mw", "q_mvar", "max_charge_mw", "max_discharge_mw", "energy_capacity_mwh", "soc", "soc_min", "soc_max", "in_service"}),
        ("grids", {"nominal_voltage_kv": 132.0, "frequency_hz": 50.0, "voltage_pu": 1.0, "angle_deg": 0.0, "p_mw": 10.0, "q_mvar": 2.0, "short_circuit_mva": 1000.0, "x_over_r": 10.0, "z1_pu": 0.01, "z2_pu": 0.01, "z0_pu": 0.02, "in_service": True, "grounded": True}, {"nominal_voltage_kv", "frequency_hz", "voltage_pu", "angle_deg", "p_mw", "q_mvar", "short_circuit_mva", "x_over_r", "z1_pu", "z2_pu", "z0_pu", "in_service", "grounded"}),
        ("current_transformers", {"primary_rated_current_a": 400.0, "secondary_rated_current_a": 1.0, "ratio": 400.0, "burden_va": 15.0, "accuracy_class": "5P20", "frequency_hz": 50.0, "polarity": "P1-S1", "in_service": True}, {"primary_rated_current_a", "secondary_rated_current_a", "ratio", "burden_va", "accuracy_class", "frequency_hz", "polarity", "in_service"}),
        ("potential_transformers", {"primary_voltage_kv": 132.0, "secondary_voltage_v": 110.0, "voltage_ratio": 1200.0, "accuracy_class": "0.5", "burden_va": 50.0, "phase_displacement_deg": 0.1, "in_service": True}, {"primary_voltage_kv", "secondary_voltage_v", "voltage_ratio", "accuracy_class", "burden_va", "phase_displacement_deg", "in_service"}),
        ("capacitive_voltage_transformers", {"rated_primary_voltage_kv": 132.0, "rated_secondary_voltage_v": 110.0, "voltage_ratio": 1200.0, "accuracy_class": "0.5", "rated_burden_va": 50.0, "polarity": "H1-X1", "frequency_hz": 50.0, "in_service": True}, {"rated_primary_voltage_kv", "rated_secondary_voltage_v", "voltage_ratio", "accuracy_class", "rated_burden_va", "polarity", "frequency_hz", "in_service"}),
    ],
)
def test_explicit_projection_covers_required_canonical_fields(element_type, values, required):
    terminals = [Terminal("T1", "from", "B1"), Terminal("T2", "to", "B2")]
    read = NetworkReadService._to_read_model(element_type, model(terminals=terminals, **values))
    assert read.element_type == element_type
    assert read.object_id == "E1"
    assert read.labels["name"] == "Element"
    assert required <= set(read.attributes)
    for key in required - {"conducts"}:
        assert read.attributes[key] == values[key]
    assert read.connectivity_refs == ("T1", "T2")
    assert read.attributes["terminal_connectivity"] == (("from", "B1"), ("to", "B2"))


def test_fuse_conducts_is_derived_not_independent_state():
    read = NetworkReadService._to_read_model("fuses", model(in_service=True, blown=False))
    assert read.attributes["conducts"] is True


def test_read_model_is_immutable_and_does_not_leak_core_mapping():
    read = ElementReadModel("E1", "BUS", {"name": "B1"}, ("T1",), {"nested": {"value": 1}})
    assert isinstance(read.attributes, MappingProxyType)
    with pytest.raises(TypeError):
        read.attributes["x"] = 1
    nested = read.attributes["nested"]
    assert isinstance(nested, MappingProxyType)
    with pytest.raises(TypeError):
        nested["value"] = 2
