"""Application boundary for executing Control decisions.

Control produces intent. This module is the only bridge in this slice from
that intent to the existing Application command system.
"""

from __future__ import annotations

from core.application.command_manager import CommandManager
from core.application.commands.breaker_commands import (
    CloseBreakerCommand,
    OpenBreakerCommand,
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
        raise ValueError(f"Unsupported Control action: {action.value}")


class ControlCommandDispatcher:
    """Execute Control intent using the existing CommandManager only."""

    def __init__(self, command_manager: CommandManager) -> None:
        if not isinstance(command_manager, CommandManager):
            raise TypeError("command_manager must be a CommandManager.")
        self._command_manager = command_manager

    @property
    def command_manager(self) -> CommandManager:
        return self._command_manager

    def execute(self, decision: ControlDecision) -> ApplicationResult:
        """Translate and execute one valid Control decision."""
        return self._command_manager.execute(
            ControlCommandTranslator.to_command(decision)
        )


__all__ = ["ControlCommandTranslator", "ControlCommandDispatcher"]
