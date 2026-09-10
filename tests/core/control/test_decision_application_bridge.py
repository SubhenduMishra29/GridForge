from __future__ import annotations

from core.application.commands.breaker_commands import TripBreakerCommand
from core.control.decision import ControlActionType, ControlDecision
from core.application.control_dispatch import ControlCommandTranslator


def test_trip_decision_translates_to_canonical_breaker_command() -> None:
    decision = ControlDecision.trip(
        control_id="UV-101",
        target_equipment_id="BRK-101",
        reason="Bus voltage below 0.80 pu",
        simulation_time=12.5,
    )

    command = ControlCommandTranslator.to_command(decision)

    assert isinstance(command, TripBreakerCommand)
    assert command.payload["breaker_id"] == "BRK-101"
    assert decision.action_type is ControlActionType.TRIP


def test_control_decision_contains_intent_only() -> None:
    decision = ControlDecision.trip(
        control_id="UV-101",
        target_equipment_id="BRK-101",
        reason="undervoltage",
        simulation_time=1.0,
    )

    assert decision.target_equipment_id == "BRK-101"
    assert not hasattr(decision, "equipment")
    assert not hasattr(decision, "network")


def test_invalid_target_action_is_rejected_before_command_translation() -> None:
    decision = ControlDecision(
        control_id="UV-101",
        action_type=ControlActionType.TRIP,
        target_equipment_id="",
        reason="invalid target",
        simulation_time=1.0,
    )

    try:
        ControlCommandTranslator.to_command(decision)
    except ValueError as exc:
        assert "target_equipment_id" in str(exc)
    else:
        raise AssertionError("invalid control target must be rejected")
