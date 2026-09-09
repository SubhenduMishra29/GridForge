"""Immutable Application commands for CT/CVT lifecycle operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_CURRENT_TRANSFORMER = "model.create_current_transformer"
UPDATE_CURRENT_TRANSFORMER = "model.update_current_transformer"
DELETE_CURRENT_TRANSFORMER = "model.delete_current_transformer"
PUT_CURRENT_TRANSFORMER_IN_SERVICE = "model.put_current_transformer_in_service"
TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE = "model.take_current_transformer_out_of_service"
CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER = "model.create_capacitive_voltage_transformer"
UPDATE_CAPACITIVE_VOLTAGE_TRANSFORMER = "model.update_capacitive_voltage_transformer"
DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER = "model.delete_capacitive_voltage_transformer"
PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE = "model.put_capacitive_voltage_transformer_in_service"
TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE = "model.take_capacitive_voltage_transformer_out_of_service"


def _validate_endpoint(endpoint):
    if endpoint is not None and not isinstance(endpoint, EndpointReference):
        raise TypeError("endpoint must be an EndpointReference or None.")


def _validate_update(values, name):
    if all(value is None for value in values):
        raise ValueError(f"{name} requires at least one mutable field.")


class CreateCurrentTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, endpoint: EndpointReference | None = None, name: str = "", ratio: float = 1.0, accuracy_class: str | None = None, in_service: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        _validate_endpoint(endpoint)
        super().__init__(command_type=CREATE_CURRENT_TRANSFORMER, payload=locals_payload(locals(), "transformer_id", "endpoint", "name", "ratio", "accuracy_class", "in_service"), command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateCurrentTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, endpoint: EndpointReference | None = None, name: str | None = None, ratio: float | None = None, accuracy_class: str | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        _validate_endpoint(endpoint)
        _validate_update((endpoint, name, ratio, accuracy_class, in_service), "UpdateCurrentTransformerCommand")
        super().__init__(command_type=UPDATE_CURRENT_TRANSFORMER, payload=locals_payload(locals(), "transformer_id", "endpoint", "name", "ratio", "accuracy_class", "in_service"), command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteCurrentTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=DELETE_CURRENT_TRANSFORMER, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class PutCurrentTransformerInServiceCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=PUT_CURRENT_TRANSFORMER_IN_SERVICE, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class TakeCurrentTransformerOutOfServiceCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class CreateCapacitiveVoltageTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, endpoint: EndpointReference | None = None, name: str = "", ratio: float = 1.0, accuracy_class: str | None = None, in_service: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        _validate_endpoint(endpoint)
        super().__init__(command_type=CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER, payload=locals_payload(locals(), "transformer_id", "endpoint", "name", "ratio", "accuracy_class", "in_service"), command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateCapacitiveVoltageTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, endpoint: EndpointReference | None = None, name: str | None = None, ratio: float | None = None, accuracy_class: str | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        _validate_endpoint(endpoint)
        _validate_update((endpoint, name, ratio, accuracy_class, in_service), "UpdateCapacitiveVoltageTransformerCommand")
        super().__init__(command_type=UPDATE_CAPACITIVE_VOLTAGE_TRANSFORMER, payload=locals_payload(locals(), "transformer_id", "endpoint", "name", "ratio", "accuracy_class", "in_service"), command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteCapacitiveVoltageTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class PutCapacitiveVoltageTransformerInServiceCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class TakeCapacitiveVoltageTransformerOutOfServiceCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


def locals_payload(values, *keys):
    return {key: values[key] for key in keys}
