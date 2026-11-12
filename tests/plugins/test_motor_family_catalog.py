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


def test_only_existing_induction_family_claims_a_dynamic_solver() -> None:
    assert motor_family_profile(MotorFamily.THREE_PHASE_SQUIRREL_CAGE_INDUCTION).dynamic_model == "induction_dq"
    assert motor_family_profile(MotorFamily.PERMANENT_MAGNET_SYNCHRONOUS).dynamic_model is None



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
