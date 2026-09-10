"""Application boundary for executing Control decisions.

Control produces intent. This module is the only bridge in this slice from
that intent to the existing Application command system.
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
from core.application.results import ApplicationResult
from core.control.decision import ControlActionType, ControlDecision


class ControlCommandTranslator:
    """Translate typed Control intent into existing Application commands."""

    @staticmethod
    def to_command(decision: ControlDecision):
        if not isinstance(decision, ControlDecision):
            raise TypeError("decision must be a ControlDecision.")
        if not decision.valid:
            raise ValueError(
                decision.diagnostic or "Control decision is not valid for execution."
            )

        target = decision.target_equipment_id
        action = decision.action_type
        if action is ControlActionType.TRIP:
            return TripBreakerCommand(breaker_id=target)
        if action is ControlActionType.OPEN:
            return OpenBreakerCommand(breaker_id=target)
        if action is ControlActionType.CLOSE:
            return CloseBreakerCommand(breaker_id=target)
        if action is ControlActionType.PUT_IN_SERVICE:
            return PutBreakerInServiceCommand(breaker_id=target)
        if action is ControlActionType.TAKE_OUT_OF_SERVICE:
            return TakeBreakerOutOfServiceCommand(breaker_id=target)
        raise ValueError(f"Unsupported Control action: {action.value}")


class ControlCommandDispatcher:
    """Execute Control intent using the existing Application command boundary.

    An optional command executor lets the Application facade remain the owner
    of semantic event publication while preserving CommandManager as the
    authoritative mutation/undo path.
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
