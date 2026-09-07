# ============================================================
# File: core/application/application.py
# GridForge V2 — Headless Application Facade
# Author: Subhendu Mishra
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
    """Public headless GridForge Application facade.

    Mutation remains exclusively command-driven. Optional read access exposes
    immutable Application snapshots and never returns Core model objects.
    Command history remains owned by the Application command manager; these
    methods expose that state only through this canonical Application boundary.
    """

    _TOPOLOGY_COMMANDS = frozenset({
        "model.create_line",
        "model.delete_line",
        "model.create_transformer",
        "model.delete_transformer",
        "model.create_branch",
        "model.update_branch",
        "model.delete_branch",
        "model.create_cable",
        "model.update_cable",
        "model.delete_cable",
        "model.create_switch",
        "model.update_switch",
        "model.delete_switch",
        "model.open_switch",
        "model.close_switch",
        "model.put_switch_in_service",
        "model.take_switch_out_of_service",
        "model.create_disconnector",
        "model.update_disconnector",
        "model.delete_disconnector",
        "model.open_disconnector",
        "model.close_disconnector",
        "model.put_disconnector_in_service",
        "model.take_disconnector_out_of_service",
        "model.create_fuse",
        "model.update_fuse",
        "model.delete_fuse",
        "model.blow_fuse",
        "model.reset_fuse",
        "model.put_fuse_in_service",
        "model.take_fuse_out_of_service",
    })

    def __init__(
        self,
        command_manager: CommandManager,
        read_service: ReadService | None = None,
        event_bus: ApplicationEventBus | None = None,
    ) -> None:
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
        """Return the Application-owned headless event bus."""
        return self._event_bus

    def execute(self, command: Command) -> ApplicationResult:
        """Execute a command, then publish committed semantic events."""
        if not isinstance(command, Command):
            raise TypeError("Application.execute requires a Command.")
        result = self._command_manager.execute(command)
        self._publish_semantic_events(command, result, operation="execute")
        return result

    def supports(self, command_type: str) -> bool:
        """Return whether a command type is currently supported."""
        if not isinstance(command_type, str):
            return False
        return self._command_manager.is_registered(command_type)

    def command_types(self) -> tuple[str, ...]:
        """Return the immutable list of registered command types."""
        return self._command_manager.registered_commands

    def undo(self) -> ApplicationResult | None:
        """Undo through the canonical Application command manager."""
        result = self._command_manager.undo()
        if result is not None and result.success:
            self._publish_history_event(result, operation="undo")
        return result

    def redo(self) -> ApplicationResult | None:
        """Redo through the canonical Application command manager."""
        result = self._command_manager.redo()
        if result is not None and result.success:
            command_id = result.get_metadata("command_id")
            if command_id:
                self._publish_semantic_events_from_metadata(
                    result.metadata,
                    operation="redo",
                )
            else:
                self._publish_network_only_result(result, operation="redo")
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

    def read_element(
        self,
        element_type: str,
        object_id: str,
    ) -> ElementReadModel:
        self._require_read_service()
        return self._read_service.element(element_type, object_id)  # type: ignore[union-attr]

    def _publish_semantic_events(
        self,
        command: Command,
        result: ApplicationResult,
        *,
        operation: str,
    ) -> None:
        metadata = {
            "command_id": str(command.command_id),
            "message": result.message,
            "operation": operation,
        }
        self._publish_model_event(command, metadata)
        self._event_bus.publish(
            NetworkChanged(
                operation=command.command_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                metadata=metadata,
            )
        )

    def _publish_model_event(
        self,
        command: Command,
        metadata: dict[str, object],
    ) -> None:
        parts = command.command_type.split(".", 1)
        if len(parts) != 2 or parts[0] != "model":
            return
        action, _ = parts[1].split("_", 1) if "_" in parts[1] else (parts[1], "")
        element_type = self._element_type(command)
        element_id = self._element_id(command)
        if element_type is None or element_id is None:
            return

        if action == "create":
            self._event_bus.publish(ElementCreated(
                element_id=element_id,
                element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                metadata=metadata,
            ))
        elif action == "delete":
            self._event_bus.publish(ElementRemoved(
                element_id=element_id,
                element_type=element_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                metadata=metadata,
            ))
        elif action == "update" or action in {"open", "close", "put", "take", "blow", "reset"}:
            changes = {
                key: value
                for key, value in command.payload.items()
                if key != self._id_key(command)
                and value is not None
            }
            self._event_bus.publish(ElementUpdated(
                element_id=element_id,
                element_type=element_type,
                changes=changes,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
            ))

        if command.command_type in self._TOPOLOGY_COMMANDS:
            self._event_bus.publish(TopologyChanged(
                operation=command.command_type,
                correlation_id=command.correlation_id,
                causation_id=command.causation_id,
                metadata=metadata,
            ))

    @staticmethod
    def _element_id(command: Command) -> str | None:
        key = Application._id_key(command)
        value = command.payload.get(key) if key else None
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _id_key(command: Command) -> str | None:
        candidates = [
            key for key in command.payload
            if key.endswith("_id") and key not in {"command_id", "correlation_id", "causation_id"}
        ]
        return candidates[0] if candidates else None

    @staticmethod
    def _element_type(command: Command) -> str | None:
        parts = command.command_type.split(".", 1)
        if len(parts) != 2:
            return None
        operation_name = parts[1]
        for prefix in ("create_", "update_", "delete_", "open_", "close_", "put_", "take_", "blow_", "reset_"):
            if operation_name.startswith(prefix):
                return operation_name[len(prefix):]
        return None

    def _publish_history_event(
        self,
        result: ApplicationResult,
        *,
        operation: str,
    ) -> None:
        command_type = result.get_metadata("command_type")
        metadata = dict(result.metadata)
        metadata["operation"] = operation
        if not isinstance(command_type, str):
            self._publish_network_only_result(result, operation=operation)
            return
        self._publish_semantic_events_from_metadata(metadata, operation=operation)

    def _publish_semantic_events_from_metadata(
        self,
        metadata: dict[str, object] | object,
        *,
        operation: str,
    ) -> None:
        data = dict(metadata) if hasattr(metadata, "items") else {}
        command_type = data.get("command_type")
        command_id = data.get("command_id")
        if not isinstance(command_type, str):
            self._publish_network_only_result(data, operation=operation)
            return
        payload = {
            "command_id": command_id,
            "operation": operation,
        }
        element_type = self._element_type_from_command_type(command_type)
        element_id = data.get("element_id")
        if isinstance(element_type, str) and isinstance(element_id, str):
            action = self._action_from_command_type(command_type)
            if action == "create":
                self._event_bus.publish(ElementCreated(element_id=element_id, element_type=element_type, metadata=payload))
            elif action == "delete":
                self._event_bus.publish(ElementRemoved(element_id=element_id, element_type=element_type, metadata=payload))
            elif action == "update":
                self._event_bus.publish(ElementUpdated(element_id=element_id, element_type=element_type, metadata=payload))
            if command_type in self._TOPOLOGY_COMMANDS:
                self._event_bus.publish(TopologyChanged(operation=command_type, metadata=payload))
        self._publish_network_only_result(data, operation=operation)

    @staticmethod
    def _action_from_command_type(command_type: str) -> str | None:
        operation_name = command_type.split(".", 1)[-1]
        return operation_name.split("_", 1)[0] if "_" in operation_name else operation_name

    @staticmethod
    def _element_type_from_command_type(command_type: str) -> str | None:
        operation_name = command_type.split(".", 1)[-1]
        for prefix in ("create_", "update_", "delete_"):
            if operation_name.startswith(prefix):
                return operation_name[len(prefix):]
        return None

    def _publish_network_only_result(self, metadata: object, *, operation: str) -> None:
        data = dict(metadata) if hasattr(metadata, "items") else {}
        command_type = data.get("command_type", operation)
        self._event_bus.publish(NetworkChanged(
            operation=str(command_type),
            metadata={**data, "operation": operation},
        ))

    def _require_read_service(self) -> None:
        if self._read_service is None:
            raise RuntimeError("Application read service is not configured.")


__all__ = ["Application"]
