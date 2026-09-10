from __future__ import annotations

from core.control.action import ControlActionBinding
from core.control.context import ControlExecutionContext
from core.control.decision import ControlActionType
from core.control.engine import ControlEngine
from core.control.logic.coils import LogicCoil
from core.control.logic.engine import LogicEngine


def test_asserted_logic_output_produces_typed_trip_decision() -> None:
    logic = LogicEngine([LogicCoil("UV_TRIP")])
    engine = ControlEngine(logic)
    engine.bind_action(
        ControlActionBinding(
            control_id="UV-101",
            source_component="UV_TRIP",
            source_output="OUT",
            target_equipment_id="BRK-101",
            action_type=ControlActionType.TRIP,
            reason="Undervoltage condition active",
        )
    )

    result = engine.evaluate(
        context=ControlExecutionContext(
            simulation_time=5.0,
            external_inputs={"UV_TRIP": {"IN": True}},
        )
    )

    assert len(result.decisions) == 1
    decision = result.decisions[0]
    assert decision.action_type is ControlActionType.TRIP
    assert decision.target_equipment_id == "BRK-101"
    assert decision.simulation_time == 5.0


def test_trip_wins_deterministically_over_close_for_same_target() -> None:
    logic = LogicEngine([LogicCoil("CLOSE"), LogicCoil("TRIP")])
    engine = ControlEngine(logic)
    engine.bind_action(ControlActionBinding(
        control_id="CLOSE-101", source_component="CLOSE", source_output="OUT",
        target_equipment_id="BRK-101", action_type=ControlActionType.CLOSE,
        reason="Close request",
    ))
    engine.bind_action(ControlActionBinding(
        control_id="TRIP-101", source_component="TRIP", source_output="OUT",
        target_equipment_id="BRK-101", action_type=ControlActionType.TRIP,
        reason="Trip request",
    ))

    result = engine.evaluate(
        simulation_time=7.0,
        external_inputs={"CLOSE": {"IN": True}, "TRIP": {"IN": True}},
    )

    assert [item.action_type for item in result.decisions] == [ControlActionType.TRIP]
    assert len(result.blocked_actions) == 1
    assert result.blocked_actions[0].action_type is ControlActionType.CLOSE
    assert result.blocked_actions[0].valid is False
