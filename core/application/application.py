# ============================================================
# File: core/application/application.py
# GridForge V2 — Headless Application Facade
# ============================================================

"""Stable public Application facade for commands, reads, events, and history."""

from __future__ import annotations

from .command import Command
from .command_manager import CommandManager
from .event_bus import ApplicationEventBus
from .events import (
    ElementCreated,
    ElementRemoved,
    ElementUpdated,
    NetworkChanged,
    TopologyChanged,
)
from .read_models import ElementReadModel, NetworkReadModel
from .read_service import ReadService
from .results import ApplicationResult


class Application:
    """Public headless GridForge Application facade."""

    _TOPOLOGY_COMMANDS = frozenset({
        "model.create_line", "model.delete_line",
        "model.create_transformer", "model.delete_transformer",
        "model.create_branch", "model.update_branch", "model.delete_branch",
        "model.create_cable", "model.update_cable", "model.delete_cable",
        "model.create_switch", "model.update_switch", "model.delete_switch",
        "model.open_switch", "model.close_switch",
        "model.put_switch_in_service", "model.take_switch_out_of_service",
        "model.create_disconnector", "model.update_disconnector", "model.delete_disconnector",
        "model.open_disconnector", "model.close_disconnector",
        "model.put_disconnector_in_service", "model.take_disconnector_out_of_service",
        "model.create_fuse", "model.update_fuse", "model.delete_fuse",
        "model.blow_fuse", "model.reset_fuse",
        "model.put_fuse_in_service", "model.take_fuse_out_of_service",
    })

    def __init__(self, command_manager: CommandManager, read_service: ReadService | None = None,
                 event_bus: ApplicationEventBus | None = None) -> None:
        if not isinstance(command_manager, CommandManager):
            raise TypeError("Application command_manager must be a CommandManager.")
        if read_service is not None and not isinstance(read_service, ReadService):
            raise TypeError("Application read_service must implement ReadService.")
        if event_bus is not None and not isinstance(event_bus, ApplicationEventBus):
            raise TypeError("Application event_bus must be an ApplicationEventBus.")
        self._command_manager = command_manager
        self._read_service = read_service
        self._event_bus = event_bus if event_bus is not None else ApplicationEventBus()

    @property
    def event_bus(self) -> ApplicationEventBus:
        return self._event_bus

    def execute(self, command: Command) -> ApplicationResult:
        """Execute a command and publish semantic events only after success/commit."""
        if not isinstance(command, Command):
            raise TypeError("Application.execute requires a Command.")
        result = self._command_manager.execute(command)
        if result.success:
            self._publish_semantic_events(command, result, operation="execute")
        return result

    def supports(self, command_type: str) -> bool:
        if not isinstance(command_type, str):
            return False
        return self._command_manager.is_registered(command_type)

    def command_types(self) -> tuple[str, ...]:
        return self._command_manager.registered_commands

    def undo(self) -> ApplicationResult | None:
        """Undo and publish the semantic inverse of the original command."""
        records = self._command_manager.undo_commands()
        command = records[-1].command if records else None
        result = self._command_manager.undo()
        if result is not None and result.success:
            self._publish_history_events(command, result, operation="undo")
        return result

    def redo(self) -> ApplicationResult | None:
        """Redo and publish semantic events for the re-executed command."""
        records = self._command_manager.redo_commands()
        command = records[-1].command if records else None
        result = self._command_manager.redo()
        if result is not None and result.success and command is not None:
            self._publish_semantic_events(command, result, operation="redo")
        return result

    def can_undo(self) -> bool:
        return self._command_manager.can_undo()

    def can_redo(self) -> bool:
        return self._command_manager.can_redo()

    def undo_count(self) -> int:
        return self._command_manager.undo_count()

    def redo_count(self) -> int:
        return self._command_manager.redo_count()

    def undo_commands(self) -> tuple:
        return self._command_manager.undo_commands()

    def redo_commands(self) -> tuple:
        return self._command_manager.redo_commands()

    def clear_history(self) -> None:
        self._command_manager.clear_history()

    def read_network(self) -> NetworkReadModel:
        self._require_read_service()
        return self._read_service.network()  # type: ignore[union-attr]

    def read_element(self, element_type: str, object_id: str) -> ElementReadModel:
        self._require_read_service()
        return self._read_service.element(element_type, object_id)  # type: ignore[union-attr]

    def _publish_semantic_events(self, command: Command, result: ApplicationResult, *, operation: str) -> None:
        metadata = {
            "command_id": str(command.command_id),
            "message": result.message,
            "operation": operation,
        }
        self._publish_model_event(command, metadata, operation=operation)
        self._publish_network_changed(command, metadata)

    def _publish_history_events(self, command: Command | None, result: ApplicationResult, *, operation: str) -> None:
        if command is None:
            self._publish_network_only_result(result, operation=operation)
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
            self._event_bus.publish(ElementCreated(
                element_id=element_id, element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id, metadata=metadata,
            ))
        elif effective_action == "delete":
            self._event_bus.publish(ElementRemoved(
                element_id=element_id, element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id, metadata=metadata,
            ))
        elif effective_action in {"update", "open", "close", "put", "take", "blow", "reset"}:
            changes = {
                key: value for key, value in command.payload.items()
                if key != self._id_key(command) and value is not None
            }
            self._event_bus.publish(ElementUpdated(
                element_id=element_id, element_type=element_type,
                changes=changes, correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            ))

        if command.command_type in self._TOPOLOGY_COMMANDS:
            self._event_bus.publish(TopologyChanged(
                operation=command.command_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id, metadata=metadata,
            ))

    def _publish_network_changed(self, command: Command, metadata: dict[str, object]) -> None:
        self._event_bus.publish(NetworkChanged(
            operation=command.command_type,
            correlation_id=command.correlation_id,
            causation_id=command.causation_id,
            metadata=metadata,
        ))

    def _publish_network_only_result(self, result: ApplicationResult, *, operation: str) -> None:
        metadata = dict(result.metadata)
        metadata["operation"] = operation
        self._event_bus.publish(NetworkChanged(
            operation=str(metadata.get("command_type", operation)),
            metadata=metadata,
        ))

    @staticmethod
    def _action_from_command_type(command_type: str) -> str:
        operation_name = command_type.split(".", 1)[-1]
        return operation_name.split("_", 1)[0] if "_" in operation_name else operation_name

    @staticmethod
    def _element_type(command: Command) -> str | None:
        operation_name = command.command_type.split(".", 1)[-1]
        for prefix in ("create_", "update_", "delete_", "open_", "close_", "put_", "take_", "blow_", "reset_"):
            if operation_name.startswith(prefix):
                return operation_name[len(prefix):]
        return None

    @staticmethod
    def _id_key(command: Command) -> str | None:
        candidates = [
            key for key in command.payload
            if key.endswith("_id") and key not in {"command_id", "correlation_id", "causation_id"}
        ]
        return candidates[0] if candidates else None

    @staticmethod
    def _element_id(command: Command) -> str | None:
        key = Application._id_key(command)
        value = command.payload.get(key) if key else None
        return value if isinstance(value, str) and value else None

    def _require_read_service(self) -> None:
        if self._read_service is None:
            raise RuntimeError("Application read service is not configured.")


__all__ = ["Application"]
