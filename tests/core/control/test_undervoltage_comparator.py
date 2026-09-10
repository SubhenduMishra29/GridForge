from __future__ import annotations

import pytest

from core.control.logic.comparators import UndervoltageComparator
from core.control.measurement_input import ControlInput
from core.measurement.measurement_channel import MeasurementQuality


def test_undervoltage_comparator_asserts_below_pickup() -> None:
    comparator = UndervoltageComparator("UV-CMP-101", pickup=0.9)
    result = comparator.evaluate(comparator.initial_state(), {"VALUE": 0.85}, 12.0)
    assert result.outputs["TRIP"] is True
    assert result.time == 12.0


def test_undervoltage_comparator_does_not_assert_at_or_above_pickup() -> None:
    comparator = UndervoltageComparator("UV-CMP-101", pickup=0.9)
    at_pickup = comparator.evaluate(comparator.initial_state(), {"VALUE": 0.9}, 1.0)
    above_pickup = comparator.evaluate(comparator.initial_state(), {"VALUE": 0.95}, 2.0)
    assert at_pickup.outputs["TRIP"] is False
    assert above_pickup.outputs["TRIP"] is False


def test_undervoltage_comparator_accepts_canonical_control_input() -> None:
    comparator = UndervoltageComparator("UV-CMP-101", pickup=0.9)
    measurement = ControlInput(
        source_id="BUS-101-V",
        value=0.8,
        unit="pu",
        timestamp=10.0,
        quality=MeasurementQuality.GOOD,
        available=True,
    )
    result = comparator.evaluate_input(measurement, simulation_time=10.0)
    assert result.outputs["TRIP"] is True
    assert result.diagnostics["source_id"] == "BUS-101-V"


def test_undervoltage_comparator_rejects_unusable_control_input() -> None:
    comparator = UndervoltageComparator("UV-CMP-101", pickup=0.9)
    measurement = ControlInput(
        source_id="BUS-101-V",
        value=0.8,
        unit="pu",
        timestamp=10.0,
        quality=MeasurementQuality.BAD,
        available=True,
    )
    with pytest.raises(ValueError, match="not usable"):
        comparator.evaluate_input(measurement, simulation_time=10.0)
