"""Immutable Application commands for SynchronousMachine mutations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_SYNCHRONOUS_MACHINE = "model.create_synchronous_machine"
UPDATE_SYNCHRONOUS_MACHINE = "model.update_synchronous_machine"
DELETE_SYNCHRONOUS_MACHINE = "model.delete_synchronous_machine"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


def _endpoint(value: EndpointReference | None, name: str) -> None:
    if value is not None and not isinstance(value, EndpointReference):
        raise TypeError(f"{name} must be an EndpointReference or None.")


class CreateSynchronousMachineCommand(Command):
    def __init__(self, *, synchronous_machine_id: str, endpoint: EndpointReference | None = None,
                 name: str = "", active_power_injection_mw: float = 0.0,
                 reactive_power_injection_mvar: float = 0.0, rated_power_mva: float | None = None,
                 rated_voltage_kv: float | None = None, frequency_hz: float = 50.0,
                 in_service: bool = True, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint, "endpoint")
        super().__init__(**_command(
            CREATE_SYNCHRONOUS_MACHINE,
            {"synchronous_machine_id": synchronous_machine_id, "endpoint": endpoint, "name": name,
             "active_power_injection_mw": active_power_injection_mw,
             "reactive_power_injection_mvar": reactive_power_injection_mvar,
             "rated_power_mva": rated_power_mva, "rated_voltage_kv": rated_voltage_kv,
             "frequency_hz": frequency_hz, "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class UpdateSynchronousMachineCommand(Command):
    def __init__(self, *, synchronous_machine_id: str, name: str | None = None,
                 active_power_injection_mw: float | None = None,
                 reactive_power_injection_mvar: float | None = None, rated_power_mva: float | None = None,
                 rated_voltage_kv: float | None = None, frequency_hz: float | None = None,
                 in_service: bool | None = None, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        values = (name, active_power_injection_mw, reactive_power_injection_mvar,
                  rated_power_mva, rated_voltage_kv, frequency_hz, in_service)
        if all(value is None for value in values):
            raise ValueError("UpdateSynchronousMachineCommand requires at least one mutable field.")
        super().__init__(**_command(
            UPDATE_SYNCHRONOUS_MACHINE,
            {"synchronous_machine_id": synchronous_machine_id, "name": name,
             "active_power_injection_mw": active_power_injection_mw,
             "reactive_power_injection_mvar": reactive_power_injection_mvar,
             "rated_power_mva": rated_power_mva, "rated_voltage_kv": rated_voltage_kv,
             "frequency_hz": frequency_hz, "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class DeleteSynchronousMachineCommand(Command):
    def __init__(self, *, synchronous_machine_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(
            DELETE_SYNCHRONOUS_MACHINE,
            {"synchronous_machine_id": synchronous_machine_id},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


__all__ = [
    "CREATE_SYNCHRONOUS_MACHINE", "UPDATE_SYNCHRONOUS_MACHINE", "DELETE_SYNCHRONOUS_MACHINE",
    "CreateSynchronousMachineCommand", "UpdateSynchronousMachineCommand", "DeleteSynchronousMachineCommand",
]
