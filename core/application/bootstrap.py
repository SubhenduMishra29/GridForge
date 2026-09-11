# ============================================================
# File: core/application/bootstrap.py
# GridForge V2 — Application Composition Root
# Author: Subhendu Mishra
# ============================================================

"""Composition root for the headless GridForge Application layer."""

from __future__ import annotations

from typing import Any

from .application import Application
from .command_handlers import build_model_command_handlers
from .command_manager import CommandManager
from .context import ApplicationContext
from .control_command_handlers import ControlCommandHandlers
from .read_service import NetworkReadService
from .services.control_service import ControlApplicationService
from .services.model_service import ModelService


def create_application(network: Any) -> Application:
    """Construct the fully configured headless Application facade."""
    if network is None:
        raise ValueError("network is required.")

    context = ApplicationContext(network=network)
    model_service = ModelService(network=network)
    control_service = ControlApplicationService()
    handlers = dict(build_model_command_handlers(model_service))
    handlers.update(ControlCommandHandlers(control_service).handlers())
    command_manager = CommandManager(
        context=context,
        handlers=handlers,
    )

    read_service = NetworkReadService(network)

    application = Application(
        command_manager=command_manager,
        read_service=read_service,
    )
    # Composition-root injection keeps the Control service behind the
    # Application boundary without introducing another command manager or
    # service locator. UI consumers use these public callables rather than
    # reaching into Core Control directly.
    application.control_service = control_service
    application.read_control = control_service.read
    return application


__all__ = ["create_application"]
