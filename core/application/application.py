# ============================================================
# File: core/application/application.py
# GridForge V2 — Headless Application Facade
# Author: Subhendu Mishra
# ============================================================

"""Stable public Application facade for commands, reads, events, history, project lifecycle, and studies."""

from __future__ import annotations

from typing import Any, Mapping

from core.control.context import ControlExecutionContext
from core.control.engine import ControlEngine

from .command import Command
from .command_manager import CommandManager
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
    ControlComponentCreated,
    ControlComponentRemoved,
    ControlConnectionCreated,
    ControlConnectionRemoved,
    ControlProgramChanged,
)
from .event_bus import ApplicationEventBus
from .events import (
    ElementCreated,
    ElementRemoved,
    ElementUpdated,
    NetworkChanged,
    TopologyChanged,
    ValidationChanged,
)
from .project import ProjectContext
from .project_lifecycle import ProjectLifecycleService
from .read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel, RelayReadModel
from .read_service import ProtectionReadService, ReadService
from .results import ApplicationResult
from .revision import ProjectRevision
from .revision_service import RevisionService
from .services.sld_service import SLDService
from .services.validation_service import ValidationService
from .study import StudyRequest, StudyResult, StudyService
from .validation import ValidationResult


class Application:
    """Public headless GridForge Application facade."""

    _TOPOLOGY_COMMANDS = frozenset({
        "model.create_line", "model.delete_line", "model.create_transformer", "model.delete_transformer",
        "model.create_cable", "model.update_cable", "model.delete_cable", "model.create_switch",
        "model.update_switch", "model.delete_switch", "model.open_switch", "model.close_switch",
        "model.put_switch_in_service", "model.take_switch_out_of_service", "model.create_disconnector",
        "model.update_disconnector", "model.delete_disconnector", "model.open_disconnector",
        "model.close_disconnector", "model.put_disconnector_in_service", "model.take_disconnector_out_of_service",
        "model.create_fuse", "model.delete_fuse", "model.blow_fuse", "model.reset_fuse",
        "model.put_fuse_in_service", "model.take_fuse_out_of_service",
        "model.create_breaker", "model.delete_breaker", "model.open_breaker", "model.close_breaker",
        "model.trip_breaker", "model.put_breaker_in_service", "model.take_breaker_out_of_service",
    })

    # NetworkChanged is deliberately narrower than "any model command".
    # It invalidates aggregate network/topology projections, not every
    # electrical-data edit. ElementUpdated remains authoritative for those.
    _NETWORK_ELEMENT_CREATE_DELETE_TYPES = frozenset({
        "bus", "line", "cable", "transformer", "switch", "breaker",
        "disconnector", "fuse", "load", "generator", "synchronous_machine",
        "motor", "shunt", "capacitor", "reactor", "solar", "battery", "grid",
    })

    def __init__(self, command_manager: CommandManager, read_service: ReadService | None = None,
                 event_bus: ApplicationEventBus | None = None,
                 protection_read_service: ProtectionReadService | None = None,
                 validation_service: ValidationService | None = None,
                 sld_service: SLDService | None = None) -> None:
        if not isinstance(command_manager, CommandManager):
            raise TypeError("Application command_manager must be a CommandManager.")
        if read_service is not None and not isinstance(read_service, ReadService):
            raise TypeError("Application read_service must implement ReadService.")
        if event_bus is not None and not isinstance(event_bus, ApplicationEventBus):
            raise TypeError("Application event_bus must be an ApplicationEventBus.")
        if protection_read_service is not None and not isinstance(protection_read_service, ProtectionReadService):
            raise TypeError("Application protection_read_service must be a ProtectionReadService.")
        if validation_service is not None and not isinstance(validation_service, ValidationService):
            raise TypeError("Application validation_service must be a ValidationService.")
        if sld_service is not None and not isinstance(sld_service, SLDService):
            raise TypeError("Application sld_service must be an SLDService.")
        self._command_manager = command_manager
        self._read_service = read_service
        self._protection_read_service = protection_read_service
        self._validation_service = validation_service
        self._sld_service = sld_service
        self._event_bus = event_bus if event_bus is not None else ApplicationEventBus()
        self._project_lifecycle: ProjectLifecycleService | None = None
        self._revision_service = RevisionService()
        self._study_service = StudyService(self._event_bus)
        self._control_execution = ControlExecutionService(
            ControlCommandDispatcher(command_manager, command_executor=self.execute)
        )

    @property
    def event_bus(self) -> ApplicationEventBus:
        return self._event_bus

    @property
    def control_execution(self) -> ControlExecutionService:
        return self._control_execution

    @property
    def study_service(self) -> StudyService:
        """Return the single Application-owned study orchestration service."""
        return self._study_service

    @property
    def project_lifecycle(self) -> ProjectLifecycleService:
        if self._project_lifecycle is None:
            raise RuntimeError("Application project lifecycle is not configured.")
        return self._project_lifecycle

    @property
    def revision(self) -> ProjectRevision:
        return self._revision_service.revision

    @property
    def is_dirty(self) -> bool:
        return self._revision_service.is_dirty

    @property
    def revision_service(self) -> RevisionService:
        return self._revision_service

    @property
    def validation_service(self) -> ValidationService:
        if self._validation_service is None:
            raise RuntimeError("Application validation service is not configured.")
        return self._validation_service

    @property
    def sld_service(self) -> SLDService:
        if self._sld_service is None:
            raise RuntimeError("Application SLD service is not configured.")
        return self._sld_service

    @property
    def presentation(self) -> Any:
        return self.project_lifecycle.presentation

    def attach_project_lifecycle(self, service: ProjectLifecycleService) -> None:
        if not isinstance(service, ProjectLifecycleService):
            raise TypeError("service must be a ProjectLifecycleService.")
        if self._project_lifecycle is not None and self._project_lifecycle is not service:
            raise RuntimeError("Application project lifecycle is already configured.")
        self._project_lifecycle = service

    def configure_project_presentation(self, *, presentation: Any, serializer: Any, deserializer: Any) -> None:
        self.project_lifecycle.configure_presentation(
            presentation=presentation,
            serializer=serializer,
            deserializer=deserializer,
        )

    def attach_sld_service(self, service: SLDService) -> None:
        if not isinstance(service, SLDService):
            raise TypeError("service must be an SLDService.")
        if self._sld_service is not None and self._sld_service is not service:
            raise RuntimeError("Application SLD service is already configured.")
        self._sld_service = service

    def new_project(self, name: str = "Untitled Project", *, project_id: str | None = None) -> ProjectContext:
        return self.project_lifecycle.new_project(name, project_id=project_id)

    def open_project(self, path: str) -> ProjectContext:
        return self.project_lifecycle.open_project(path)

    def save_project(self, path: str | None = None) -> ProjectContext:
        context = self.project_lifecycle.save_project(path)
        self._revision_service.mark_persisted()
        return context

    def save_project_as(self, path: str) -> ProjectContext:
        context = self.project_lifecycle.save_project_as(path)
        self._revision_service.mark_persisted()
        return context

    def close_project(self) -> ProjectContext | None:
        context = self.project_lifecycle.close_project()
        if context is not None:
            self._revision_service.reset_for_project()
        return context

    def execute_study(self, request: StudyRequest) -> StudyResult:
        """Execute an immutable study request through the Application boundary."""
        return self._study_service.execute(request)

    def study_result(self, study_id) -> StudyResult | None:
        """Return a previously registered immutable study result."""
        return self._study_service.get_result(study_id)

    def cancel_study(self, study_id) -> bool:
        """Request cooperative cancellation of an active study."""
        return self._study_service.cancel(study_id)

    def _replace_runtime(self, command_manager: CommandManager, read_service: ReadService,
                         validation_service: ValidationService | None = None) -> None:
        if not isinstance(command_manager, CommandManager):
            raise TypeError("Application command_manager must be a CommandManager.")
        if not isinstance(read_service, ReadService):
            raise TypeError("Application read_service must implement ReadService.")
        if validation_service is not None and not isinstance(validation_service, ValidationService):
            raise TypeError("validation_service must be a ValidationService.")
        self._command_manager = command_manager
        self._read_service = read_service
        self._validation_service = validation_service
        self._revision_service.reset_for_project()
        self._control_execution = ControlExecutionService(
            ControlCommandDispatcher(command_manager, command_executor=self.execute)
        )

    def mark_project_persisted(self) -> ProjectRevision:
        return self._revision_service.mark_persisted()

    def record_presentation_change(self) -> ProjectRevision:
        return self._revision_service.record_presentation_change()

    def validate_project(self) -> ValidationResult:
        result = self.validation_service.validate_project()
        self._event_bus.publish(ValidationChanged(metadata={
            "valid": result.valid,
            "errors": result.summary.errors,
            "warnings": result.summary.warnings,
            "model_revision": result.model_revision,
            "topology_revision": result.topology_revision,
        }))
        return result

    def read_validation(self) -> ValidationResult | None:
        return self.validation_service.read_validation()

    def execute_control_cycle(self, control_engine: ControlEngine, *, simulation_time: float | None = None,
                              external_inputs: Mapping[str, Mapping[str, Any]] | None = None,
                              context: ControlExecutionContext | None = None,
                              interlock_inputs: Mapping[str, Mapping[str, bool]] | None = None) -> ControlCycleResult:
        cycle = ControlCycleService(control_engine, self._control_execution)
        return cycle.execute(simulation_time=simulation_time, external_inputs=external_inputs,
                             context=context, interlock_inputs=interlock_inputs)

    def execute(self, command: Command) -> ApplicationResult:
        if not isinstance(command, Command):
            raise TypeError("Application.execute requires a Command.")
        if command.command_type.startswith("sld."):
            result = self.sld_service.execute(command)
            if result.success:
                self._revision_service.record_presentation_change()
            return result
        result = self._command_manager.execute(command)
        if result.success:
            self._revision_service.record_command_success(command)
            if self._validation_service is not None:
                self._validation_service.invalidate()
                self._event_bus.publish(ValidationChanged(metadata={"valid": False, "invalidated": True}))
            self._publish_semantic_events(command, result, operation="execute")
        return result

    def supports(self, command_type: str) -> bool:
        if not isinstance(command_type, str):
            return False
        if self._sld_service is not None and command_type in SLDService.COMMAND_TYPES:
            return True
        return self._command_manager.is_registered(command_type)

    def command_types(self) -> tuple[str, ...]:
        model_commands = self._command_manager.registered_commands
        if self._sld_service is None:
            return model_commands
        return tuple(model_commands) + tuple(sorted(SLDService.COMMAND_TYPES))

    def undo(self) -> ApplicationResult | None:
        records = self._command_manager.undo_commands()
        command = records[-1].command if records else None
        result = self._command_manager.undo()
        if result is not None and result.success:
            self._revision_service.record_undo()
            if self._validation_service is not None:
                self._validation_service.invalidate()
                self._event_bus.publish(ValidationChanged(metadata={"valid": False, "invalidated": True}))
            self._publish_history_events(command, result, operation="undo")
        return result

    def redo(self) -> ApplicationResult | None:
        records = self._command_manager.redo_commands()
        command = records[-1].command if records else None
        result = self._command_manager.redo()
        if result is not None and result.success and command is not None:
            self._revision_service.record_redo()
            if self._validation_service is not None:
                self._validation_service.invalidate()
                self._event_bus.publish(ValidationChanged(metadata={"valid": False, "invalidated": True}))
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

    def read_protection(self) -> ProtectionReadModel:
        self._require_protection_read_service(); return self._protection_read_service.protection()  # type: ignore[union-attr]

    def read_relay(self, relay_id: str) -> RelayReadModel:
        self._require_protection_read_service(); return self._protection_read_service.relay(relay_id)  # type: ignore[union-attr]

    def _publish_semantic_events(self, command: Command, result: ApplicationResult, *, operation: str) -> None:
        metadata = {"command_id": str(command.command_id), "message": result.message, "operation": operation}
        if command.command_type.startswith("model."):
            self._publish_model_event(command, metadata, operation=operation)
            self._publish_network_changed(command, metadata)
        elif command.command_type.startswith("control."):
            self._publish_control_event(command, result, metadata, operation=operation)

    def _publish_control_event(self, command: Command, result: ApplicationResult,
                               metadata: dict[str, object], *, operation: str) -> None:
        command_type = command.command_type
        payload = dict(result.metadata)
        payload.update(metadata)
        cid, caid = command.correlation_id, command.causation_id
        if command_type == ADD_CONTROL_COMPONENT:
            self._event_bus.publish(ControlComponentCreated(component_id=str(payload["component_id"]), component_type=str(payload["component_type"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type == REMOVE_CONTROL_COMPONENT:
            self._event_bus.publish(ControlComponentRemoved(component_id=str(payload["component_id"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type == CONNECT_CONTROL_SIGNALS:
            self._event_bus.publish(ControlConnectionCreated(source_id=str(command.payload["source_component"]), target_id=str(command.payload["target_component"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type == DISCONNECT_CONTROL_SIGNALS:
            self._event_bus.publish(ControlConnectionRemoved(source_id=str(command.payload["source_component"]), target_id=str(command.payload["target_component"]), metadata=payload, correlation_id=cid, causation_id=caid))
        elif command_type in {ADD_LADDER_RUNG, REMOVE_LADDER_RUNG, MOVE_LADDER_ELEMENT, ADD_LOGIC_DEPENDENCY, REMOVE_LOGIC_DEPENDENCY}:
            self._event_bus.publish(ControlProgramChanged(metadata={**payload, "command_type": command_type}, correlation_id=cid, causation_id=caid))

    def _publish_history_events(self, command: Command | None, result: ApplicationResult, *, operation: str) -> None:
        if command is None:
            return
        self._publish_semantic_events(command, result, operation=operation)

    def _publish_model_event(self, command: Command, metadata: dict[str, object], *, operation: str) -> None:
        parts = command.command_type.split(".", 1)
        if len(parts) != 2 or parts[0] != "model":
            return
        action = self._action_from_command_type(command.command_type)
        element_type = self._element_type(command)
        element_id = self._element_id(command)
        if element_type is None or element_id is None:
            return
        effective_action = action
        if operation == "undo":
            effective_action = {"create": "delete", "delete": "create"}.get(action, action)
        if effective_action == "create":
            self._event_bus.publish(ElementCreated(element_id=element_id, element_type=element_type, metadata=metadata))
        elif effective_action == "delete":
            self._event_bus.publish(ElementRemoved(element_id=element_id, element_type=element_type, metadata=metadata))
        elif effective_action in {"update", "open", "close", "reset", "blow", "trip", "put_in_service", "take_out_of_service"}:
            self._event_bus.publish(ElementUpdated(element_id=element_id, element_type=element_type, changes=metadata))

    def _publish_network_changed(self, command: Command, metadata: dict[str, object]) -> None:
        """Publish NetworkChanged only for commands that invalidate network state.

        The event is an aggregate network-projection invalidation. Electrical
        parameter edits remain ElementUpdated-only unless their command also
        changes connectivity/state represented by _TOPOLOGY_COMMANDS.
        Project metadata, persistence operations, and study execution never
        reach this method because they are not model commands.
        """
        if not self._is_network_change_command(command):
            return
        operation = str(metadata.get("operation", "execute"))
        if self._is_topology_command(command):
            self._event_bus.publish(TopologyChanged(operation=operation, metadata=metadata))
        self._event_bus.publish(NetworkChanged(operation=operation, metadata=metadata))

    @classmethod
    def _is_network_change_command(cls, command: Command) -> bool:
        if not command.command_type.startswith("model."):
            return False
        if cls._is_topology_command(command):
            return True
        action = cls._action_from_command_type(command.command_type)
        if action not in {"create", "delete"}:
            return False
        element_type = cls._element_type(command)
        return element_type in cls._NETWORK_ELEMENT_CREATE_DELETE_TYPES

    @staticmethod
    def _is_topology_command(command: Command) -> bool:
        if command.command_type in Application._TOPOLOGY_COMMANDS:
            return True
        if command.command_type == "model.update_breaker":
            payload = command.payload
            return payload.get("closed") is not None or payload.get("in_service") is not None
        return False

    @staticmethod
    def _action_from_command_type(command_type: str) -> str:
        action = command_type.rsplit(".", 1)[-1]
        if action.startswith("create_"):
            return "create"
        if action.startswith("delete_"):
            return "delete"
        if action.startswith("update_"):
            return "update"
        return action

    @staticmethod
    def _element_type(command: Command) -> str | None:
        payload = command.payload
        value = payload.get("element_type") or payload.get("equipment_type")
        if value is None and command.command_type.startswith("model."):
            action = command.command_type.split(".", 1)[1]
            for prefix in ("create_", "update_", "delete_", "open_", "close_", "trip_", "put_", "take_", "blow_", "reset_"):
                if action.startswith(prefix):
                    return action[len(prefix):].removesuffix("_in_service").removesuffix("_out_of_service")
        return str(value) if value is not None else None

    @staticmethod
    def _element_id(command: Command) -> str | None:
        payload = command.payload
        value = payload.get("element_id") or payload.get("equipment_id") or payload.get("id")
        if value is None:
            for key in ("breaker_id", "switch_id", "disconnector_id", "fuse_id", "line_id", "transformer_id", "cable_id"):
                if key in payload:
                    value = payload[key]
                    break
        return str(value) if value is not None else None

    def _require_read_service(self) -> None:
        if self._read_service is None:
            raise RuntimeError("Application read service is not configured.")

    def _require_protection_read_service(self) -> None:
        if self._protection_read_service is None:
            raise RuntimeError("Application protection read service is not configured.")
