# ============================================================
# File: application/commands/command_dispatcher.py
# GridForge V2 — Application Command Dispatcher
# Author: Subhendu Mishra
# ============================================================
"""Application command routing boundary.

The dispatcher selects an application handler. Handlers own use-case
orchestration and Core mutation; this module contains no business logic.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .command import Command
from .command_result import CommandResult


CommandHandler = Callable[[Command], CommandResult | Any]


class CommandDispatcher:
    """Route commands to explicitly registered application handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, name: str, handler: CommandHandler) -> None:
        if not name:
            raise ValueError("name must not be empty")
        if name in self._handlers:
            raise ValueError(f"handler already registered for command: {name}")
        self._handlers[name] = handler

    def unregister(self, name: str) -> None:
        self._handlers.pop(name, None)

    def dispatch(self, command: Command) -> CommandResult:
        handler = self._handlers.get(command.name)
        if handler is None:
            return CommandResult.failure(
                f"no handler registered for command: {command.name}"
            )

        try:
            result = handler(command)
        except Exception as exc:  # handler boundary converts execution failure to result
            return CommandResult.failure(str(exc) or exc.__class__.__name__)

        if isinstance(result, CommandResult):
            return result
        return CommandResult.ok(result)


__all__ = ["CommandDispatcher", "CommandHandler"]
