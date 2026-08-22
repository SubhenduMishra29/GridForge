# ============================================================
# File: core/application/command_manager.py
# GridForge V2 — Headless Application Command Manager
# ============================================================
"""
GridForge V2
============

Module:
    core.application.command_manager

Purpose
-------
Provides headless Application command dispatch and command-history
ownership.

Architectural Position
----------------------

    UI / Plugin / Automation
              |
              v
       Application
              |
              v
       CommandManager
          /       \
         v         v
    CommandHistory Handler
                    |
                    v
             Application Service
                    |
                    v
                   Core

Responsibilities
----------------
CommandManager owns:

    * command registration;
    * command dispatch;
    * synchronous command execution;
    * successful-command history recording;
    * Application command capability discovery.

It does NOT own:

    * Core domain state;
    * Core Network internals;
    * UI state;
    * Qt;
    * SLD/canvas state;
    * rendering;
    * plugin lifecycle;
    * domain calculations.

History
-------
Only successfully executed commands are recorded.

A failed command is never placed into the undo history.

Undo/redo execution itself is intentionally not implemented yet.
CommandHistory establishes the ownership boundary; reversible
command semantics will be introduced separately.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .command import Command
from .context import ApplicationContext
from .errors import ApplicationError, ExecutionError
from .history import CommandHistory
from .results import ApplicationResult


CommandHandler = Callable[
    [Command, ApplicationContext],
    ApplicationResult,
]


@dataclass(frozen=True)
class CommandRegistration:
    """
    Immutable registration record for an Application command.
    """

    command_type: str
    handler: CommandHandler


class CommandManager:
    """
    Headless Application command dispatcher.

    CommandManager is the Application owner of command history.

    Core is never used as the command-history owner.
    """

    def __init__(
        self,
        context: ApplicationContext,
        history: CommandHistory | None = None,
    ) -> None:
        if context is None:
            raise ValueError(
                "CommandManager context must not be None."
            )

        self._context = context
        self._history = (
            history
            if history is not None
            else CommandHistory()
        )
        self._handlers: dict[str, CommandHandler] = {}

    # ========================================================
    # CONTEXT
    # ========================================================

    @property
    def context(self) -> ApplicationContext:
        """
        Return the immutable Application dependency context.
        """
        return self._context

    # ========================================================
    # HISTORY
    # ========================================================

    @property
    def history(self) -> CommandHistory:
        """
        Return the Application-owned command history.

        The history object contains only Application command
        records and has no direct Core mutation capability.
        """
        return self._history

    def can_undo(self) -> bool:
        """
        Return whether Application history contains an undo record.

        Actual undo execution is not yet implemented.
        """
        return self._history.can_undo()

    def can_redo(self) -> bool:
        """
        Return whether Application history contains a redo record.

        Actual redo execution is not yet implemented.
        """
        return self._history.can_redo()

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        command_type: str,
        handler: CommandHandler,
    ) -> None:
        """
        Register a handler for an Application command type.
        """

        if not isinstance(command_type, str):
            raise TypeError(
                "command_type must be a string."
            )

        if not command_type.strip():
            raise ValueError(
                "command_type must not be empty."
            )

        if not callable(handler):
            raise TypeError(
                "command handler must be callable."
            )

        if command_type in self._handlers:
            raise ValueError(
                f"Command already registered: {command_type}"
            )

        self._handlers[command_type] = handler

    def unregister(
        self,
        command_type: str,
    ) -> bool:
        """
        Remove a registered command handler.
        """
        return (
            self._handlers.pop(
                command_type,
                None,
            )
            is not None
        )

    def is_registered(
        self,
        command_type: str,
    ) -> bool:
        """
        Return whether a command type has a registered handler.
        """
        return command_type in self._handlers

    def registered_commands(self) -> tuple[str, ...]:
        """
        Return registered command types as an immutable tuple.
        """
        return tuple(self._handlers.keys())

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Command,
    ) -> ApplicationResult:
        """
        Execute a registered Application command.

        A command is added to history only after its handler
        completes successfully.

        Parameters
        ----------
        command:
            Immutable Application command.

        Returns
        -------
        ApplicationResult
            Result returned by the command handler.

        Raises
        ------
        ApplicationError
            Expected Application-level failure.

        ExecutionError
            Unexpected execution failure or invalid result.
        """

        if not isinstance(command, Command):
            raise TypeError(
                "CommandManager.execute requires a Command."
            )

        handler = self._handlers.get(
            command.command_type,
        )

        if handler is None:
            raise ExecutionError(
                code="COMMAND_NOT_REGISTERED",
                message=(
                    "No handler is registered for command "
                    f"'{command.command_type}'."
                ),
                details={
                    "command_type": command.command_type,
                    "command_id": str(command.command_id),
                },
            )

        try:
            result = handler(
                command,
                self._context,
            )

        except ApplicationError:
            # Expected Application failures remain unchanged.
            #
            # Crucially, failed commands are NOT recorded.
            raise

        except Exception as exc:
            raise ExecutionError(
                code="COMMAND_EXECUTION_FAILED",
                message=(
                    f"Command '{command.command_type}' "
                    "failed during execution."
                ),
                details={
                    "command_type": command.command_type,
                    "command_id": str(command.command_id),
                },
                cause=exc,
            ) from exc

        if not isinstance(
            result,
            ApplicationResult,
        ):
            raise ExecutionError(
                code="INVALID_COMMAND_RESULT",
                message=(
                    f"Command handler for "
                    f"'{command.command_type}' did not return "
                    "an ApplicationResult."
                ),
                details={
                    "command_type": command.command_type,
                },
            )

        # History is updated ONLY after successful execution.
        self._history.record(
            command,
            description=result.message,
        )

        return result


__all__ = [
    "CommandHandler",
    "CommandRegistration",
    "CommandManager",
]
