from __future__ import annotations
import pytest
from plugins.motor_dynamics.catalog import MOTOR_FAMILY_PROFILES, MotorFamily, MotorNameplate, motor_family_profile
from plugins.motor_dynamics.instrumentation import motor_measurement_points


def test_every_motor_family_has_a_profile_and_measurement_template() -> None:
    assert set(MOTOR_FAMILY_PROFILES) == set(MotorFamily)
    for family in MotorFamily:
        points = motor_measurement_points(family)
        assert points
        ids = [point.point_id for point in points]
        assert len(ids) == len(set(ids))
        assert any(point.required for point in points)


@pytest.mark.parametrize("family", [
    MotorFamily.THREE_PHASE_SQUIRREL_CAGE_INDUCTION,
    MotorFamily.PERMANENT_MAGNET_SYNCHRONOUS,
    MotorFamily.BRUSHLESS_DC,
    MotorFamily.AC_SERVO,
    MotorFamily.TRACTION_PERMANENT_MAGNET,
])
def test_ac_family_requires_frequency(family: MotorFamily) -> None:
    with pytest.raises(ValueError, match="frequency_hz is required"):
        MotorNameplate(family, 15.0, 400.0, 28.0, 1470.0)


def test_dc_nameplate_does_not_require_frequency() -> None:
    item = MotorNameplate(MotorFamily.DC_SHUNT, 5.5, 220.0, 28.0, 1450.0)
    assert item.frequency_hz is None


def test_dynamic_solver_availability_is_explicit_by_family() -> None:
    assert motor_family_profile(MotorFamily.THREE_PHASE_SQUIRREL_CAGE_INDUCTION).dynamic_model == "induction_dq"
    assert motor_family_profile(MotorFamily.PERMANENT_MAGNET_SYNCHRONOUS).dynamic_model == "pmsm_dq"
    assert motor_family_profile(MotorFamily.TRACTION_PERMANENT_MAGNET).dynamic_model == "pmsm_dq"
    assert motor_family_profile(MotorFamily.BRUSHLESS_DC).dynamic_model == "bldc_trapezoidal"



@pytest.mark.parametrize("family", [
    MotorFamily.STEPPER_VARIABLE_RELUCTANCE,
    MotorFamily.STEPPER_PERMANENT_MAGNET,
    MotorFamily.STEPPER_HYBRID,
])
def test_stepper_instrumentation_uses_two_winding_phases(family: MotorFamily) -> None:
    point_ids = {point.point_id for point in motor_measurement_points(family)}
    assert "terminal.phase_a_current" in point_ids
    assert "terminal.phase_b_current" in point_ids
    assert "terminal.ic" not in point_ids
    assert "drive.dc_link_voltage" in point_ids



from plugins.motor_dynamics.transient_solver import (
    PMSMParameters,
    solve_pmsm_transient_cpu,
)


def _pmsm_parameters(**overrides):
    values = dict(
        stator_resistance_ohm=0.5,
        d_axis_inductance_h=0.004,
        q_axis_inductance_h=0.006,
        permanent_magnet_flux_wb=0.08,
        pole_pairs=4,
        inertia_kg_m2=0.02,
        thermal_capacity_j_k=5000.0,
        thermal_conductance_w_k=20.0,
    )
    values.update(overrides)
    return PMSMParameters(**values)


def test_pmsm_solver_returns_finite_immutable_channels_and_positive_torque() -> None:
    result = solve_pmsm_transient_cpu(
        "pmsm-01",
        _pmsm_parameters(),
        0.05,
        0.0001,
        stator_voltage_d_v=0.0,
        stator_voltage_q_v=12.0,
        load_torque_nm=0.1,
    )
    channels = result.channels(_pmsm_parameters())
    assert result.backend == "cpu-rk4"
    assert result.sample_count == 501
    assert all(__import__("numpy").isfinite(values).all() for values in channels.values())
    assert channels["stator_current_q_a"][-1] > 0.0
    assert channels["electromagnetic_torque_nm"][-1] > 0.0
    assert channels["rotor_speed_rad_s"][-1] > 0.0
    assert not result.state_data.flags.writeable
    assert not channels["electromagnetic_torque_nm"].flags.writeable


def test_pmsm_zero_voltage_zero_initial_state_remains_at_rest() -> None:
    result = solve_pmsm_transient_cpu(
        "pmsm-rest",
        _pmsm_parameters(),
        0.02,
        0.001,
        stator_voltage_d_v=0.0,
        stator_voltage_q_v=0.0,
    )
    assert result.state("rotor_speed_rad_s")[-1] == pytest.approx(0.0)
    assert result.state("stator_current_d_a")[-1] == pytest.approx(0.0)
    assert result.state("stator_current_q_a")[-1] == pytest.approx(0.0)


def test_pmsm_supports_sample_aligned_voltage_and_load_disturbances() -> None:
    import numpy as np
    count = 101
    voltage_q = np.full(count, 8.0)
    load = np.zeros(count)
    load[50:] = 0.2
    result = solve_pmsm_transient_cpu(
        "pmsm-disturbance",
        _pmsm_parameters(),
        0.01,
        0.0001,
        stator_voltage_d_v=np.zeros(count),
        stator_voltage_q_v=voltage_q,
        load_torque_nm=load,
    )
    assert result.load_torque_nm[49] == 0.0
    assert result.load_torque_nm[50] == 0.2
    assert result.diagnostics["load_torque_profile"] == "zero_order_hold"


@pytest.mark.parametrize("kwargs, message", [
    ({"stator_resistance_ohm": 0.0}, "stator_resistance_ohm must be finite and positive"),
    ({"d_axis_inductance_h": -0.1}, "d_axis_inductance_h must be finite and positive"),
    ({"permanent_magnet_flux_wb": float("nan")}, "permanent_magnet_flux_wb must be finite and positive"),
    ({"pole_pairs": 0}, "pole_pairs must be a positive integer"),
])
def test_pmsm_parameter_validation(kwargs, message) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _pmsm_parameters(**kwargs)


def test_pmsm_rejects_misaligned_input_profiles() -> None:
    with pytest.raises(ValueError, match="exactly 11 samples"):
        solve_pmsm_transient_cpu(
            "pmsm-bad-profile",
            _pmsm_parameters(),
            0.01,
            0.001,
            stator_voltage_d_v=[0.0] * 10,
            stator_voltage_q_v=8.0,
        )
