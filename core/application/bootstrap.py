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
Constructs the headless Application runtime around the canonical
Core Network.

Composition
-----------

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
    Model Handlers       Command History
         |
         v
    ModelService
         |
         v
        Core

This module is composition infrastructure only.

It does NOT:

    * construct domain models;
    * mutate Network;
    * execute domain logic;
    * manipulate topology;
    * access Qt;
    * access UI state;
    * manage plugins.

Python Compatibility
--------------------
Python 3.10 / 3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .command_handlers import register_model_handlers
from .command_manager import CommandManager
from .context import ApplicationContext


# =====================================================================
# APPLICATION
# =====================================================================

@dataclass(frozen=True)
class Application:
    """
    Headless GridForge Application runtime.

    The Application owns the ApplicationContext and the
    CommandManager.

    Domain state remains owned by Core.
    """

    context: ApplicationContext
    command_manager: CommandManager

    # ================================================================
    # COMMAND EXECUTION
    # ================================================================

    def execute(self, command: Any):
        """
        Execute an Application command.

        CommandManager already owns the canonical ApplicationContext,
        therefore the command is the only argument required here.
        """

        return self.command_manager.execute(
            command,
        )

    # ================================================================
    # CAPABILITY DISCOVERY
    # ================================================================

    def registered_commands(self) -> tuple[str, ...]:
        """
        Return the currently registered Application command types.
        """

        return self.command_manager.registered_commands()


# =====================================================================
# FACTORY
# =====================================================================

def create_application(
    network: Any,
) -> Application:
    """
    Construct the canonical headless GridForge Application.

    Parameters
    ----------
    network:
        Already-created canonical Core Network.

    Returns
    -------
    Application
        Fully composed Application runtime.

    Composition order
    -----------------
    1. Construct ApplicationContext around the canonical Network.
    2. Construct CommandManager with that context.
    3. Register canonical model handlers.
    4. Return the composed Application.

    The Core Network is intentionally supplied by the caller.

    This prevents the Application layer from becoming responsible
    for Core/domain construction.
    """

    if network is None:
        raise ValueError(
            "network must not be None."
        )

    context = ApplicationContext(
        network=network,
    )

    command_manager = CommandManager(
        context,
    )

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
