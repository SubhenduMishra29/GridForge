"""Immutable Application commands for Capacitor lifecycle operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_CAPACITOR = "model.create_capacitor"
UPDATE_CAPACITOR = "model.update_capacitor"
DELETE_CAPACITOR = "model.delete_capacitor"
PUT_CAPACITOR_IN_SERVICE = "model.put_capacitor_in_service"
TAKE_CAPACITOR_OUT_OF_SERVICE = "model.take_capacitor_out_of_service"


class CreateCapacitorCommand(Command):
    def __init__(self, *, capacitor_id: str, name: str = "", endpoint: EndpointReference | None = None, reactive_power_injection_mvar: float = 0.0, in_service: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if endpoint is not None and not isinstance(endpoint, EndpointReference):
            raise TypeError("endpoint must be an EndpointReference or None.")
        super().__init__(command_type=CREATE_CAPACITOR, payload={"capacitor_id": capacitor_id, "name": name, "endpoint": endpoint, "reactive_power_injection_mvar": reactive_power_injection_mvar, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateCapacitorCommand(Command):
    def __init__(self, *, capacitor_id: str, name: str | None = None, endpoint: EndpointReference | None = None, reactive_power_injection_mvar: float | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if endpoint is not None and not isinstance(endpoint, EndpointReference):
            raise TypeError("endpoint must be an EndpointReference or None.")
        if all(value is None for value in (name, endpoint, reactive_power_injection_mvar, in_service)):
            raise ValueError("UpdateCapacitorCommand requires at least one mutable Capacitor field.")
        super().__init__(command_type=UPDATE_CAPACITOR, payload={"capacitor_id": capacitor_id, "name": name, "endpoint": endpoint, "reactive_power_injection_mvar": reactive_power_injection_mvar, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteCapacitorCommand(Command):
    def __init__(self, *, capacitor_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=DELETE_CAPACITOR, payload={"capacitor_id": capacitor_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class PutCapacitorInServiceCommand(Command):
    def __init__(self, *, capacitor_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=PUT_CAPACITOR_IN_SERVICE, payload={"capacitor_id": capacitor_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class TakeCapacitorOutOfServiceCommand(Command):
    def __init__(self, *, capacitor_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=TAKE_CAPACITOR_OUT_OF_SERVICE, payload={"capacitor_id": capacitor_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = ["CREATE_CAPACITOR", "UPDATE_CAPACITOR", "DELETE_CAPACITOR", "PUT_CAPACITOR_IN_SERVICE", "TAKE_CAPACITOR_OUT_OF_SERVICE", "CreateCapacitorCommand", "UpdateCapacitorCommand", "DeleteCapacitorCommand", "PutCapacitorInServiceCommand", "TakeCapacitorOutOfServiceCommand"]
