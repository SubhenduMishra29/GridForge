# ============================================================
# File: core/application/bootstrap.py
# GridForge V2 — Headless Application Bootstrap
# ============================================================
"""
GridForge V2
============

Module:
    core.application.bootstrap

Purpose
-------
Constructs the headless GridForge Application infrastructure
from already-created Core dependencies.

The bootstrap layer is the Composition Root for the Application
package.

It is responsible for:

    * accepting canonical Core dependencies;
    * creating ApplicationContext;
    * creating CommandManager;
    * registering built-in Application commands.

It does NOT:

    * construct UI objects;
    * initialize Qt;
    * create MainWindow;
    * create SLD/canvas objects;
    * create renderers;
    * own presentation state;
    * implement domain logic;
    * modify Core architecture.

Composition Root
----------------

    Existing Core
         |
         v
    ApplicationContext
         |
         +------------------+
         |                  |
         v                  v
    CommandManager      Application Services
         |
         v
    Built-in Commands

The Application layer is therefore independently usable without
the UI.

Headless Usage
--------------
A future CLI, test harness, automation system, plugin host, or UI
may construct the Application through this module.

The consumer does not need to know the internal registration
details of built-in commands.

Core Ownership
--------------
The Core Network is supplied to the bootstrap function.

The bootstrap function does not create or replace the Network.

This keeps Core ownership outside the Application layer.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from core.application.command_manager import CommandManager
from core.application.context import ApplicationContext
from core.application.commands import create_bus_handler


def create_application(
    network: object,
) -> CommandManager:
    """
    Construct the headless GridForge Application command manager.

    Parameters
    ----------
    network:
        Existing canonical Core Network instance.

    Returns
    -------
    CommandManager
        Fully configured headless Application command manager.

    Notes
    -----
    Core construction remains outside this function.

    The caller owns the lifecycle of the supplied Network.
    """

    context = ApplicationContext(
        network=network,
    )

    manager = CommandManager(
        context=context,
    )

    _register_builtin_commands(manager)

    return manager


def _register_builtin_commands(
    manager: CommandManager,
) -> None:
    """
    Register built-in GridForge Application commands.

    This function is intentionally private.

    External plugins must not modify the built-in command
    registration contract directly.

    Plugin command registration will be handled through the
    Plugin/Application integration boundary later.
    """

    manager.register(
        "bus.create",
        create_bus_handler,
    )


__all__ = [
    "create_application",
]
