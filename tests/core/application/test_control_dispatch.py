from core.application.command import Command
from core.application.command_manager import CommandManager
from core.application.control_dispatch import ControlCommandTranslator
from core.application.commands.breaker_commands import (
    CloseBreakerCommand,
    OpenBreakerCommand,
    PutBreakerInServiceCommand,
    TakeBreakerOutOfServiceCommand,
    TripBreakerCommand,
)
from core.control.action import ControlActionBinding
from core.control.decision import ControlActionType, ControlDecision
import pytest


def _decision(action: ControlActionType, *, target_type: str = "breaker") -> ControlDecision:
    return ControlDecision(
        control_id="CTRL-1",
        action_type=action,
        target_equipment_id="BRK-1",
        target_equipment_type=target_type,
        reason="test action",
        simulation_time=1.0,
    )


def test_translator_covers_all_declared_breaker_control_actions() -> None:
    expected = {
        ControlActionType.TRIP: TripBreakerCommand,
        ControlActionType.OPEN: OpenBreakerCommand,
        ControlActionType.CLOSE: CloseBreakerCommand,
        ControlActionType.PUT_IN_SERVICE: PutBreakerInServiceCommand,
        ControlActionType.TAKE_OUT_OF_SERVICE: TakeBreakerOutOfServiceCommand,
    }

    for action, command_type in expected.items():
        command = ControlCommandTranslator.to_command(_decision(action))
        assert isinstance(command, command_type)
        assert command.payload["breaker_id"] == "BRK-1"


def test_dispatcher_uses_application_command_executor_for_translated_control_intent() -> None:
    manager = CommandManager(context=object())
    calls: list[Command] = []

    def executor(command: Command):
        calls.append(command)
        return None

    from core.application.control_dispatch import ControlCommandDispatcher

    dispatcher = ControlCommandDispatcher(manager, command_executor=executor)
    dispatcher.execute(_decision(ControlActionType.PUT_IN_SERVICE))

    assert len(calls) == 1
    assert isinstance(calls[0], PutBreakerInServiceCommand)


def test_control_decision_rejects_non_breaker_target_type() -> None:
    with pytest.raises(ValueError, match="target_equipment_type"):
        _decision(ControlActionType.OPEN, target_type="line")


def test_action_binding_declares_breaker_target_contract() -> None:
    binding = ControlActionBinding(
        control_id="CTRL-1",
        source_component="UV-1",
        source_output="trip",
        target_equipment_id="BRK-1",
        target_equipment_type="breaker",
        action_type=ControlActionType.TRIP,
        reason="undervoltage",
    )
    assert binding.target_equipment_type == "breaker"
    assert binding.decision(simulation_time=1.0).target_equipment_type == "breaker"


def test_translator_rejects_non_breaker_control_target() -> None:
    decision = object.__new__(ControlDecision)
    object.__setattr__(decision, "control_id", "CTRL-1")
    object.__setattr__(decision, "action_type", ControlActionType.OPEN)
    object.__setattr__(decision, "target_equipment_id", "LINE-1")
    object.__setattr__(decision, "target_equipment_type", "line")
    object.__setattr__(decision, "reason", "invalid target")
    object.__setattr__(decision, "simulation_time", 1.0)
    object.__setattr__(decision, "triggered_by", None)
    object.__setattr__(decision, "valid", True)
    object.__setattr__(decision, "diagnostic", None)

    with pytest.raises(ValueError, match="breaker"):
        ControlCommandTranslator.to_command(decision)
