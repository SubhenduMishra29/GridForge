"""Application boundary for executing Control decisions.

Control produces intent. This module is the only bridge in this slice from
that intent to the existing Application command system.

Author: Subhendu Mishra
"""

from __future__ import annotations

from collections.abc import Callable

from core.application.command import Command
from core.application.command_manager import CommandManager
from core.application.commands.breaker_commands import (
    CloseBreakerCommand,
    OpenBreakerCommand,
    PutBreakerInServiceCommand,
    TakeBreakerOutOfServiceCommand,
    TripBreakerCommand,
)
from core.application.commands.model_commands import (
    BlowFuseCommand,
    CloseDisconnectorCommand,
    CloseSwitchCommand,
    OpenDisconnectorCommand,
    OpenSwitchCommand,
    PutDisconnectorInServiceCommand,
    PutFuseInServiceCommand,
    PutSwitchInServiceCommand,
    ResetFuseCommand,
    TakeDisconnectorOutOfServiceCommand,
    TakeFuseOutOfServiceCommand,
    TakeSwitchOutOfServiceCommand,
)
from core.application.commands.motor_commands import (
    StartMotorCommand,
    StopMotorCommand,
    PutMotorInServiceCommand,
    TakeMotorOutOfServiceCommand,
)
from core.application.results import ApplicationResult
from core.control.decision import ControlActionType, ControlDecision, ControlTargetType


class ControlCommandTranslator:
    """Translate typed Control intent into existing Application commands."""

    @staticmethod
    def to_command(decision: ControlDecision) -> Command:
        if not isinstance(decision, ControlDecision):
            raise TypeError("decision must be a ControlDecision.")
        if not decision.valid:
            raise ValueError(
                decision.diagnostic or "Control decision is not valid for execution."
            )

        target = decision.target_equipment_id
        action = decision.action_type
        target_type = decision.target_equipment_type

        if target_type == ControlTargetType.BREAKER.value:
            commands = {
                ControlActionType.TRIP: TripBreakerCommand,
                ControlActionType.OPEN: OpenBreakerCommand,
                ControlActionType.CLOSE: CloseBreakerCommand,
                ControlActionType.PUT_IN_SERVICE: PutBreakerInServiceCommand,
                ControlActionType.TAKE_OUT_OF_SERVICE: TakeBreakerOutOfServiceCommand,
            }
            command_type = commands.get(action)
            if command_type is None:
                raise ValueError(f"Unsupported action {action.value!r} for breaker target.")
            return command_type(breaker_id=target)

        if target_type == ControlTargetType.SWITCH.value:
            commands = {
                ControlActionType.OPEN: OpenSwitchCommand,
                ControlActionType.CLOSE: CloseSwitchCommand,
                ControlActionType.PUT_IN_SERVICE: PutSwitchInServiceCommand,
                ControlActionType.TAKE_OUT_OF_SERVICE: TakeSwitchOutOfServiceCommand,
            }
            command_type = commands.get(action)
            if command_type is None:
                raise ValueError(f"Unsupported action {action.value!r} for switch target.")
            return command_type(switch_id=target)

        if target_type == ControlTargetType.DISCONNECTOR.value:
            commands = {
                ControlActionType.OPEN: OpenDisconnectorCommand,
                ControlActionType.CLOSE: CloseDisconnectorCommand,
                ControlActionType.PUT_IN_SERVICE: PutDisconnectorInServiceCommand,
                ControlActionType.TAKE_OUT_OF_SERVICE: TakeDisconnectorOutOfServiceCommand,
            }
            command_type = commands.get(action)
            if command_type is None:
                raise ValueError(f"Unsupported action {action.value!r} for disconnector target.")
            return command_type(disconnector_id=target)

        if target_type == ControlTargetType.FUSE.value:
            commands = {
                ControlActionType.TRIP: BlowFuseCommand,
                ControlActionType.BLOW: BlowFuseCommand,
                ControlActionType.RESET: ResetFuseCommand,
                ControlActionType.PUT_IN_SERVICE: PutFuseInServiceCommand,
                ControlActionType.TAKE_OUT_OF_SERVICE: TakeFuseOutOfServiceCommand,
            }
            command_type = commands.get(action)
            if command_type is None:
                raise ValueError(f"Unsupported action {action.value!r} for fuse target.")
            return command_type(fuse_id=target)

        if target_type == ControlTargetType.MOTOR.value:
            commands = {
                ControlActionType.START: StartMotorCommand,
                ControlActionType.STOP: StopMotorCommand,
                ControlActionType.PUT_IN_SERVICE: PutMotorInServiceCommand,
                ControlActionType.TAKE_OUT_OF_SERVICE: TakeMotorOutOfServiceCommand,
            }
            command_type = commands.get(action)
            if command_type is None:
                raise ValueError(f"Unsupported action {action.value!r} for motor target.")
            return command_type(motor_id=target)

        raise ValueError(
            f"No Application command contract is registered for Control target "
            f"type {target_type!r}."
        )


class ControlCommandDispatcher:
    """Execute Control intent using the Application command boundary.

    CommandManager remains the authoritative mutation/undo path; Control has
    no access to equipment instances or Core mutation APIs.
    """

    def __init__(
        self,
        command_manager: CommandManager,
        *,
        command_executor: Callable[[Command], ApplicationResult] | None = None,
    ) -> None:
        if not isinstance(command_manager, CommandManager):
            raise TypeError("command_manager must be a CommandManager.")
        self._command_manager = command_manager
        self._command_executor = command_executor or command_manager.execute

    @property
    def command_manager(self) -> CommandManager:
        return self._command_manager

    def execute(self, decision: ControlDecision) -> ApplicationResult:
        """Translate and execute one valid Control decision."""
        return self._command_executor(ControlCommandTranslator.to_command(decision))


__all__ = ["ControlCommandTranslator", "ControlCommandDispatcher"]
