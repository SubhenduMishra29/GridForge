"""Immutable Application commands for the physical Relay lifecycle."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID, uuid4

from ..command import Command

CREATE_RELAY = "model.create_relay"
UPDATE_RELAY = "model.update_relay"
DELETE_RELAY = "model.delete_relay"
PUT_RELAY_IN_SERVICE = "model.put_relay_in_service"
TAKE_RELAY_OUT_OF_SERVICE = "model.take_relay_out_of_service"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


class CreateRelayCommand(Command):
    def __init__(self, *, relay_id: str, relay_type: str, name: str = "",
                 plugin_id: str | None = None, settings: Mapping[str, Any] | None = None,
                 in_service: bool = True, enabled: bool = True, blocked: bool = False,
                 presentation_x: float | None = None, presentation_y: float | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(**_command(CREATE_RELAY, {"presentation_x": presentation_x, "presentation_y": presentation_y, 
            "relay_id": relay_id, "element_id": relay_id, "relay_type": relay_type, "name": name,
            "plugin_id": plugin_id, "settings": dict(settings or {}),
            "in_service": in_service, "enabled": enabled, "blocked": blocked,
        }, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class UpdateRelayCommand(Command):
    def __init__(self, *, relay_id: str, name: str | None = None,
                 plugin_id: str | None = None, settings: Mapping[str, Any] | None = None,
                 enabled: bool | None = None, blocked: bool | None = None,
                 in_service: bool | None = None, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(value is None for value in (name, plugin_id, settings, enabled, blocked, in_service)):
            raise ValueError("UpdateRelayCommand requires at least one mutable Relay field.")
        super().__init__(**_command(UPDATE_RELAY, {
            "relay_id": relay_id, "element_id": relay_id, "name": name, "plugin_id": plugin_id,
            "settings": dict(settings) if settings is not None else None,
            "enabled": enabled, "blocked": blocked, "in_service": in_service,
        }, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class DeleteRelayCommand(Command):
    def __init__(self, *, relay_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_RELAY, {"relay_id": relay_id, "element_id": relay_id},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class PutRelayInServiceCommand(Command):
    def __init__(self, *, relay_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(PUT_RELAY_IN_SERVICE, {"relay_id": relay_id, "element_id": relay_id},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class TakeRelayOutOfServiceCommand(Command):
    def __init__(self, *, relay_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(TAKE_RELAY_OUT_OF_SERVICE, {"relay_id": relay_id, "element_id": relay_id},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


__all__ = [
    "CREATE_RELAY", "UPDATE_RELAY", "DELETE_RELAY",
    "PUT_RELAY_IN_SERVICE", "TAKE_RELAY_OUT_OF_SERVICE",
    "CreateRelayCommand", "UpdateRelayCommand", "DeleteRelayCommand",
    "PutRelayInServiceCommand", "TakeRelayOutOfServiceCommand",
]
