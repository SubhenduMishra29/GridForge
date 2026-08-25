# ============================================================
# File: core/application/bootstrap.py
# GridForge V2 — Application Composition Root
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Bootstrap
=====================================

Composition root for the headless Application layer.

This module constructs and wires the Application-layer objects
against the authoritative Core Network.

Composition
-----------

    Core Network
        |
        v
    ApplicationContext
        |
        +----------------------+
        |                      |
        v                      v
    ModelService        CommandManager
        |                      |
        v                      v
    Model Handlers  <----------+
        |
        v
    Application

Responsibilities
----------------
- Accept the authoritative Core Network.
- Construct ApplicationContext.
- Construct ModelService against that Network.
- Build the canonical model-command handler registry.
- Construct CommandManager with that registry.
- Construct and return the Application facade.

This module does NOT:
- create or replace the Core Network;
- mutate Core state;
- resolve EndpointReference values;
- create Transactions;
- execute commands;
- manage undo/redo;
- contain UI/Qt/SLD logic.
"""

from __future__ import annotations

from typing import Any

from .application import Application
from .command_handlers import build_model_command_handlers
from .command_manager import CommandManager
from .context import ApplicationContext
from .services.model_service import ModelService


# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_application(
    network: Any,
) -> Application:
    """
    Construct the fully configured headless Application.

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
    The supplied Network remains the authoritative Core object.
    Bootstrap only composes the Application layer around it.
    """

    if network is None:
        raise ValueError(
            "network is required."
        )

    context = ApplicationContext(
        network=network,
    )

    model_service = ModelService(
        network=network,
    )

    handlers = build_model_command_handlers(
        model_service,
    )

    command_manager = CommandManager(
        context=context,
        handlers=handlers,
    )

    return Application(
        command_manager=command_manager,
    )


__all__ = [
    "create_application",
]
