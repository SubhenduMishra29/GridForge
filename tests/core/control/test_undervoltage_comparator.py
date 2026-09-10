from __future__ import annotations

import pytest

from core.control.action import ControlActionBinding
from core.control.context import ControlExecutionContext
from core.control.decision import ControlActionType
from core.control.engine import ControlEngine
from core.control.logic.comparators import UndervoltageComparator
from core.control.logic.engine import LogicEngine
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


def test_undervoltage_comparator_drives_bound_trip_decision() -> None:
    logic = LogicEngine([UndervoltageComparator("UV-CMP-101", pickup=0.9)])
    engine = ControlEngine(logic)
    engine.bind_action(
        ControlActionBinding(
            control_id="UV-101",
            source_component="UV-CMP-101",
            source_output="TRIP",
            target_equipment_id="BRK-101",
            action_type=ControlActionType.TRIP,
            reason="Undervoltage pickup",
        )
    )

    result = engine.evaluate(
        context=ControlExecutionContext(
            simulation_time=25.0,
            external_inputs={"UV-CMP-101": {"VALUE": 0.82}},
        )
    )

    assert len(result.decisions) == 1
    assert result.decisions[0].action_type is ControlActionType.TRIP
    assert result.decisions[0].target_equipment_id == "BRK-101"
    assert result.decisions[0].simulation_time == 25.0
