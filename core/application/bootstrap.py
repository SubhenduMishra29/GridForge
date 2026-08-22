# ============================================================
# File: core/application/bootstrap.py
# GridForge V2 — Headless Application Composition Root
# ============================================================
"""
GridForge V2
============

Module:
    core.application.bootstrap

Purpose
-------
Constructs the headless Application runtime from an already-created
canonical Core Network.

Architectural responsibility
----------------------------

    Core Network
          |
          v
    ApplicationContext
          |
          v
    CommandManager
          |
          v
    Model Command Handlers

This module is the Application composition boundary.

It does NOT:

    * construct domain models;
    * contain business logic;
    * execute commands;
    * mutate Network;
    * manipulate topology;
    * access Qt;
    * access UI state;
    * manage plugins.

The Core Network remains the authoritative domain state.

The ApplicationContext remains an immutable dependency container.

The CommandManager remains responsible for command dispatch,
execution history, and command-handler invocation.

Python Compatibility
--------------------
Python 3.10 / 3.11.
"""

from __future__ import annotations

from dataclasses import dataclass

from .command_handlers import register_model_handlers
from .command_manager import CommandManager
from .context import ApplicationContext


# =====================================================================
# APPLICATION RUNTIME
# =====================================================================

@dataclass(frozen=True)
class Application:
    """
    Headless GridForge Application runtime.

    Attributes
    ----------
    context:
        Immutable Application dependency context.

    command_manager:
        Canonical Application command dispatcher.

    Notes
    -----
    Application is intentionally a thin composition object.

    It does not contain domain logic.

    Domain behavior remains in Core and Application services.
    """

    context: ApplicationContext
    command_manager: CommandManager

    def execute(self, command):
        """
        Execute an Application command.

        Parameters
        ----------
        command:
            Immutable Application Command.

        Returns
        -------
        ApplicationResult
            Result returned by the registered command handler.

        Notes
        -----
        The Application façade supplies the canonical context to
        CommandManager. CommandManager remains responsible for
        dispatch and history.
        """

        return self.command_manager.execute(
            command,
            self.context,
        )


# =====================================================================
# FACTORY
# =====================================================================

def create_application(
    network,
) -> Application:
    """
    Construct the canonical headless GridForge Application.

    Parameters
    ----------
    network:
        Already-constructed canonical Core Network.

    Returns
    -------
    Application
        Fully composed Application runtime.

    Composition order
    -----------------
        1. Validate supplied Network.
        2. Construct ApplicationContext.
        3. Construct CommandManager.
        4. Register Application command handlers.
        5. Return immutable Application runtime.

    The function deliberately does not construct the Core Network.

    Core construction belongs to the higher-level Composition Root.
    """

    if network is None:
        raise ValueError(
            "network must not be None."
        )

    context = ApplicationContext(
        network=network,
    )

    command_manager = CommandManager()

    register_model_handlers(
        command_manager,
    )

    return Application(
        context=context,
        command_manager=command_manager,
    )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "Application",
    "create_application",
]
