# ============================================================
# File: core/application/bootstrap.py
# GridForge V2 — Application Composition Root
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Bootstrap
=====================================

Composition root for the headless Application layer.

Responsibilities
----------------

This module is responsible only for constructing and wiring the
Application-layer components.

Composition:

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
        |
        v
    Application facade

This module does NOT:

    * implement domain logic;
    * mutate the Core directly;
    * resolve endpoint references;
    * execute commands;
    * create Transactions;
    * perform undo/redo;
    * contain UI or Qt code;
    * contain SLD logic.

The Core Network is supplied by the caller and remains the
authoritative domain object.
"""

from __future__ import annotations

from typing import Any

from .application import Application
from .command_handlers import register_model_handlers
from .command_manager import CommandManager
from .context import ApplicationContext


# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_application(
    network: Any,
) -> Application:
    """
    Construct the fully wired headless Application.

    Parameters
    ----------
    network:
        The authoritative Core Network instance.

    Returns
    -------
    Application
        Fully configured Application facade.

    Notes
    -----
    Bootstrap owns composition only.

    The supplied Network is not replaced, copied, or recreated.
    """

    if network is None:
        raise ValueError(
            "network is required."
        )

    context = ApplicationContext(
        network=network,
    )

    command_manager = CommandManager(
        context=context,
    )

    register_model_handlers(
        command_manager,
        context,
    )

    return Application(
        command_manager=command_manager,
    )


__all__ = [
    "create_application",
]
