# ============================================================
# File: core/application/bootstrap.py
# GridForge V2 — Application Composition Root
# Author: Subhendu Mishra
# ============================================================

"""Composition root for the headless GridForge Application layer."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.analysis.dynamic_model_association import DynamicMachineModelRegistry
from core.network import Network
from core.persistence import ProjectPersistenceService

from .application import Application
from .command_handlers import build_model_command_handlers
from .command_manager import CommandManager
from .context import ApplicationContext
from .project import ProjectContext
from .project_lifecycle import ProjectLifecycleService
from .read_service import NetworkReadService
from .services.validation_service import ValidationService


def create_application(network: Any) -> Application:
    """Construct the fully configured headless Application facade."""
    if network is None:
        raise ValueError("network is required.")

    def build_runtime(active_network: Any) -> tuple[CommandManager, NetworkReadService, ValidationService]:
        context = ApplicationContext(network=active_network)
        model_service = __import__(
            "core.application.services.model_service", fromlist=["ModelService"]
        ).ModelService(network=active_network)
        handlers = build_model_command_handlers(model_service)
        command_manager = CommandManager(context=context, handlers=handlers)
        return command_manager, NetworkReadService(active_network), ValidationService(active_network)

    command_manager, read_service, validation_service = build_runtime(network)
    application = Application(
        command_manager=command_manager,
        read_service=read_service,
        validation_service=validation_service,
    )

    def activate_network(active_network: Any) -> None:
        next_command_manager, next_read_service, next_validation_service = build_runtime(active_network)
        application._replace_runtime(next_command_manager, next_read_service, next_validation_service)

    persistence = ProjectPersistenceService()
    dynamic_models = DynamicMachineModelRegistry()

    def load_project(path):
        loaded = persistence.load(path)
        dynamic_models.replace(loaded.dynamic_models)
        return loaded

    def save_project(context, active_network, presentation, path):
        persistence.save(
            context,
            active_network,
            presentation,
            path,
            dynamic_models=dynamic_models.all(),
        )

    # Keep the project-scoped association store outside Network topology.  The
    # composition root owns the persistence wiring; Core Network remains purely
    # electrical truth and the solver receives detached dynamic definitions.
    application.dynamic_models = dynamic_models

    lifecycle = ProjectLifecycleService(
        network=network,
        network_factory=Network,
        activate_network=activate_network,
        context=ProjectContext(project_id=str(uuid4()), name="Untitled Project", path=None),
        loader=load_project,
        saver=save_project,
    )
    application.attach_project_lifecycle(lifecycle)
    return application


__all__ = ["create_application"]
