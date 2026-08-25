# ============================================================
# File: core/application/application.py
# GridForge V2 — Headless Application Facade
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Headless Application Facade
============================================

The Application facade is the stable public entry point between
external consumers and the internal Application infrastructure.

Architecture
------------

    External Consumer
          |
          v
      Application
          |
          v
    CommandManager
          |
          v
       Handler
          |
          v
    Application Service
          |
          v
         Core

The facade owns no Core state.

The facade does not expose:

    * CommandManager;
    * ApplicationContext;
    * Transaction;
    * CommandHistory;
    * handlers;
    * Application services;
    * Core internals.

The canonical mutation path is:

    Application.execute(command)

Headless Boundary
-----------------

This module is independent of:

    * PySide6;
    * PyQt;
    * Qt;
    * QGraphicsScene;
    * QGraphicsItem;
    * UI;
    * SLD;
    * canvas;
    * renderers;
    * plugin implementation details.

Composition
-----------

The Application object receives a fully configured
CommandManager from the Composition Root.

The Application does not construct:

    * Network;
    * ApplicationContext;
    * CommandManager;
    * services;
    * handlers.

Construction therefore remains outside the public facade.

Capability Discovery
--------------------

Consumers may query whether a command is supported without
executing it.

Command execution remains the only mutation entry point.
"""

from __future__ import annotations

from .command import Command
from .command_manager import CommandManager
from .results import ApplicationResult


class Application:
    """
    Public headless GridForge Application facade.

    Parameters
    ----------
    command_manager:
        Fully configured internal Application command manager.

    The command manager remains private.

    External consumers interact through the semantic facade
    methods exposed by this class.
    """

    def __init__(
        self,
        command_manager: CommandManager,
    ) -> None:
        if not isinstance(
            command_manager,
            CommandManager,
        ):
            raise TypeError(
                "Application command_manager must be "
                "a CommandManager."
            )

        self._command_manager = command_manager

    # ========================================================
    # EXECUTION
    # ========================================================

    def execute(
        self,
        command: Command,
    ) -> ApplicationResult:
        """
        Execute an Application command.

        This is the canonical mutation entry point.

        External consumers provide immutable Application commands.

        The internal CommandManager performs:

            * command dispatch;
            * transaction management;
            * undo registration;
            * history management;
            * rollback on failure.
        """

        if not isinstance(
            command,
            Command,
        ):
            raise TypeError(
                "Application.execute requires a Command."
            )

        return self._command_manager.execute(
            command,
        )

    # ========================================================
    # CAPABILITY DISCOVERY
    # ========================================================

    def supports(
        self,
        command_type: str,
    ) -> bool:
        """
        Return whether a command type is currently supported.

        This performs capability discovery only.

        It does not execute a command or mutate Core state.
        """

        if not isinstance(
            command_type,
            str,
        ):
            return False

        return self._command_manager.is_registered(
            command_type,
        )

    def command_types(
        self,
    ) -> tuple[str, ...]:
        """
        Return the currently registered command types.

        The returned tuple is immutable.

        This is a capability-discovery API and does not expose
        the CommandManager itself.
        """

        return self._command_manager.registered_commands


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "Application",
]
