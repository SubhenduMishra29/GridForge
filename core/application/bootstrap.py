# ============================================================
# File: core/application/bootstrap.py
# GridForge V2 — Headless Application Composition Root
# Author: Subhendu Mishra
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

Architectural Responsibility
----------------------------
This module is the Composition Root for the headless Application.

It is responsible only for wiring already-defined components.

It does NOT:

    * construct domain models;
    * construct the Core Network;
    * mutate Network;
    * execute domain logic;
    * manipulate topology;
    * access Qt;
    * access UI state;
    * manage plugins;
    * define the Application façade.

The canonical Application façade is defined in
``core.application.application``.

Python Compatibility
--------------------
Python 3.10 / 3.11.
"""

from __future__ import annotations

from typing import Any

from .application import Application
from .command_handlers import register_model_handlers
from .command_manager import CommandManager
from .context import ApplicationContext


# =====================================================================
# APPLICATION FACTORY
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

        The Application layer does not construct the Network.
        Ownership of the Network remains outside the Composition Root.

    Returns
    -------
    Application
        Fully composed headless Application runtime.

    Composition order
    -----------------
    1. Construct ApplicationContext around the canonical Network.
    2. Construct CommandManager with that context.
    3. Register canonical model handlers.
    4. Return the canonical Application façade.

    Notes
    -----
    The returned object is the single Application façade defined by
    ``core.application.application``.

    No duplicate Application implementation exists in this module.
    """

    if network is None:
        raise ValueError(
            "network must not be None."
        )

    # ---------------------------------------------------------------
    # 1. Application Context
    # ---------------------------------------------------------------

    context = ApplicationContext(
        network=network,
    )

    # ---------------------------------------------------------------
    # 2. Command Manager
    # ---------------------------------------------------------------

    command_manager = CommandManager(
        context,
    )

    # ---------------------------------------------------------------
    # 3. Register canonical model handlers
    # ---------------------------------------------------------------

    register_model_handlers(
        command_manager,
    )

    # ---------------------------------------------------------------
    # 4. Construct the canonical Application façade
    # ---------------------------------------------------------------

    return Application(
        context=context,
        command_manager=command_manager,
    )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "create_application",
]
