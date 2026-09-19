# ============================================================
# GridForge V2 — Application Composition Root
# ============================================================
# Author: Subhendu Mishra

"""Composition root for the headless GridForge Application layer."""

from __future__ import annotations

from typing import Any
from dataclasses import replace
from uuid import uuid4

from core.analysis.power_flow import PowerFlowAnalysis
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.power_flow_preparation import PreparedPowerFlow
from core.analysis.short_circuit import ShortCircuitAnalysis
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.analysis.dynamic_model_association import DynamicMachineModelRegistry
from core.analysis.transient_event_state import TransientEventState
from core.analysis.transient_events import (
    schedule_breaker_close,
    schedule_breaker_open,
    schedule_equipment_state,
    schedule_fault_apply,
    schedule_fault_clear,
)
from core.analysis.transient_fault import TransientFault
from core.analysis.transient_network import TransientNetworkSolver
from core.analysis.transient_runtime import TransientNetworkRuntime
from core.analysis.transient_stability import TransientStabilityAnalysis, TransientStabilityStudyConfiguration
from core.network import Network
from core.persistence import ProjectPersistenceService
from core.protection.project_configuration import ProtectionProjectConfiguration
from core.protection.runtime import ProtectionRuntime
from core.solver.dynamics import DAESolver, EventManager, Integrator, MultiMachineSystem, TransientStabilitySolver
from core.solver.power_flow.result import PowerFlowResult
from core.solver.short_circuit.fault_types import FaultType

from .application import Application
from .control_command_handlers import ControlCommandHandlers
from .command_handlers import build_model_command_handlers
from .command_manager import CommandManager
from .context import ApplicationContext
from .project import ProjectContext
from .project_lifecycle import ProjectLifecycleService
from .protection_configuration_handlers import ProtectionConfigurationHandlers
from .read_service import NetworkReadService, ProtectionReadService
from .relay_command_handlers import RelayCommandHandlers
from .services.control_service import ControlApplicationService
from .services.model_service import ModelService
from .services.protection_configuration_service import ProtectionConfigurationService
from .services.relay_model_service import RelayModelService
from .services.validation_service import ValidationService
from .study import StudyRequest, StudyCancellationToken
from .study_preparation import StudyPreparationService


