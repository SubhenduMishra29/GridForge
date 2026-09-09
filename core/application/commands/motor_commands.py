"""Immutable Application commands for Motor mutations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_MOTOR = "model.create_motor"
UPDATE_MOTOR = "model.update_motor"
DELETE_MOTOR = "model.delete_motor"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


def _endpoint(value: EndpointReference | None, name: str) -> None:
    if value is not None and not isinstance(value, EndpointReference):
        raise TypeError(f"{name} must be an EndpointReference or None.")


class CreateMotorCommand(Command):
    def __init__(self, *, motor_id: str, endpoint: EndpointReference | None = None,
                 rated_mva: float = 1.0, rated_kv: float = 1.0, power_factor: float = 0.9,
                 p: float = 0.0, q: float = 0.0, efficiency: float = 1.0,
                 slip: float = 0.0, starting_current_pu: float = 0.0, running: bool = False,
                 in_service: bool = True, name: str = "", command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint, "endpoint")
        super().__init__(**_command(
            CREATE_MOTOR,
            {"motor_id": motor_id, "endpoint": endpoint, "rated_mva": rated_mva, "rated_kv": rated_kv,
             "power_factor": power_factor, "p": p, "q": q, "efficiency": efficiency, "slip": slip,
             "starting_current_pu": starting_current_pu, "running": running, "in_service": in_service,
             "name": name},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class UpdateMotorCommand(Command):
    def __init__(self, *, motor_id: str, rated_mva: float | None = None, rated_kv: float | None = None,
                 power_factor: float | None = None, p: float | None = None, q: float | None = None,
                 efficiency: float | None = None, slip: float | None = None,
                 starting_current_pu: float | None = None, running: bool | None = None,
                 in_service: bool | None = None, name: str | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        values = (rated_mva, rated_kv, power_factor, p, q, efficiency, slip,
                  starting_current_pu, running, in_service, name)
        if all(value is None for value in values):
            raise ValueError("UpdateMotorCommand requires at least one mutable field.")
        super().__init__(**_command(
            UPDATE_MOTOR,
            {"motor_id": motor_id, "rated_mva": rated_mva, "rated_kv": rated_kv,
             "power_factor": power_factor, "p": p, "q": q, "efficiency": efficiency,
             "slip": slip, "starting_current_pu": starting_current_pu, "running": running,
             "in_service": in_service, "name": name},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class DeleteMotorCommand(Command):
    def __init__(self, *, motor_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(
            DELETE_MOTOR,
            {"motor_id": motor_id},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


__all__ = ["CREATE_MOTOR", "UPDATE_MOTOR", "DELETE_MOTOR", "CreateMotorCommand", "UpdateMotorCommand", "DeleteMotorCommand"]
