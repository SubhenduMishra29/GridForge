# ============================================================
# File: core/application/application.py
# GridForge V2 — Headless Application Facade
# Author: Subhendu Mishra
# ============================================================

"""Stable public Application facade for commands, reads, events, history, project lifecycle, and studies."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from core.control.context import ControlExecutionContext
from core.control.engine import ControlEngine

from .command import Command
from .command_manager import CommandManager
from .commands.sld_commands import AddSLDNodeCommand
from .commands.control_commands import (
    ADD_CONTROL_COMPONENT, REMOVE_CONTROL_COMPONENT,
    CONNECT_CONTROL_SIGNALS, DISCONNECT_CONTROL_SIGNALS,
    ADD_LADDER_RUNG, REMOVE_LADDER_RUNG, MOVE_LADDER_ELEMENT,
    ADD_LOGIC_DEPENDENCY, REMOVE_LOGIC_DEPENDENCY,
)
from .control_cycle import ControlCycleResult, ControlCycleService
from .control_dispatch import ControlCommandDispatcher
from .control_execution import ControlExecutionService
from .control_events import (
    ControlComponentCreated, ControlComponentRemoved,
    ControlConnectionCreated, ControlConnectionRemoved,
    ControlProgramChanged,
)
from .event_bus import ApplicationEventBus
from .events import (
    ElementCreated, ElementRemoved, ElementUpdated,
    NetworkChanged, ProjectClosed, ProjectLoaded, ProjectSaved,
    SLDPresentationChanged, TopologyChanged, ProtectionChanged, ValidationChanged,
    SimpleWireConnectionCreated, SimpleWireConnectionRemoved,
)
from .project import ProjectContext, ProjectSnapshot
from .project_lifecycle import ProjectLifecycleService
from .project_transition import ProjectTransitionDecision, ProjectTransitionRequired
from .read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel, RelayReadModel, SimpleWireReadModel
from .read_service import ProtectionReadService, ReadService
from .results import ApplicationResult
from core.persistence.network_serializer import deserialize_network, serialize_network
from .revision import ProjectRevision
from .revision_service import RevisionService
from .sld_command_handlers import SLDCommandHandlers
from .services.sld_service import SLDService
from .services.measurement_channel_service import MeasurementChannelService
from .services.validation_service import ValidationService
from .study import StudyExecutionContext, StudyRequest, StudyResult, StudyService
from .validation import ValidationResult


class Application:
    """Public headless GridForge Application facade."""

    _NETWORK_ELEMENT_CREATE_DELETE_TYPES = frozenset({
        "bus", "line", "cable", "transformer", "switch", "breaker", "disconnector", "fuse", "load",
        "generator", "synchronous_machine", "motor", "shunt", "capacitor", "reactor", "solar", "battery", "grid",
    })
    _STATE_CHANGE_FIELDS = frozenset({"closed", "in_service", "tripped", "blown", "status"})

    def __init__(self, command_manager: CommandManager, read_service: ReadService | None = None,
                 event_bus: ApplicationEventBus | None = None,
                 protection_read_service: ProtectionReadService | None = None,
                 validation_service: ValidationService | None = None,
                 sld_service: SLDService | None = None,
                 measurement_channel_service: MeasurementChannelService | None = None) -> None:
        if not isinstance(command_manager, CommandManager): raise TypeError("Application command_manager must be a CommandManager.")
        if read_service is not None and not isinstance(read_service, ReadService): raise TypeError("Application read_service must implement ReadService.")
        if event_bus is not None and not isinstance(event_bus, ApplicationEventBus): raise TypeError("Application event_bus must be an ApplicationEventBus.")
        if protection_read_service is not None and not isinstance(protection_read_service, ProtectionReadService): raise TypeError("Application protection_read_service must be a ProtectionReadService.")
        if validation_service is not None and not isinstance(validation_service, ValidationService): raise TypeError("Application validation_service must be a ValidationService.")
        if sld_service is not None and not isinstance(sld_service, SLDService): raise TypeError("Application sld_service must be an SLDService.")
        if measurement_channel_service is not None and not isinstance(measurement_channel_service, MeasurementChannelService): raise TypeError("Application measurement_channel_service must be a MeasurementChannelService.")
        self._command_manager = command_manager
        self._read_service = read_service
        self._protection_read_service = protection_read_service
        self._validation_service = validation_service
        self._sld_service = sld_service
        self._measurement_channel_service = measurement_channel_service
        self._event_bus = event_bus if event_bus is not None else ApplicationEventBus()
        self._project_lifecycle: ProjectLifecycleService | None = None
        self._revision_service = RevisionService()
        self._study_service = StudyService(self._event_bus)
        self._control_execution = ControlExecutionService(ControlCommandDispatcher(command_manager, command_executor=self.execute))
        self._command_manager.set_pre_commit_hook(self._coordinate_pre_commit)
        if self._sld_service is not None:
            self._register_sld_handlers(self._sld_service)

    @property
    def event_bus(self) -> ApplicationEventBus: return self._event_bus
    @property
    def control_execution(self) -> ControlExecutionService: return self._control_execution
    @property
    def study_service(self) -> StudyService: return self._study_service
    @property
    def project_lifecycle(self) -> ProjectLifecycleService:
        if self._project_lifecycle is None: raise RuntimeError("Application project lifecycle is not configured.")
        return self._project_lifecycle
    @property
    def revision(self) -> ProjectRevision: return self._revision_service.revision
    @property
    def is_dirty(self) -> bool: return self._revision_service.is_dirty
    @property
    def revision_service(self) -> RevisionService: return self._revision_service
    @property
    def validation_service(self) -> ValidationService:
        if self._validation_service is None: raise RuntimeError("Application validation service is not configured.")
        return self._validation_service
    @property
    def sld_service(self) -> SLDService:
        if self._sld_service is None: raise RuntimeError("Application SLD service is not configured.")
        return self._sld_service
    @property
    def presentation(self) -> Any: return self.project_lifecycle.presentation
    @property
    def measurement_channel_service(self) -> MeasurementChannelService:
        if self._measurement_channel_service is None: raise RuntimeError("Application measurement channel service is not configured.")
        return self._measurement_channel_service

    def _register_sld_handlers(self, service: SLDService) -> None:
        for command_type, handler in SLDCommandHandlers(service).handlers().items():
            self._command_manager.register_handler(command_type, handler)

    def attach_project_lifecycle(self, service: ProjectLifecycleService) -> None:
        if not isinstance(service, ProjectLifecycleService): raise TypeError("service must be a ProjectLifecycleService.")
        if self._project_lifecycle is not None and self._project_lifecycle is not service: raise RuntimeError("Application project lifecycle is already configured.")
        self._project_lifecycle = service
        if self._sld_service is not None:
            service.configure_presentation_activator(
                lambda context, presentation: self._bind_sld_transactionally(self._sld_service, presentation)
            )

    def configure_project_presentation(self, *, presentation: Any, serializer: Any, deserializer: Any) -> None:
        self.project_lifecycle.configure_presentation(presentation=presentation, serializer=serializer, deserializer=deserializer)
        if self._sld_service is not None:
            self.project_lifecycle.configure_presentation_activator(
                lambda context, value: self._bind_sld_transactionally(self._sld_service, value)
            )

    def configure_project_presentation_contract(self, *, factory: Any, serializer: Any, deserializer: Any) -> None:
        self.project_lifecycle.configure_presentation_contract(factory=factory, serializer=serializer, deserializer=deserializer)

    def configure_presentation_activator(self, activator: Any) -> None:
        if not callable(activator): raise TypeError("activator must be callable.")
        if self._sld_service is None:
            self.project_lifecycle.configure_presentation_activator(activator)
            return
        sld_service = self._sld_service

        def composite(context: ProjectContext | None, value: Any | None):
            sld_rollback = self._bind_sld_transactionally(sld_service, value)
            try:
                workspace_rollback = activator(context, value)
            except BaseException:
                sld_rollback()
                raise

            def rollback() -> None:
                try:
                    if workspace_rollback is not None:
                        workspace_rollback()
                finally:
                    sld_rollback()

            return rollback

        self.project_lifecycle.configure_presentation_activator(composite)

    @staticmethod
    def _bind_sld_transactionally(service: SLDService, value: Any) -> Any:
        previous = service.document if service.is_bound else None
        if value is None: service.detach_document()
        else: service.bind_document(value)

        def rollback() -> None:
            if previous is None: service.detach_document()
            else: service.bind_document(previous)
        return rollback

    def attach_sld_service(self, service: SLDService) -> None:
        if not isinstance(service, SLDService): raise TypeError("service must be an SLDService.")
        if self._sld_service is not None and self._sld_service is not service: raise RuntimeError("Application SLD service is already configured.")
        self._sld_service = service
        service.attach_application(self)
        self._command_manager.set_pre_commit_hook(self._coordinate_pre_commit)
        if self._project_lifecycle is not None:
            self._project_lifecycle.configure_presentation_activator(
                lambda context, value: self._bind_sld_transactionally(service, value)
            )
        self._register_sld_handlers(service)
        presentation = self.presentation if self._project_lifecycle is not None else None
        if presentation is not None: service.bind_document(presentation)

    @staticmethod
    def _coerce_transition_decision(decision: ProjectTransitionDecision | str | None) -> ProjectTransitionDecision | None:
        if decision is None: return None
        if isinstance(decision, ProjectTransitionDecision): return decision
        if isinstance(decision, str):
            try: return ProjectTransitionDecision(decision.strip().lower())
            except ValueError as exc: raise ValueError(f"Unsupported project transition decision: {decision!r}") from exc
        raise TypeError("decision must be ProjectTransitionDecision, string, or None.")

    def _prepare_project_transition(self, decision: ProjectTransitionDecision | str | None) -> bool:
        if not self.is_dirty: return True
        normalized = self._coerce_transition_decision(decision)
        if normalized is None:
            raise ProjectTransitionRequired("The active project is dirty; the transition requires SAVE, DISCARD, or CANCEL.")
        if normalized is ProjectTransitionDecision.CANCEL: return False
        if normalized is ProjectTransitionDecision.SAVE:
            self.save_project()
            return True
        if normalized is ProjectTransitionDecision.DISCARD:
            self._run_project_transition(self.project_lifecycle.discard_project_changes)
            return True
        raise RuntimeError(f"Unhandled transition decision: {normalized!r}")

    def _run_project_transition(self, transition: Any) -> Any:
        """Coordinate revision/validation state around one lifecycle activation transaction."""
        if not callable(transition):
            raise TypeError("transition must be callable.")
        revision_state = self._revision_service.snapshot_state()
        try:
            result = transition()
        except BaseException:
            self._revision_service.restore_state(revision_state)
            raise

        # Lifecycle activation has committed successfully; only now establish
        # the clean baseline for the newly authoritative project state.
        self._revision_service.reset_for_project()
        if self._validation_service is not None:
            self._validation_service.invalidate()
            self._event_bus.publish(
                ValidationChanged(
                    metadata={
                        "valid": False,
                        "invalidated": True,
                        "reason": "project_transition",
                        **self._project_scope_metadata(),
                    }
                )
            )
        return result

    def discard_project_changes(self) -> ProjectContext:
        """Discard active-project changes through the existing lifecycle transaction."""
        self._study_service.ensure_no_active_studies()
        return self._run_project_transition(self.project_lifecycle.discard_project_changes)

    def new_project(self, name: str = "Untitled Project", *, project_id: str | None = None,
                    decision: ProjectTransitionDecision | str | None = None) -> ProjectContext:
        self._study_service.ensure_no_active_studies()
        if not self._prepare_project_transition(decision):
            current = self.project_lifecycle.context
            if current is None: raise RuntimeError("Cancel cannot leave the Application without an active project.")
            return current
        context = self._run_project_transition(
            lambda: self.project_lifecycle.new_project(name, project_id=project_id)
        )
        self._event_bus.publish(ProjectLoaded(metadata={
            "project_id": context.project_id, "name": context.name, "operation": "new",
            "activation_generation": self.project_lifecycle.activation_generation,
            "semantic_scope": "APPLICATION_PROJECT_ACTIVATED", "ui_workspace_ready": False,
        }))
        return context

    def open_project(self, path: str, *, decision: ProjectTransitionDecision | str | None = None) -> ProjectContext:
        self._study_service.ensure_no_active_studies()
        if not self._prepare_project_transition(decision):
            current = self.project_lifecycle.context
            if current is None: raise RuntimeError("Cancel cannot leave the Application without an active project.")
            return current
        context = self._run_project_transition(lambda: self.project_lifecycle.open_project(path))
        self._event_bus.publish(ProjectLoaded(metadata={
            "project_id": context.project_id, "name": context.name,
            "path": str(context.path) if context.path else None, "operation": "open",
            "activation_generation": self.project_lifecycle.activation_generation,
            "semantic_scope": "APPLICATION_PROJECT_ACTIVATED", "ui_workspace_ready": False,
        }))
        return context

    def save_project(self, path: str | None = None) -> ProjectContext:
        context = self.project_lifecycle.save_project(path)
        self._revision_service.mark_persisted()
        self._event_bus.publish(ProjectSaved(metadata={
            "project_id": context.project_id, "path": str(context.path) if context.path else None,
            "activation_generation": self.project_lifecycle.activation_generation,
        }))
        return context

    def save_project_as(self, path: str) -> ProjectContext:
        context = self.project_lifecycle.save_project_as(path)
        self._revision_service.mark_persisted()
        self._event_bus.publish(ProjectSaved(metadata={
            "project_id": context.project_id, "path": str(context.path) if context.path else None,
            "activation_generation": self.project_lifecycle.activation_generation,
        }))
        return context

    def close_project(self, *, decision: ProjectTransitionDecision | str | None = None) -> ProjectContext | None:
        self._study_service.ensure_no_active_studies()
        if not self._prepare_project_transition(decision): return self.project_lifecycle.context
        previous_generation = self.project_lifecycle.activation_generation
        context = self._run_project_transition(self.project_lifecycle.close_project)
        if context is not None:
            self._event_bus.publish(ProjectClosed(metadata={
                "project_id": context.project_id, "name": context.name,
                "activation_generation": previous_generation, "operation": "close",
                "semantic_scope": "APPLICATION_PROJECT_ACTIVATED", "ui_workspace_ready": False,
            }))
        return context

    def capture_project_snapshot(self) -> ProjectSnapshot:
        lifecycle = self.project_lifecycle
        context = lifecycle.context
        if context is None: raise RuntimeError("No active project.")
        network_snapshot = deserialize_network(serialize_network(lifecycle.network))
        dynamic_models = tuple(getattr(getattr(self, "dynamic_models", None), "snapshot", lambda: ())())
        return ProjectSnapshot(project_id=context.project_id, activation_generation=lifecycle.activation_generation,
                               revision=self.revision, network=network_snapshot, dynamic_models=dynamic_models)

    def execute_study(self, request: StudyRequest) -> StudyResult:
        if not isinstance(request, StudyRequest):
            raise TypeError("request must be a StudyRequest.")
        lifecycle = self.project_lifecycle
        context = lifecycle.context
        if context is None or not lifecycle.has_project or lifecycle.state != "ACTIVE":
            raise RuntimeError("Cannot start a study without a valid active project activation.")
        if request.project_id != context.project_id or request.activation_generation != lifecycle.activation_generation:
            raise ValueError("StudyRequest project scope does not match the active project generation.")
        # Project validation is an Application study gate. A study cannot
        # publish StudyStarted until authoritative project validation succeeds.
        validation = self.validate_project()
        if not validation.valid:
            raise ValueError("Project validation failed; study execution is blocked before StudyStarted.")
        if request.source_revision != self.revision:
            raise ValueError("StudyRequest source_revision does not match the active project revision.")
        network = lifecycle.network
        # Runtime-only provenance metadata; never authoritative persisted state.
        network.project_id = context.project_id
        network.activation_generation = lifecycle.activation_generation
        if network.state.topology_revision != request.source_revision.topology_revision:
            raise ValueError("Network topology revision does not match StudyRequest source revision.")
        if network.state.topology_dirty or not network.state.topology_valid:
            network.rebuild_topology()
        if network.state.topology_dirty or not network.state.topology_valid:
            raise ValueError("Topology normalization did not produce a valid study-ready state.")
        snapshot = network.topology_snapshot
        if snapshot is None:
            raise ValueError("Canonical TopologySnapshot is unavailable.")
        if snapshot.project_id != request.project_id or snapshot.activation_generation != request.activation_generation or snapshot.topology_revision != request.source_revision.topology_revision:
            raise ValueError("TopologySnapshot provenance does not match StudyRequest.")
        project_snapshot = self.capture_project_snapshot()
        execution_context = StudyExecutionContext(
            project_id=request.project_id,
            activation_generation=request.activation_generation,
            source_revision=request.source_revision,
            topology_snapshot=snapshot,
            project_snapshot=project_snapshot,
        )
        return self._study_service.execute(request, execution_context)

    def study_result(self, study_id, *, project_id: str, activation_generation: int) -> StudyResult | None:
        return self._study_service.get_result(study_id, project_id=project_id, activation_generation=activation_generation)

    def cancel_study(self, study_id, *, project_id: str, activation_generation: int) -> bool:
        return self._study_service.cancel(study_id, project_id=project_id, activation_generation=activation_generation)

    def _replace_runtime(self, command_manager: CommandManager, read_service: ReadService, validation_service: ValidationService | None = None) -> None:
        if not isinstance(command_manager, CommandManager): raise TypeError("Application command_manager must be a CommandManager.")
        if not isinstance(read_service, ReadService): raise TypeError("read_service must implement ReadService.")
        if validation_service is not None and not isinstance(validation_service, ValidationService): raise TypeError("validation_service must be a ValidationService.")
        if self._sld_service is not None:
            for command_type, handler in SLDCommandHandlers(self._sld_service).handlers().items():
                command_manager.register_handler(command_type, handler)
        next_control_execution = ControlExecutionService(ControlCommandDispatcher(command_manager, command_executor=self.execute))
        self._command_manager, self._read_service, self._validation_service, self._control_execution = command_manager, read_service, validation_service, next_control_execution
        self._command_manager.set_pre_commit_hook(self._coordinate_pre_commit)

    def _coordinate_pre_commit(self, command: Command, result: ApplicationResult, transaction: Any) -> None:
        """Coordinate placement presentation mutation inside the same transaction."""
        if self._sld_service is None or command.command_type not in {"model.create_relay"} and not command.command_type.startswith("model.create_"):
            return
        # Most placement tools carry presentation_x/presentation_y.
        # PlaceBusCommand is a compatibility constructor whose canonical
        # CREATE_BUS payload still carries x/y; the Bus command handler removes
        # those fields before Core mutation. Normalize both forms here so Bus
        # placement participates in the same Application transaction without
        # treating coordinates as Core electrical properties.
        x = command.payload.get("presentation_x")
        y = command.payload.get("presentation_y")
        if x is None and command.command_type == "model.create_bus":
            x = command.payload.get("x")
        if y is None and command.command_type == "model.create_bus":
            y = command.payload.get("y")
        if x is None or y is None:
            return
        element_id = self._element_id(command)
        element_type = self._element_type(command)
        if element_id is None or element_type is None:
            raise ValueError("Placement command must expose canonical element identity and type.")
        source = "protection_read_model" if element_type.upper() == "RELAY" else "application_read_model"
        existing = self._sld_service.document.model.get_node_by_equipment_id_optional(element_id)
        if existing is not None:
            owner = existing.properties.get("presentation_owner")
            if owner == "engineer" and existing.properties.get("projection_source") is None:
                return
            if existing.properties.get("projection_source") != source:
                raise ValueError(f"Placement projection ownership collision for equipment ID: {element_id!r}")
            return
        projection_result = self._sld_service.execute(
            AddSLDNodeCommand(
                node_id=f"sld-node-{element_id}",
                equipment_id=element_id,
                x=float(x),
                y=float(y),
                presentation_owner="engineer",
                projection_source=None,
                element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.command_id,
            ),
            transaction,
        )
        if not projection_result.success:
            raise RuntimeError(projection_result.message)

    def mark_project_persisted(self) -> ProjectRevision: return self._revision_service.mark_persisted()
    def record_presentation_change(self) -> ProjectRevision: return self._revision_service.record_presentation_change()

    def validate_project(self) -> ValidationResult:
        context = self.project_lifecycle.context
        if context is None: raise RuntimeError("Validation requires an active project.")
        result = self.validation_service.validate_project(context=context, presentation=self.presentation)
        scoped = replace(result, project_id=context.project_id, activation_generation=self.project_lifecycle.activation_generation)
        self._event_bus.publish(ValidationChanged(metadata={
            "valid": scoped.valid,
            "errors": scoped.summary.errors,
            "warnings": scoped.summary.warnings,
            "model_revision": scoped.model_revision,
            "topology_revision": scoped.topology_revision,
            "project_id": scoped.project_id,
            "activation_generation": scoped.activation_generation,
        }))
        return scoped

    def read_validation(self) -> ValidationResult | None:
        result = self.validation_service.read_validation()
        if result is None: return None
        context = self.project_lifecycle.context
        if context is None: return None
        return replace(result, project_id=context.project_id, activation_generation=self.project_lifecycle.activation_generation)

    def execute_control_cycle(self, control_engine: ControlEngine, *, simulation_time: float | None = None,
                              external_inputs: Mapping[str, Mapping[str, Any]] | None = None,
                              context: ControlExecutionContext | None = None,
                              interlock_inputs: Mapping[str, Mapping[str, bool]] | None = None) -> ControlCycleResult:
        return ControlCycleService(control_engine, self._control_execution).execute(simulation_time=simulation_time, external_inputs=external_inputs, context=context, interlock_inputs=interlock_inputs)

    def execute(self, command: Command) -> ApplicationResult:
        if not isinstance(command, Command): raise TypeError("Application.execute requires a Command.")
        result = self._command_manager.execute(command)
        if result.success:
            if command.command_type.startswith("sld."): self._revision_service.record_presentation_change()
            else:
                self._revision_service.record_command_success(command)
                if self._validation_service is not None:
                    self._validation_service.invalidate()
                    self._event_bus.publish(ValidationChanged(metadata={"valid": False, "invalidated": True, **self._project_scope_metadata()}))
            self._publish_semantic_events(command, result, operation="execute")
        return result

    def supports(self, command_type: str) -> bool: return isinstance(command_type, str) and self._command_manager.is_registered(command_type)
    def command_types(self) -> tuple[str, ...]: return self._command_manager.registered_commands

    def undo(self) -> ApplicationResult | None:
        records = self._command_manager.undo_commands()
        command = records[-1].command if records else None
        result = self._command_manager.undo()
        if result is not None and result.success:
            self._revision_service.record_undo()
            if self._validation_service is not None and command is not None and not command.command_type.startswith("sld."):
                self._validation_service.invalidate()
                self._event_bus.publish(ValidationChanged(metadata={"valid": False, "invalidated": True, **self._project_scope_metadata()}))
            self._publish_history_events(command, result, operation="undo")
        return result

    def redo(self) -> ApplicationResult | None:
        records = self._command_manager.redo_commands()
        command = records[-1].command if records else None
        result = self._command_manager.redo()
        if result is not None and result.success and command is not None:
            self._revision_service.record_redo()
            if self._validation_service is not None and not command.command_type.startswith("sld."):
                self._validation_service.invalidate()
                self._event_bus.publish(ValidationChanged(metadata={"valid": False, "invalidated": True, **self._project_scope_metadata()}))
            self._publish_semantic_events(command, result, operation="redo")
        return result

    def can_undo(self) -> bool: return self._command_manager.can_undo()
    def can_redo(self) -> bool: return self._command_manager.can_redo()
    def undo_count(self) -> int: return self._command_manager.undo_count()
    def redo_count(self) -> int: return self._command_manager.redo_count()
    def undo_commands(self) -> tuple: return self._command_manager.undo_commands()
    def redo_commands(self) -> tuple: return self._command_manager.redo_commands()
    def clear_history(self) -> None: self._command_manager.clear_history()

    def read_network(self) -> NetworkReadModel:
        self._require_read_service(); return self._read_service.network()  # type: ignore[union-attr]
    def read_element(self, element_type: str, object_id: str) -> ElementReadModel:
        self._require_read_service(); return self._read_service.element(element_type, object_id)  # type: ignore[union-attr]
    def read_simple_wire(self, connection_id: str) -> SimpleWireReadModel:
        network = self.read_network()
        for connection in network.simple_wires:
            if connection.connection_id == connection_id:
                return connection
        raise KeyError(f"Simple Wire connection '{connection_id}' is not represented by the Application read model.")

    def read_protection(self) -> ProtectionReadModel:
        self._require_protection_read_service(); return self._protection_read_service.protection()  # type: ignore[union-attr]
    def read_relay(self, relay_id: str) -> RelayReadModel:
        self._require_protection_read_service(); return self._protection_read_service.relay(relay_id)  # type: ignore[union-attr]

    def _project_scope_metadata(self) -> dict[str, object]:
        context = self.project_lifecycle.context
        return {"project_id": context.project_id if context is not None else None,
                "activation_generation": self.project_lifecycle.activation_generation}

    def _publish_semantic_events(self, command: Command, result: ApplicationResult, *, operation: str) -> None:
        metadata = {**dict(result.metadata), "command_id": str(command.command_id), "message": result.message, "operation": operation}
        if command.command_type in {"connectivity.create_simple_wire", "connectivity.remove_simple_wire"}:
            action = "create" if command.command_type.endswith("create_simple_wire") else "remove"
            if operation == "undo":
                action = "remove" if action == "create" else "create"
            event_type = SimpleWireConnectionCreated if action == "create" else SimpleWireConnectionRemoved
            endpoint_a = metadata.get("endpoint_a") or getattr(command, "payload", {}).get("endpoint_a")
            endpoint_b = metadata.get("endpoint_b") or getattr(command, "payload", {}).get("endpoint_b")
            if endpoint_a is None or endpoint_b is None:
                raise RuntimeError(
                    f"Simple Wire semantic event lacks endpoint snapshots for {metadata.get('connection_id')!r}."
                )
            if hasattr(endpoint_a, "to_mapping"):
                endpoint_a = endpoint_a.to_mapping()
            if hasattr(endpoint_b, "to_mapping"):
                endpoint_b = endpoint_b.to_mapping()
            self._event_bus.publish(event_type(
                connection_id=str(metadata.get("connection_id") or getattr(command, "payload", {}).get("connection_id")),
                endpoint_a=endpoint_a,
                endpoint_b=endpoint_b,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                metadata=metadata,
            ))
            self._event_bus.publish(TopologyChanged(operation=operation, metadata=metadata, correlation_id=command.correlation_id, causation_id=command.causation_id))
            self._event_bus.publish(NetworkChanged(operation=operation, metadata=metadata, correlation_id=command.correlation_id, causation_id=command.causation_id))
        elif command.command_type in {"model.connect_terminal", "model.disconnect_terminal", "model.reconnect_terminal"}:
            self._event_bus.publish(TopologyChanged(operation=operation, metadata=metadata, correlation_id=command.correlation_id, causation_id=command.causation_id))
            self._event_bus.publish(NetworkChanged(operation=operation, metadata=metadata, correlation_id=command.correlation_id, causation_id=command.causation_id))
        elif command.command_type.startswith("model."):
            self._publish_model_event(command, metadata, operation=operation); self._publish_network_changed(command, metadata)
        elif command.command_type.startswith("control."): self._publish_control_event(command, result, metadata, operation=operation)
        elif command.command_type.startswith("sld."):
            payload = dict(result.metadata)
            payload.update(metadata)
            self._event_bus.publish(SLDPresentationChanged(operation=operation, metadata=payload,
                                                          correlation_id=command.correlation_id,
                                                          causation_id=command.causation_id))

    def _publish_control_event(self, command: Command, result: ApplicationResult, metadata: dict[str, object], *, operation: str) -> None:
        command_type = command.command_type; payload = dict(result.metadata); payload.update(metadata)
        cid, caid = command.correlation_id, command.causation_id
        if command_type == ADD_CONTROL_COMPONENT: self._event_bus.publish(ControlComponentCreated(component_id=str(payload["component_id"]), component_type=str(payload["component_type"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type == REMOVE_CONTROL_COMPONENT: self._event_bus.publish(ControlComponentRemoved(component_id=str(payload["component_id"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type == CONNECT_CONTROL_SIGNALS: self._event_bus.publish(ControlConnectionCreated(source_id=str(command.payload["source_component"]), target_id=str(command.payload["target_component"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type == DISCONNECT_CONTROL_SIGNALS: self._event_bus.publish(ControlConnectionRemoved(source_id=str(command.payload["source_component"]), target_id=str(command.payload["target_component"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type in {ADD_LADDER_RUNG, REMOVE_LADDER_RUNG, MOVE_LADDER_ELEMENT, ADD_LOGIC_DEPENDENCY, REMOVE_LOGIC_DEPENDENCY}: self._event_bus.publish(ControlProgramChanged(metadata={**payload, "command_type": command_type}, correlation_id=cid, causation_id=caid))

    def _publish_history_events(self, command: Command | None, result: ApplicationResult, *, operation: str) -> None:
        if command is not None: self._publish_semantic_events(command, result, operation=operation)

    def _publish_model_event(self, command: Command, metadata: dict[str, object], *, operation: str) -> None:
        action = self._action_from_command_type(command.command_type); element_type = self._element_type(command); element_id = self._element_id(command)
        if element_type is None or element_id is None: return
        effective_action = {"create": "delete", "delete": "create"}.get(action, action) if operation == "undo" else action
        if effective_action == "create":
            self._event_bus.publish(ElementCreated(
                element_id=element_id,
                element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                metadata=metadata,
            ))
        elif effective_action == "delete":
            self._event_bus.publish(ElementRemoved(
                element_id=element_id,
                element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                metadata=metadata,
            ))
        elif effective_action in {"update", "open", "close", "reset", "blow", "trip", "put_in_service", "take_out_of_service"}:
            self._event_bus.publish(ElementUpdated(
                element_id=element_id,
                element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                changes=metadata,
            ))

    def _publish_network_changed(self, command: Command, metadata: dict[str, object]) -> None:
        if not self._is_network_change_command(command): return
        operation = str(metadata.get("operation", "execute"))
        if self._is_topology_command(command):
            self._event_bus.publish(TopologyChanged(
                operation=operation,
                metadata=metadata,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            ))
        self._event_bus.publish(NetworkChanged(
            operation=operation,
            metadata=metadata,
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
        ))

    @classmethod
    def _is_network_change_command(cls, command: Command) -> bool:
        if not command.command_type.startswith("model."): return False
        if cls._is_topology_command(command): return True
        action = cls._action_from_command_type(command.command_type)
        if action not in {"create", "delete"}: return False
        return cls._element_type(command) in cls._NETWORK_ELEMENT_CREATE_DELETE_TYPES

    @classmethod
    def _is_topology_command(cls, command: Command) -> bool: return RevisionService.is_topology_command(command)

    @staticmethod
    def _action_from_command_type(command_type: str) -> str:
        action = command_type.rsplit(".", 1)[-1]
        for prefix, value in (("create_", "create"), ("delete_", "delete"), ("update_", "update")):
            if action.startswith(prefix): return value
        return action

    @staticmethod
    def _element_type(command: Command) -> str | None:
        payload = command.payload; value = payload.get("element_type") or payload.get("equipment_type")
        if value is None and command.command_type.startswith("model."):
            action = command.command_type.split(".", 1)[1]
            for prefix in ("create_", "update_", "delete_", "open_", "close_", "trip_", "put_", "take_", "blow_", "reset_"):
                if action.startswith(prefix): return action[len(prefix):].removesuffix("_in_service").removesuffix("_out_of_service")
        return str(value) if value is not None else None

    @staticmethod
    def _element_id(command: Command) -> str | None:
        payload = command.payload; value = payload.get("element_id") or payload.get("equipment_id") or payload.get("id")
        if value is None:
            for key in ("bus_id", "breaker_id", "switch_id", "disconnector_id", "fuse_id", "line_id", "transformer_id", "cable_id"):
                if key in payload: value = payload[key]; break
        return str(value) if value is not None else None

    def _require_read_service(self) -> None:
        if self._read_service is None: raise RuntimeError("Application read service is not configured.")
    def _require_protection_read_service(self) -> None:
        if self._protection_read_service is None: raise RuntimeError("Application protection read service is not configured.")
