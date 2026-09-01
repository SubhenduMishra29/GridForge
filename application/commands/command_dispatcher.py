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
CommandCompletion = Callable[[Command, CommandResult], None]


class CommandDispatcher:
    """Route commands to explicitly registered application handlers."""

    def __init__(self, *, on_complete: CommandCompletion | None = None) -> None:
        self._handlers: dict[str, CommandHandler] = {}
        self._on_complete = on_complete

    @property
    def on_complete(self) -> CommandCompletion | None:
        return self._on_complete

    def set_completion_handler(self, callback: CommandCompletion | None) -> None:
        """Set the optional application-level completion notification."""
        self._on_complete = callback

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
            result = CommandResult.failure(
                f"no handler registered for command: {command.name}"
            )
            self._notify_completion(command, result)
            return result

        try:
            raw_result = handler(command)
        except Exception as exc:  # application boundary converts failure to result
            result = CommandResult.failure(str(exc) or exc.__class__.__name__)
        else:
            result = raw_result if isinstance(raw_result, CommandResult) else CommandResult.ok(raw_result)

        self._notify_completion(command, result)
        return result

    def _notify_completion(self, command: Command, result: CommandResult) -> None:
        if self._on_complete is not None:
            self._on_complete(command, result)


__all__ = ["CommandDispatcher", "CommandHandler", "CommandCompletion"]