def create_application(network: Any) -> Application:
    """Construct the fully configured headless GridForge Application facade."""
    if network is None:
        raise ValueError("network is required.")

    initial_context = ProjectContext(project_id=str(uuid4()), name="Untitled Project", path=None)
    # The protection service may resolve the active Network for its own
    # Application-scoped configuration checks. Study execution never uses this
    # provider; studies capture an explicit detached ProjectSnapshot.
    lifecycle = None
    protection_configuration_service = ProtectionConfigurationService(
        ProtectionProjectConfiguration(initial_context.project_id),
        network_provider=lambda: lifecycle.network if lifecycle is not None else network,
    )

    def register_handlers(target: dict[str, Any], source: Any, family: str) -> None:
        """Merge one handler family into the single Application registry.

        Duplicate command ownership is a composition error, not a last-write-wins
        condition.  The composition root therefore rejects duplicate handlers
        before constructing the CommandManager.
        """
        for command_type, handler in dict(source).items():
            if command_type in target:
                raise RuntimeError(
                    f"Duplicate Application handler registration for {command_type!r} "
                    f"while composing {family}."
                )
            target[command_type] = handler

    def build_runtime(active_network: Any) -> tuple[CommandManager, NetworkReadService, ValidationService]:
        context = ApplicationContext(network=active_network)
        model_service = ModelService(network=active_network)
        handlers: dict[str, Any] = {}
        register_handlers(handlers, build_model_command_handlers(model_service), "model")
        register_handlers(
            handlers,
            RelayCommandHandlers(
                RelayModelService(
                    active_network,
                    protection_configuration_provider=lambda: protection_configuration_service.configuration,
                )
            ).handlers(),
            "protection relay",
        )
        register_handlers(
            handlers,
            ProtectionConfigurationHandlers(protection_configuration_service).handlers(),
            "protection configuration",
        )
        # Control editing commands are composed into the same authoritative
        # Application command registry as model and protection commands.
        control_service = ControlApplicationService()
        register_handlers(handlers, ControlCommandHandlers(control_service).handlers(), "control")
        command_manager = CommandManager(context=context, handlers=handlers)
        return command_manager, NetworkReadService(active_network), ValidationService(active_network)

    command_manager, read_service, validation_service = build_runtime(network)
    application = Application(
        command_manager=command_manager,
        read_service=read_service,
        validation_service=validation_service,
    )

    application.protection_configuration_service = protection_configuration_service
    application.protection_runtime = ProtectionRuntime(network, protection_configuration_service.configuration)
    application._protection_read_service = ProtectionReadService(network)

    persistence = ProjectPersistenceService()
    dynamic_models = DynamicMachineModelRegistry()

    def activate_project_transaction(
        context: ProjectContext | None,
        loaded,
        candidate_network: Any,
        presentation: Any | None,
        generation: int,
    ):
        """Stage and atomically commit every project-bound Application dependency."""
        next_command_manager, next_read_service, next_validation_service = build_runtime(candidate_network)
        next_protection_read_service = ProtectionReadService(candidate_network)
        if context is None:
            next_configuration = None
            next_dynamic_models = ()
            next_protection_runtime = None
        else:
            next_configuration = (
                loaded.protection_configuration
                if loaded is not None and loaded.protection_configuration is not None
                else ProtectionProjectConfiguration(context.project_id)
            )
            if next_configuration.project_id != context.project_id:
                raise ValueError(
                    f"Protection configuration project_id {next_configuration.project_id!r} does not match "
                    f"active project {context.project_id!r}."
                )
            next_dynamic_models = tuple(
                replace(item, activation_generation=generation)
                for item in (loaded.dynamic_models if loaded is not None else ())
            )
            next_protection_runtime = ProtectionRuntime(candidate_network, next_configuration)

        previous_runtime = (
            application._command_manager,
            application._read_service,
            application._validation_service,
            application._control_execution,
            application._protection_read_service,
            application.protection_runtime,
        )
        previous_configuration = protection_configuration_service.configuration
        previous_dynamic_models = dynamic_models.snapshot()
        previous_revision = application.revision_service.snapshot_state()
        previous_presentation = application.presentation

        try:
            application._replace_runtime(
                next_command_manager,
                next_read_service,
                next_validation_service,
            )
            application._protection_read_service = next_protection_read_service
            if next_configuration is None:
                protection_configuration_service.deactivate()
            else:
                protection_configuration_service.activate(next_configuration)
            dynamic_models.replace(next_dynamic_models)
            application.protection_runtime = next_protection_runtime
            if application._sld_service is not None:
                if presentation is None:
                    application._sld_service.detach_document()
                else:
                    application._sld_service.bind_document(presentation)
            application.revision_service.reset_for_project()
        except Exception:
            (
                application._command_manager,
                application._read_service,
                application._validation_service,
                application._control_execution,
                application._protection_read_service,
                application.protection_runtime,
            ) = previous_runtime
            if previous_configuration is None:
                protection_configuration_service.deactivate()
            else:
                protection_configuration_service.activate(previous_configuration)
            dynamic_models.replace(previous_dynamic_models)
            application.revision_service.restore_state(previous_revision)
            if application._sld_service is not None:
                if previous_presentation is None:
                    application._sld_service.detach_document()
                else:
                    application._sld_service.bind_document(previous_presentation)
            raise

        def rollback() -> None:
            (
                application._command_manager,
                application._read_service,
                application._validation_service,
                application._control_execution,
                application._protection_read_service,
                application.protection_runtime,
            ) = previous_runtime
            if previous_configuration is None:
                protection_configuration_service.deactivate()
            else:
                protection_configuration_service.activate(previous_configuration)
            dynamic_models.replace(previous_dynamic_models)
            application.revision_service.restore_state(previous_revision)
            if application._sld_service is not None:
                if previous_presentation is None:
                    application._sld_service.detach_document()
                else:
                    application._sld_service.bind_document(previous_presentation)

        return rollback

    def validate_project_candidate(context: ProjectContext, loaded, candidate_network, presentation) -> None:
        del candidate_network, presentation
        if loaded is not None:
            for association in loaded.dynamic_models:
                if association.project_id != context.project_id:
                    raise ValueError(
                        f"Dynamic model association {association.machine_id!r} belongs to "
                        f"project {association.project_id!r}, not {context.project_id!r}."
                    )
            if loaded.protection_configuration is not None and loaded.protection_configuration.project_id != context.project_id:
                raise ValueError("Protection configuration project_id does not match the candidate project.")

    def load_project(path):
        # Loading is side-effect free. Candidate dynamic/protection state is
        # installed only by the successful activation transaction.
        return persistence.load(path)

    def save_project(context, active_network, presentation, path):
        persistence.save(
            context,
            active_network,
            presentation,
            path,
            dynamic_models=dynamic_models.all(),
            protection_configuration=protection_configuration_service.configuration,
        )

    def new_network() -> Network:
        return Network()

    application.dynamic_models = dynamic_models

    lifecycle = ProjectLifecycleService(
        network=network,
        network_factory=new_network,
        context=initial_context,
        loader=load_project,
        saver=save_project,
        activation_transaction=activate_project_transaction,
        project_state_validator=validate_project_candidate,
    )
    application.attach_project_lifecycle(lifecycle)

    def study_configuration(request: StudyRequest, expected_type: type[Any]) -> Any:
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
        snapshot = application.capture_project_snapshot()
        if snapshot.project_id != request.project_id or snapshot.activation_generation != request.activation_generation:
            raise RuntimeError("Study snapshot no longer matches the requested project generation.")
        prepared = StudyPreparationService(snapshot).prepare_power_flow(configuration)
        if token.cancelled:
            return None
        analysis = PowerFlowAnalysis.from_prepared(prepared)
        analysis.solve()
        if token.cancelled:
            return None
        return analysis.to_engineering_result()

    def run_short_circuit(request: StudyRequest, token: StudyCancellationToken) -> Any:
        if token.cancelled:
            return None
        configuration = study_configuration(request, ShortCircuitStudyConfiguration)
        snapshot = application.capture_project_snapshot()
        if snapshot.project_id != request.project_id or snapshot.activation_generation != request.activation_generation:
            raise RuntimeError("Study snapshot no longer matches the requested project generation.")
        prepared = StudyPreparationService(snapshot).prepare_short_circuit(configuration)
        if token.cancelled:
            return None
        analysis = ShortCircuitAnalysis.from_prepared(prepared)
        return analysis.run()

    def configure_transient_events(request: StudyRequest, event_manager: EventManager, event_state: TransientEventState) -> None:
        for event in request.configuration.get("events", ()):
            kind = str(event["type"]).strip().lower()
            time = float(event["time"])
            event_id = str(event["event_id"])
            if kind == "breaker_open":
                schedule_breaker_open(event_manager, event_state, time, str(event["breaker_id"]), event_id, event.get("affected_equipment_ids", ()))
            elif kind == "breaker_close":
                schedule_breaker_close(event_manager, event_state, time, str(event["breaker_id"]), event_id, event.get("affected_equipment_ids", ()))
            elif kind == "equipment_state":
                schedule_equipment_state(event_manager, event_state, time, str(event["equipment_id"]), bool(event["conducting"]), event_id)
            elif kind == "fault_apply":
                fault = TransientFault(
                    fault_type=FaultType.from_value(event["fault_type"]),
                    bus_id=str(event["bus_id"]),
                    impedance=complex(event.get("impedance", 0.0j)),
                )
                schedule_fault_apply(event_manager, event_state, time, fault, event_id)
            elif kind == "fault_clear":
                schedule_fault_clear(event_manager, event_state, time, event_id)
            else:
                raise ValueError(f"Unsupported transient event type: {kind!r}.")

    def run_transient_stability(request: StudyRequest, token: StudyCancellationToken) -> Any:
        if token.cancelled:
            return None
        configuration = study_configuration(request, TransientStabilityStudyConfiguration)
        prepared_power_flow = request.configuration.get("prepared_power_flow")
        power_flow_result = request.configuration.get("power_flow_result")
        if not isinstance(prepared_power_flow, PreparedPowerFlow) or not isinstance(power_flow_result, PowerFlowResult):
            raise TypeError("transient_stability requires prepared_power_flow and power_flow_result in the study request.")
        snapshot = application.capture_project_snapshot()
        if snapshot.project_id != request.project_id or snapshot.activation_generation != request.activation_generation:
            raise RuntimeError("Study snapshot no longer matches the requested project generation.")
        prepared = StudyPreparationService(snapshot).prepare_transient_stability(
            configuration, prepared_power_flow, power_flow_result,
            DynamicMachineModelRegistry(snapshot.dynamic_models),
        )
        if token.cancelled:
            return None
        machine_system = MultiMachineSystem(prepared.machines)
        event_state = TransientEventState.from_snapshot(prepared.network)
        network_runtime = TransientNetworkRuntime(event_state, machine_system)
        event_manager = EventManager()
        configure_transient_events(request, event_manager, event_state)
        dae_solver = DAESolver(machine_system, network_runtime.solve, prepared.mechanical_powers, integrator=Integrator("RK4"))
        solver = TransientStabilitySolver(dae_solver, start_time=configuration.start_time, end_time=configuration.end_time, dt=configuration.dt, event_manager=event_manager)
        analysis = TransientStabilityAnalysis(solver, configuration, prepared.initial_state)
        result = analysis.run()
        if token.cancelled:
            return None
        return result

    application.study_service.register("power_flow", run_power_flow)
    application.study_service.register("short_circuit", run_short_circuit)
    application.study_service.register("transient_stability", run_transient_stability)
    return application


__all__ = ["create_application"]
