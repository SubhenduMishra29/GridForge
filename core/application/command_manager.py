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
Provides the headless command-dispatch infrastructure for the
GridForge V2 Application layer.

The CommandManager is responsible for translating an incoming
Application Command into an Application operation.

Architectural flow
------------------

    UI / Plugin / Automation
              |
              v
           Command
              |
              v
       CommandManager
              |
              v
       Command Handler
              |
              v
       Application Service
              |
              v
             Core

The CommandManager is infrastructure.

It is NOT:

    * a UI controller;
    * a Qt action manager;
    * a graphics interaction manager;
    * a domain service;
    * a Core model owner;
    * a plugin manager;
    * a renderer manager.

Headless Requirement
--------------------
This module must have zero dependency on:

    * PySide6;
    * PyQt5;
    * PyQt6;
    * Qt;
    * QGraphicsScene;
    * QGraphicsItem;
    * UI controllers;
    * SLD/canvas classes.

Command Registration
--------------------
Each command type is associated with a handler.

Conceptually:

    "element.create" -> handler

The handler is an Application-layer callable.

The CommandManager does not know what the handler does internally.

It simply:

    1. receives a Command;
    2. identifies its command type;
    3. resolves the registered handler;
    4. invokes the handler;
    5. returns the ApplicationResult.

Dependency Injection
--------------------
Handlers are registered explicitly.

The manager does not instantiate services automatically.

This keeps construction in the Composition Root.

Example:

    manager.register(
        "element.create",
        create_element_handler,
    )

Then:

    result = manager.execute(command)

Command Immutability
--------------------
The manager must never modify a Command.

The command is treated as immutable input.

Error Boundary
--------------
Expected ApplicationError exceptions are allowed to cross the
manager boundary unchanged.

Unexpected exceptions are wrapped as ExecutionError so that
Application consumers receive a structured Application-level
failure without exposing arbitrary implementation exceptions.

The original exception is retained as ``cause``.

History
-------
The manager establishes the command-history boundary but does
not yet implement undo/redo semantics.

This is deliberate.

Undo/redo requires explicit definition of:

    * reversible commands;
    * inverse operations;
    * Core transaction semantics;
    * failure handling;
    * history invalidation.

Those rules must not be invented prematurely.

Therefore this implementation maintains no undo stack yet.

Threading
---------
The CommandManager is deliberately synchronous.

Asynchronous execution is not introduced at this boundary until
the Application architecture explicitly requires it.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from .command import Command
from .context import ApplicationContext
from .errors import ApplicationError, ExecutionError
from .results import ApplicationResult


CommandHandler = Callable[
    [Command, ApplicationContext],
    ApplicationResult,
]


@dataclass(frozen=True)
class CommandRegistration:
    """
    Immutable registration record for one Application command.

    Parameters
    ----------
    command_type:
        Stable semantic command identifier.

    handler:
        Callable responsible for executing the command.
    """

    command_type: str
    handler: CommandHandler


class CommandManager:
    """
    Headless Application command dispatcher.

    The manager owns command-handler registration and synchronous
    command execution.

    It deliberately does not own:

        * Core objects;
        * ApplicationContext construction;
        * services;
        * UI state;
        * undo/redo history.
    """

    def __init__(
        self,
        context: ApplicationContext,
    ) -> None:
        if context is None:
            raise ValueError(
                "CommandManager context must not be None."
            )

        self._context = context
        self._handlers: Dict[str, CommandHandler] = {}

    @property
    def context(self) -> ApplicationContext:
        """
        Return the immutable Application dependency context.
        """
        return self._context

    def register(
        self,
        command_type: str,
        handler: CommandHandler,
    ) -> None:
        """
        Register a handler for an Application command type.

        Parameters
        ----------
        command_type:
            Stable semantic command identifier.

        handler:
            Application-level callable that executes the command.

        Raises
        ------
        ValueError
            If command_type is invalid or already registered.

        TypeError
            If handler is not callable.
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

        Returns
        -------
        bool
            True when a handler was removed, otherwise False.
        """
        return self._handlers.pop(command_type, None) is not None

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
        Return registered command types.

        A tuple is returned so callers cannot mutate the internal
        registration collection.
        """
        return tuple(self._handlers.keys())

    def execute(
        self,
        command: Command,
    ) -> ApplicationResult:
        """
        Execute a registered Application command synchronously.

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
            Expected Application failure.

        ExecutionError
            Unexpected handler failure.

        KeyError
            Not used. Missing handlers are converted into a
            structured ExecutionError.
        """
        if not isinstance(command, Command):
            raise TypeError(
                "CommandManager.execute requires a Command."
            )

        handler = self._handlers.get(command.command_type)

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
            # Expected Application failures already conform to the
            # Application boundary and must cross unchanged.
            raise

        except Exception as exc:
            # Unexpected implementation failures are converted to
            # a structured Application-level execution failure.
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

        if not isinstance(result, ApplicationResult):
            raise ExecutionError(
                code="INVALID_COMMAND_RESULT",
                message=(
                    f"Command handler for '{command.command_type}' "
                    "did not return an ApplicationResult."
                ),
                details={
                    "command_type": command.command_type,
                },
            )

        return result


__all__ = [
    "CommandHandler",
    "CommandRegistration",
    "CommandManager",
]
