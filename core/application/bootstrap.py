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
from core.control.configuration import ControlConfiguration
from core.protection.runtime import ProtectionRuntime
from core.solver.dynamics import DAESolver, EventManager, Integrator, MultiMachineSystem, TransientStabilitySolver
from core.solver.power_flow.result import PowerFlowResult
from core.solver.short_circuit.fault_types import FaultType

from .application import Application
from .control_command_handlers import ControlCommandHandlers
from .command_handlers import build_model_command_handlers
from .services.electrical_connection_service import ElectricalConnectionCommandHandlers
from .services.simple_wire_service import SimpleWireConnectionCommandHandlers
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
from .services.measurement_channel_service import MeasurementChannelService
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
    control_service = ControlApplicationService(ControlConfiguration.empty(initial_context.project_id))
    measurement_channel_service = MeasurementChannelService()
    measurement_channel_service.activate(initial_context, network, (), generation=1)
    protection_configuration_service = ProtectionConfigurationService(
        ProtectionProjectConfiguration(initial_context.project_id),
        network_provider=lambda: lifecycle.network if lifecycle is not None else network,
        measurement_channel_provider=lambda: measurement_channel_service.channels,
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
        register_handlers(handlers, ElectricalConnectionCommandHandlers().handlers(), "electrical connection")
        register_handlers(handlers, SimpleWireConnectionCommandHandlers().handlers(), "simple wire connectivity")
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
        register_handlers(handlers, ControlCommandHandlers(control_service).handlers(), "control")
        command_manager = CommandManager(context=context, handlers=handlers)
        return command_manager, NetworkReadService(active_network), ValidationService(active_network)

    command_manager, read_service, validation_service = build_runtime(network)
    application = Application(
        command_manager=command_manager,
        read_service=read_service,
        validation_service=validation_service,
        measurement_channel_service=measurement_channel_service,
        control_service=control_service,
    )

    application.protection_configuration_service = protection_configuration_service
    application.protection_runtime = ProtectionRuntime(network, protection_configuration_service.configuration)
    application._protection_read_service = ProtectionReadService(network)

    def activate_network(active_network: Any):
        """Replace project-bound Application runtime and return its rollback."""
        previous_command_manager = application._command_manager
        previous_read_service = application._read_service
        previous_validation_service = application._validation_service
        previous_protection_read_service = application._protection_read_service
        previous_control_execution = application._control_execution

        try:
            next_command_manager, next_read_service, next_validation_service = build_runtime(active_network)
            application._replace_runtime(next_command_manager, next_read_service, next_validation_service)
            application._protection_read_service = ProtectionReadService(active_network)
        except Exception:
            application._command_manager = previous_command_manager
            application._read_service = previous_read_service
            application._validation_service = previous_validation_service
            application._protection_read_service = previous_protection_read_service
            application._control_execution = previous_control_execution
            raise

        def rollback() -> None:
            application._command_manager = previous_command_manager
            application._read_service = previous_read_service
            application._validation_service = previous_validation_service
            application._protection_read_service = previous_protection_read_service
            application._control_execution = previous_control_execution

        return rollback

    persistence = ProjectPersistenceService()
    dynamic_models = DynamicMachineModelRegistry()

    def activate_project_state(context: ProjectContext | None, loaded, network: Network, generation: int):
        """Install project-scoped protection/dynamic runtime state transactionally."""
        previous_configuration = protection_configuration_service.configuration
        previous_protection_runtime = application.protection_runtime
        previous_measurement = measurement_channel_service.serialize_definitions()
        previous_measurement_project = measurement_channel_service.project_id
        previous_measurement_generation = measurement_channel_service.activation_generation
        previous_dynamic_models = dynamic_models.snapshot()
        previous_control_configuration = control_service.configuration

        try:
            if context is None:
                measurement_channel_service.activate(None, network, (), 0)
                protection_configuration_service.deactivate()
                application.protection_runtime = None
                dynamic_models.replace(())
            else:
                definitions = loaded.measurement_definitions if loaded is not None else ()
                measurement_channel_service.activate(context, network, definitions, generation)
                configuration = (
                    loaded.protection_configuration
                    if loaded is not None and loaded.protection_configuration is not None
                    else ProtectionProjectConfiguration(context.project_id)
                )
                if configuration.project_id != context.project_id:
                    raise ValueError(
                        f"Protection configuration project_id {configuration.project_id!r} does not match "
                        f"active project {context.project_id!r}."
                    )
                protection_configuration_service.activate(configuration)
                for item in configuration.elements:
                    protection_configuration_service.validate_configuration(item)
                for item in configuration.elements:
                    relay = network.get_by_id("relay", item.relay_id)
                    for input_name, channel_id in item.input_channel_ids.items():
                        relay.bind_input(input_name, measurement_channel_service.require(channel_id))
                control_configuration = loaded.control_configuration if loaded is not None and loaded.control_configuration is not None else ControlConfiguration.empty(context.project_id)
                if control_configuration.project_id != context.project_id: raise ValueError("Control configuration project_id does not match the active project.")
                control_configuration.validate(); control_service.activate(control_configuration)
                if loaded is None:
                    dynamic_models.replace(())
                else:
                    dynamic_models.replace(
                        tuple(
                            replace(item, activation_generation=generation)
                            for item in loaded.dynamic_models
                        )
                    )
                application.protection_runtime = ProtectionRuntime(network=network, configuration=configuration)
                application.protection_runtime.compose(measurement_channel_service.channels)

        except Exception:
            if previous_measurement_project is None:
                measurement_channel_service.deactivate()
            else:
                measurement_channel_service.activate(
                    ProjectContext(previous_measurement_project, "restored", None),
                    application.project_lifecycle.network,
                    previous_measurement,
                    previous_measurement_generation,
                )
            if previous_configuration is None:
                protection_configuration_service.deactivate()
            else:
                protection_configuration_service.activate(previous_configuration)
            application.protection_runtime = previous_protection_runtime
            dynamic_models.replace(previous_dynamic_models)
            control_service.activate(previous_control_configuration)
            raise

        def rollback() -> None:
            if previous_measurement_project is None:
                measurement_channel_service.deactivate()
            else:
                measurement_channel_service.activate(
                    ProjectContext(previous_measurement_project, "restored", None),
                    application.project_lifecycle.network,
                    previous_measurement,
                    previous_measurement_generation,
                )
            if previous_configuration is None:
                protection_configuration_service.deactivate()
            else:
                protection_configuration_service.activate(previous_configuration)
            application.protection_runtime = previous_protection_runtime
            dynamic_models.replace(previous_dynamic_models)
            control_service.activate(previous_control_configuration)

        return rollback

    def validate_project_candidate(context: ProjectContext, loaded, candidate_network, presentation) -> None:
        """Validate candidate identity/provenance without mutating active state."""
        if candidate_network is None:
            raise ValueError("Candidate Network is required.")
        if presentation is None:
            raise ValueError("Candidate presentation is required.")
        if loaded is not None:
            if loaded.context.project_id != context.project_id:
                raise ValueError("Loaded ProjectContext does not match the candidate project.")
            for association in loaded.dynamic_models:
                if association.project_id != context.project_id:
                    raise ValueError(
                        f"Dynamic model association {association.machine_id!r} belongs to "
                        f"project {association.project_id!r}, not {context.project_id!r}."
                    )
                if association.activation_generation < 1:
                    raise ValueError(
                        f"Dynamic model association {association.machine_id!r} has invalid persisted "
                        "activation provenance."
                    )
            configuration = loaded.protection_configuration
            if configuration is not None and configuration.project_id != context.project_id:
                raise ValueError("Protection configuration project_id does not match the candidate project.")
            control_configuration = loaded.control_configuration
            if control_configuration is not None:
                if control_configuration.project_id != context.project_id: raise ValueError("Control configuration project_id does not match the candidate project.")
                control_configuration.validate()

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
            measurement_definitions=measurement_channel_service.serialize_definitions(),
            control_configuration=control_service.configuration,
        )

    def new_network() -> Network:
        return Network()

    application.dynamic_models = dynamic_models
    application._control_service = control_service

    lifecycle = ProjectLifecycleService(
        network=network,
        network_factory=new_network,
        context=initial_context,
        loader=load_project,
        saver=save_project,
        activate_network=activate_network,
        project_state_activator=activate_project_state,
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

    def run_power_flow(request: StudyRequest, execution_context, token: StudyCancellationToken) -> Any:
        if token.cancelled:
            return None
        configuration = study_configuration(request, PowerFlowStudyConfiguration)
        prepared = StudyPreparationService(execution_context).prepare_power_flow(configuration)
        if token.cancelled:
            return None
        analysis = PowerFlowAnalysis.from_prepared(prepared)
        analysis.solve()
        if token.cancelled:
            return None
        return analysis.to_engineering_result()

    def run_short_circuit(request: StudyRequest, execution_context, token: StudyCancellationToken) -> Any:
        if token.cancelled:
            return None
        configuration = study_configuration(request, ShortCircuitStudyConfiguration)
        prepared = StudyPreparationService(execution_context).prepare_short_circuit(configuration)
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

    def run_transient_stability(request: StudyRequest, execution_context, token: StudyCancellationToken) -> Any:
        if token.cancelled:
            return None
        configuration = study_configuration(request, TransientStabilityStudyConfiguration)
        prepared_power_flow = request.configuration.get("prepared_power_flow")
        power_flow_result = request.configuration.get("power_flow_result")
        if not isinstance(prepared_power_flow, PreparedPowerFlow) or not isinstance(power_flow_result, PowerFlowResult):
            raise TypeError("transient_stability requires prepared_power_flow and power_flow_result in the study request.")
        prepared = StudyPreparationService(execution_context).prepare_transient_stability(
            configuration, prepared_power_flow, power_flow_result,
            DynamicMachineModelRegistry(execution_context.project_snapshot.dynamic_models),
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
