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
Provides the headless Application composition boundary.

This module wires the already-constructed Core Network into an
ApplicationContext and registers Application command handlers
with a generic CommandManager.

Architecture
------------

    Core Network
          |
          v
    ApplicationContext
          |
          v
    CommandManager
          |
          +--------------------+
          |                    |
          v                    v
    bus.create            bus.delete
          |                    |
          v                    v
    CreateBusHandler     DeleteBusHandler
          |                    |
          +---------+----------+
                    |
                    v
             Application Service
                    |
                    v
                   Core

Responsibilities
----------------
This module owns only Application composition.

It:

    * accepts an already-created Core Network;
    * constructs ApplicationContext;
    * constructs CommandManager;
    * registers Application command handlers;
    * returns the configured CommandManager.

It does NOT:

    * construct the Core Network;
    * execute commands;
    * mutate Core objects;
    * contain domain logic;
    * contain UI logic;
    * depend on Qt;
    * know about SLD/canvas objects;
    * manage plugins;
    * perform engineering calculations.

Headless Requirement
--------------------
This module is completely independent of:

    * PySide6;
    * PyQt5;
    * PyQt6;
    * Qt;
    * QGraphicsScene;
    * renderers;
    * UI controllers.

Command Registration
--------------------
Current command registrations:

    "bus.create" -> create_bus_handler
    "bus.delete" -> delete_bus_handler

CommandManager remains generic and does not know about individual
commands.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from typing import Any

from .command_manager import CommandManager
from .commands.create_bus import create_bus_handler
from .commands.delete_bus import delete_bus_handler
from .context import ApplicationContext


def create_application_context(
    network: Any,
) -> ApplicationContext:
    """
    Construct the immutable ApplicationContext.

    Parameters
    ----------
    network:
        Already-constructed canonical Core Network.

    Returns
    -------
    ApplicationContext
        Headless Application dependency context.

    Notes
    -----
    The Core Network is constructed outside this module.

    This function therefore does not become a hidden Core factory.
    """

    return ApplicationContext(
        network=network,
    )


def create_command_manager(
    context: ApplicationContext,
) -> CommandManager:
    """
    Construct and configure the Application CommandManager.

    Parameters
    ----------
    context:
        Immutable headless ApplicationContext.

    Returns
    -------
    CommandManager
        Configured command dispatcher.

    Notes
    -----
    CommandManager remains generic.

    Command-specific knowledge is introduced here, at the
    Application composition boundary.
    """

    if not isinstance(
        context,
        ApplicationContext,
    ):
        raise TypeError(
            "create_command_manager requires "
            "an ApplicationContext."
        )

    manager = CommandManager(
        context,
    )

    # -------------------------------------------------------------
    # BUS COMMANDS
    # -------------------------------------------------------------

    manager.register(
        "bus.create",
        create_bus_handler,
    )

    manager.register(
        "bus.delete",
        delete_bus_handler,
    )

    return manager


def create_application(
    network: Any,
) -> tuple[ApplicationContext, CommandManager]:
    """
    Construct the complete headless Application boundary.

    Parameters
    ----------
    network:
        Already-constructed canonical Core Network.

    Returns
    -------
    tuple
        ``(ApplicationContext, CommandManager)``

    Architecture
    ------------
        network
            ↓
        ApplicationContext
            ↓
        CommandManager
            ↓
        registered handlers
    """

    context = create_application_context(
        network,
    )

    manager = create_command_manager(
        context,
    )

    return (
        context,
        manager,
    )


__all__ = [
    "create_application_context",
    "create_command_manager",
    "create_application",
]
