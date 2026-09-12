# ============================================================
# GridForge V2 — Application Composition Root
# ============================================================
# Author: Subhendu Mishra
# ============================================================

"""Composition root for the headless GridForge Application layer."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.analysis.power_flow import PowerFlowAnalysis
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.short_circuit import ShortCircuitAnalysis
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
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
from .services.model_service import ModelService
from .services.validation_service import ValidationService
from .study import StudyRequest, StudyCancellationToken


def create_application(network: Any) -> Application:
    """Construct the fully configured headless Application facade."""
    if network is None:
        raise ValueError("network is required.")

    def build_runtime(active_network: Any) -> tuple[CommandManager, NetworkReadService, ValidationService]:
        context = ApplicationContext(network=active_network)
        model_service = ModelService(network=active_network)
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

    def new_network() -> Network:
        dynamic_models.replace(())
        return Network()

    # Keep the project-scoped association store outside Network topology. The
    # composition root owns persistence wiring; the solver receives detached
    # dynamic definitions and the electrical Network remains authoritative.
    application.dynamic_models = dynamic_models

    lifecycle = ProjectLifecycleService(
        network=network,
        network_factory=new_network,
        activate_network=activate_network,
        context=ProjectContext(project_id=str(uuid4()), name="Untitled Project", path=None),
        loader=load_project,
        saver=save_project,
    )
    application.attach_project_lifecycle(lifecycle)

    def study_configuration(request: StudyRequest, expected_type: type[Any]) -> Any:
        """Extract one immutable Core study configuration from the request."""
        configuration = request.configuration.get("configuration", request.configuration)
        if not isinstance(configuration, expected_type):
            raise TypeError(
                f"{request.study_type!r} requires {expected_type.__name__}; "
                f"received {type(configuration).__name__}."
            )
        return configuration

    def run_power_flow(request: StudyRequest, token: StudyCancellationToken) -> Any:
        if token.cancelled:
            return None
        configuration = study_configuration(request, PowerFlowStudyConfiguration)
        analysis = PowerFlowAnalysis.from_network(lifecycle.network, configuration)
        if token.cancelled:
            return None
        analysis.solve()
        if token.cancelled:
            return None
        return analysis.to_engineering_result()

    def run_short_circuit(request: StudyRequest, token: StudyCancellationToken) -> Any:
        if token.cancelled:
            return None
        configuration = study_configuration(request, ShortCircuitStudyConfiguration)
        analysis = ShortCircuitAnalysis.from_network(lifecycle.network, configuration)
        if token.cancelled:
            return None
        return analysis.run()

    application.study_service.register("power_flow", run_power_flow)
    application.study_service.register("short_circuit", run_short_circuit)
    return application


__all__ = ["create_application"]