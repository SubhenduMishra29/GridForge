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


def _endpoint(value):
    if value is not None and not isinstance(value, EndpointReference):
        raise TypeError("endpoint must be an EndpointReference or None.")


def _update(values, name):
    if all(value is None for value in values):
        raise ValueError(f"{name} requires at least one mutable field.")


class CreateCurrentTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, name: str = "", primary_rated_current_a: float = 100.0, secondary_rated_current_a: float = 5.0, burden_va: float | None = None, accuracy_class: str | None = None, frequency_hz: float = 50.0, polarity: str = "P1_P2", in_service: bool = True, p1_endpoint: EndpointReference | None = None, p2_endpoint: EndpointReference | None = None, s1_endpoint: EndpointReference | None = None, s2_endpoint: EndpointReference | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        for value in (p1_endpoint, p2_endpoint, s1_endpoint, s2_endpoint): _endpoint(value)
        super().__init__(command_type=CREATE_CURRENT_TRANSFORMER, payload={"transformer_id": transformer_id, "name": name, "primary_rated_current_a": primary_rated_current_a, "secondary_rated_current_a": secondary_rated_current_a, "burden_va": burden_va, "accuracy_class": accuracy_class, "frequency_hz": frequency_hz, "polarity": polarity, "in_service": in_service, "p1_endpoint": p1_endpoint, "p2_endpoint": p2_endpoint, "s1_endpoint": s1_endpoint, "s2_endpoint": s2_endpoint}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateCurrentTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, name: str | None = None, primary_rated_current_a: float | None = None, secondary_rated_current_a: float | None = None, burden_va: float | None = None, accuracy_class: str | None = None, frequency_hz: float | None = None, polarity: str | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        _update((name, primary_rated_current_a, secondary_rated_current_a, burden_va, accuracy_class, frequency_hz, polarity, in_service), "UpdateCurrentTransformerCommand")
        super().__init__(command_type=UPDATE_CURRENT_TRANSFORMER, payload={"transformer_id": transformer_id, "name": name, "primary_rated_current_a": primary_rated_current_a, "secondary_rated_current_a": secondary_rated_current_a, "burden_va": burden_va, "accuracy_class": accuracy_class, "frequency_hz": frequency_hz, "polarity": polarity, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


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
    def __init__(self, *, transformer_id: str, name: str = "", rated_primary_voltage_kv: float = 220.0, rated_secondary_voltage_v: float = 110.0, accuracy_class: str = "0.5", rated_burden_va: float = 100.0, polarity: str = "NORMAL", frequency_hz: float = 50.0, in_service: bool = True, h1_endpoint: EndpointReference | None = None, h2_endpoint: EndpointReference | None = None, x1_endpoint: EndpointReference | None = None, x2_endpoint: EndpointReference | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        for value in (h1_endpoint, h2_endpoint, x1_endpoint, x2_endpoint): _endpoint(value)
        super().__init__(command_type=CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER, payload={"transformer_id": transformer_id, "name": name, "rated_primary_voltage_kv": rated_primary_voltage_kv, "rated_secondary_voltage_v": rated_secondary_voltage_v, "accuracy_class": accuracy_class, "rated_burden_va": rated_burden_va, "polarity": polarity, "frequency_hz": frequency_hz, "in_service": in_service, "h1_endpoint": h1_endpoint, "h2_endpoint": h2_endpoint, "x1_endpoint": x1_endpoint, "x2_endpoint": x2_endpoint}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateCapacitiveVoltageTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, name: str | None = None, rated_primary_voltage_kv: float | None = None, rated_secondary_voltage_v: float | None = None, accuracy_class: str | None = None, rated_burden_va: float | None = None, polarity: str | None = None, frequency_hz: float | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        _update((name, rated_primary_voltage_kv, rated_secondary_voltage_v, accuracy_class, rated_burden_va, polarity, frequency_hz, in_service), "UpdateCapacitiveVoltageTransformerCommand")
        super().__init__(command_type=UPDATE_CAPACITIVE_VOLTAGE_TRANSFORMER, payload={"transformer_id": transformer_id, "name": name, "rated_primary_voltage_kv": rated_primary_voltage_kv, "rated_secondary_voltage_v": rated_secondary_voltage_v, "accuracy_class": accuracy_class, "rated_burden_va": rated_burden_va, "polarity": polarity, "frequency_hz": frequency_hz, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteCapacitiveVoltageTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class PutCapacitiveVoltageTransformerInServiceCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class TakeCapacitiveVoltageTransformerOutOfServiceCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None):
        super().__init__(command_type=TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE, payload={"transformer_id": transformer_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = [
    "CREATE_CURRENT_TRANSFORMER", "UPDATE_CURRENT_TRANSFORMER", "DELETE_CURRENT_TRANSFORMER",
    "PUT_CURRENT_TRANSFORMER_IN_SERVICE", "TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE",
    "CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER", "UPDATE_CAPACITIVE_VOLTAGE_TRANSFORMER",
    "DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER", "PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE",
    "TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE",
    "CreateCurrentTransformerCommand", "UpdateCurrentTransformerCommand", "DeleteCurrentTransformerCommand",
    "PutCurrentTransformerInServiceCommand", "TakeCurrentTransformerOutOfServiceCommand",
    "CreateCapacitiveVoltageTransformerCommand", "UpdateCapacitiveVoltageTransformerCommand",
    "DeleteCapacitiveVoltageTransformerCommand", "PutCapacitiveVoltageTransformerInServiceCommand",
    "TakeCapacitiveVoltageTransformerOutOfServiceCommand",
]
