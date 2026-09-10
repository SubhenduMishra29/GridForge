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
from core.control.decision import ControlActionType, ControlDecision


def _decision(action: ControlActionType) -> ControlDecision:
    return ControlDecision(
        control_id="CTRL-1",
        action_type=action,
        target_equipment_id="BRK-1",
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
