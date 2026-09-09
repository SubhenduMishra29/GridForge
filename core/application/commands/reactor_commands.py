"""Immutable Application commands for Reactor mutations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_REACTOR = "model.create_reactor"
UPDATE_REACTOR = "model.update_reactor"
DELETE_REACTOR = "model.delete_reactor"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


def _endpoint(value: EndpointReference | None, name: str) -> None:
    if value is not None and not isinstance(value, EndpointReference):
        raise TypeError(f"{name} must be an EndpointReference or None.")


class CreateReactorCommand(Command):
    def __init__(self, *, reactor_id: str, endpoint: EndpointReference | None = None,
                 name: str = "", reactive_power_injection_mvar: float = -10.0,
                 in_service: bool = True, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint, "endpoint")
        super().__init__(**_command(
            CREATE_REACTOR,
            {"reactor_id": reactor_id, "endpoint": endpoint, "name": name,
             "reactive_power_injection_mvar": reactive_power_injection_mvar,
             "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class UpdateReactorCommand(Command):
    def __init__(self, *, reactor_id: str, name: str | None = None,
                 reactive_power_injection_mvar: float | None = None,
                 in_service: bool | None = None, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(value is None for value in (name, reactive_power_injection_mvar, in_service)):
            raise ValueError("UpdateReactorCommand requires at least one mutable field.")
        super().__init__(**_command(
            UPDATE_REACTOR,
            {"reactor_id": reactor_id, "name": name,
             "reactive_power_injection_mvar": reactive_power_injection_mvar,
             "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class DeleteReactorCommand(Command):
    def __init__(self, *, reactor_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(
            DELETE_REACTOR,
            {"reactor_id": reactor_id},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


__all__ = [
    "CREATE_REACTOR", "UPDATE_REACTOR", "DELETE_REACTOR",
    "CreateReactorCommand", "UpdateReactorCommand", "DeleteReactorCommand",
]
