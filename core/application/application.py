# ============================================================
# File: core/application/application.py
# GridForge V2 — Headless Application Facade
# ============================================================
"""
GridForge V2
============

Module:
    core.application.application

Purpose
-------
Defines the public headless Application façade for GridForge V2.

The Application façade is the stable entry point between external
consumers and the internal Application infrastructure.

External consumers may include:

    * UI;
    * plugins;
    * CLI;
    * automation;
    * batch workflows;
    * future remote/API integrations.

Architectural Boundary
-----------------------

    External Consumer
          |
          v
    Application
          |
          v
    CommandManager
          |
          v
    Application Service
          |
          v
         Core

The consumer does not need to know:

    * how commands are registered;
    * which service implements a use case;
    * how Core objects are constructed;
    * how Network mutation is performed.

Headless Requirement
--------------------
This module must remain completely independent of:

    * PySide6;
    * PyQt;
    * Qt;
    * QGraphicsScene;
    * QGraphicsItem;
    * UI controllers;
    * SLD;
    * canvas;
    * renderers.

Application Ownership
---------------------
The Application object owns the Application-level command
execution infrastructure.

It does NOT own the Core Network.

The Network is supplied by the Composition Root and remains
owned by the Core/application composition boundary.

Public API
----------
The Application façade exposes semantic operations.

For example:

    application.execute(command)

A future higher-level API may expose:

    application.create_bus(...)

but such convenience methods should only be added when they
represent stable Application use cases.

The command remains the canonical mutation path.

No direct Core mutation is exposed.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from typing import Any

from .command import Command
from .command_manager import CommandManager
from .context import ApplicationContext
from .results import ApplicationResult


class Application:
    """
    Public headless GridForge Application façade.

    Parameters
    ----------
    command_manager:
        Configured Application command manager.

    Notes
    -----
    The façade does not create the CommandManager itself.

    Construction belongs to ``create_application()`` in
    ``core.application.bootstrap``.
    """

    def __init__(
        self,
        command_manager: CommandManager,
    ) -> None:
        if command_manager is None:
            raise ValueError(
                "Application command_manager must not be None."
            )

        self._command_manager = command_manager

    @property
    def command_manager(self) -> CommandManager:
        """
        Return the underlying command manager.

        This property exists primarily for Application infrastructure
        and diagnostics.

        UI code should normally use ``execute()`` rather than
        manipulating the manager directly.
        """
        return self._command_manager

    @property
    def context(self) -> ApplicationContext:
        """
        Return the Application dependency context.
        """
        return self._command_manager.context

    def execute(
        self,
        command: Command,
    ) -> ApplicationResult:
        """
        Execute an Application command.

        Parameters
        ----------
        command:
            Immutable Application command representing caller intent.

        Returns
        -------
        ApplicationResult
            Result produced by the registered Application handler.

        Notes
        -----
        This is the canonical Application mutation entry point.

        External consumers should not directly call Core mutation
        methods when an Application command exists for the operation.
        """
        return self._command_manager.execute(command)

    def supports(
        self,
        command_type: str,
    ) -> bool:
        """
        Return whether the Application currently supports a command.

        This is useful for capability discovery by UI, plugins,
        automation, or other consumers.

        It does not execute the command.
        """
        return self._command_manager.is_registered(
            command_type,
        )

    def command_types(self) -> tuple[str, ...]:
        """
        Return the currently registered Application command types.
        """
        return self._command_manager.registered_commands()


__all__ = [
    "Application",
]
