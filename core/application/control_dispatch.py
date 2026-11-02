"""Application boundary for executing Control decisions.

Control produces intent. This module is the only bridge in this slice from
that intent to the existing Application command system.

Author: Subhendu Mishra
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

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


class InvalidApplicationResultError(TypeError):
    """The configured Application executor violated its result contract."""


class ControlTripBatchCommand(Command):
    """One atomic Application transaction for a coordinated breaker-trip set."""

    COMMAND_TYPE = "control.execute_trip_batch"

    def __init__(self, commands: tuple[Command, ...]) -> None:
        items = tuple(commands)
        if len(items) < 2:
            raise ValueError("A coordinated trip batch requires at least two breaker commands.")
        if any(not isinstance(item, Command) or item.command_type != "model.trip_breaker" for item in items):
            raise TypeError("A coordinated trip batch accepts only canonical TripBreakerCommand values.")
        breaker_ids = tuple(str(item.payload.get("breaker_id", "")).strip() for item in items)
        if any(not item for item in breaker_ids) or len(set(breaker_ids)) != len(breaker_ids):
            raise ValueError("A coordinated trip batch requires distinct, non-empty breaker IDs.")
        super().__init__(
            command_type=self.COMMAND_TYPE,
            payload={"commands": items, "breaker_ids": breaker_ids},
            command_id=uuid4(),
        )


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

    def execute_command(self, command: Command) -> ApplicationResult:
        """Execute this exact validated command through the configured Application boundary."""
        if not isinstance(command, Command):
            raise TypeError("command must be a Command.")
        result = self._command_executor(command)
        if not isinstance(result, ApplicationResult):
            raise InvalidApplicationResultError(
                "Application command executor must return ApplicationResult; "
                f"received {type(result).__name__}."
            )
        return result

    def execute(self, decision: ControlDecision) -> ApplicationResult:
        """Backward-compatible translation and execution of one Control decision."""
        return self.execute_command(ControlCommandTranslator.to_command(decision))

    def execute_trip_batch(self, decisions: tuple[ControlDecision, ...]) -> ApplicationResult:
        """Execute simultaneous breaker trips in one Application transaction."""
        items = tuple(decisions)
        if len(items) < 2:
            raise ValueError("execute_trip_batch requires at least two decisions.")
        commands = tuple(ControlCommandTranslator.to_command(item) for item in items)
        return self.execute_command(ControlTripBatchCommand(commands))


__all__ = ["ControlCommandTranslator", "ControlCommandDispatcher", "ControlTripBatchCommand", "InvalidApplicationResultError"]
