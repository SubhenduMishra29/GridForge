"""Immutable Application commands for CT/CVT lifecycle operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command

CREATE_CT = "model.create_current_transformer"
UPDATE_CT = "model.update_current_transformer"
DELETE_CT = "model.delete_current_transformer"
PUT_CT_IN_SERVICE = "model.put_current_transformer_in_service"
TAKE_CT_OUT_OF_SERVICE = "model.take_current_transformer_out_of_service"
CREATE_CVT = "model.create_capacitive_voltage_transformer"
UPDATE_CVT = "model.update_capacitive_voltage_transformer"
DELETE_CVT = "model.delete_capacitive_voltage_transformer"
PUT_CVT_IN_SERVICE = "model.put_capacitive_voltage_transformer_in_service"
TAKE_CVT_OUT_OF_SERVICE = "model.take_capacitive_voltage_transformer_out_of_service"


class _MeasurementCommand(Command):
    def __init__(self, *, command_type: str, payload: dict, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=command_type, payload=payload, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class CreateCurrentTransformerCommand(_MeasurementCommand):
    def __init__(self, *, ct_id: str, name: str = "", primary_rated_current_a: float = 100.0, secondary_rated_current_a: float = 5.0, burden_va: float | None = None, accuracy_class: str | None = None, frequency_hz: float = 50.0, polarity: str = "P1_P2", in_service: bool = True, p1_endpoint=None, p2_endpoint=None, s1_endpoint=None, s2_endpoint=None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _validate_refs(p1_endpoint, p2_endpoint, s1_endpoint, s2_endpoint)
        super().__init__(command_type=CREATE_CT, payload=locals_payload(locals(), "ct_id", "name", "primary_rated_current_a", "secondary_rated_current_a", "burden_va", "accuracy_class", "frequency_hz", "polarity", "in_service", "p1_endpoint", "p2_endpoint", "s1_endpoint", "s2_endpoint"), command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class UpdateCurrentTransformerCommand(_MeasurementCommand):
    def __init__(self, *, ct_id: str, name=None, primary_rated_current_a=None, secondary_rated_current_a=None, burden_va=None, accuracy_class=None, frequency_hz=None, polarity=None, in_service=None, command_id=None, correlation_id=None, causation_id=None) -> None:
        if all(value is None for value in (name, primary_rated_current_a, secondary_rated_current_a, burden_va, accuracy_class, frequency_hz, polarity, in_service)):
            raise ValueError("UpdateCurrentTransformerCommand requires at least one mutable field.")
        super().__init__(command_type=UPDATE_CT, payload=locals_payload(locals(), "ct_id", "name", "primary_rated_current_a", "secondary_rated_current_a", "burden_va", "accuracy_class", "frequency_hz", "polarity", "in_service"), command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteCurrentTransformerCommand(_MeasurementCommand):
    def __init__(self, *, ct_id: str, command_id=None, correlation_id=None, causation_id=None) -> None:
        super().__init__(command_type=DELETE_CT, payload={"ct_id": ct_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class PutCurrentTransformerInServiceCommand(_MeasurementCommand):
    def __init__(self, *, ct_id: str, command_id=None, correlation_id=None, causation_id=None) -> None:
        super().__init__(command_type=PUT_CT_IN_SERVICE, payload={"ct_id": ct_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class TakeCurrentTransformerOutOfServiceCommand(_MeasurementCommand):
    def __init__(self, *, ct_id: str, command_id=None, correlation_id=None, causation_id=None) -> None:
        super().__init__(command_type=TAKE_CT_OUT_OF_SERVICE, payload={"ct_id": ct_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class CreateCapacitiveVoltageTransformerCommand(_MeasurementCommand):
    def __init__(self, *, cvt_id: str, name: str = "", rated_primary_voltage_kv: float = 220.0, rated_secondary_voltage_v: float = 110.0, accuracy_class: str = "0.5", rated_burden_va: float = 100.0, polarity: str = "NORMAL", frequency_hz: float = 50.0, in_service: bool = True, h1_endpoint=None, h2_endpoint=None, x1_endpoint=None, x2_endpoint=None, command_id=None, correlation_id=None, causation_id=None) -> None:
        _validate_refs(h1_endpoint, h2_endpoint, x1_endpoint, x2_endpoint)
        super().__init__(command_type=CREATE_CVT, payload=locals_payload(locals(), "cvt_id", "name", "rated_primary_voltage_kv", "rated_secondary_voltage_v", "accuracy_class", "rated_burden_va", "polarity", "frequency_hz", "in_service", "h1_endpoint", "h2_endpoint", "x1_endpoint", "x2_endpoint"), command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class UpdateCapacitiveVoltageTransformerCommand(_MeasurementCommand):
    def __init__(self, *, cvt_id: str, name=None, rated_primary_voltage_kv=None, rated_secondary_voltage_v=None, accuracy_class=None, rated_burden_va=None, polarity=None, frequency_hz=None, in_service=None, command_id=None, correlation_id=None, causation_id=None) -> None:
        if all(value is None for value in (name, rated_primary_voltage_kv, rated_secondary_voltage_v, accuracy_class, rated_burden_va, polarity, frequency_hz, in_service)):
            raise ValueError("UpdateCapacitiveVoltageTransformerCommand requires at least one mutable field.")
        super().__init__(command_type=UPDATE_CVT, payload=locals_payload(locals(), "cvt_id", "name", "rated_primary_voltage_kv", "rated_secondary_voltage_v", "accuracy_class", "rated_burden_va", "polarity", "frequency_hz", "in_service"), command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteCapacitiveVoltageTransformerCommand(_MeasurementCommand):
    def __init__(self, *, cvt_id: str, command_id=None, correlation_id=None, causation_id=None) -> None:
        super().__init__(command_type=DELETE_CVT, payload={"cvt_id": cvt_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class PutCapacitiveVoltageTransformerInServiceCommand(_MeasurementCommand):
    def __init__(self, *, cvt_id: str, command_id=None, correlation_id=None, causation_id=None) -> None:
        super().__init__(command_type=PUT_CVT_IN_SERVICE, payload={"cvt_id": cvt_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


class TakeCapacitiveVoltageTransformerOutOfServiceCommand(_MeasurementCommand):
    def __init__(self, *, cvt_id: str, command_id=None, correlation_id=None, causation_id=None) -> None:
        super().__init__(command_type=TAKE_CVT_OUT_OF_SERVICE, payload={"cvt_id": cvt_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id)


def _validate_refs(*refs) -> None:
    from ..endpoint_reference import EndpointReference
    for ref in refs:
        if ref is not None and not isinstance(ref, EndpointReference):
            raise TypeError("measurement endpoints must be EndpointReference or None.")


def locals_payload(values: dict, *names: str) -> dict:
    return {name: values[name] for name in names}


__all__ = [name for name in globals() if name.startswith(("CREATE_", "UPDATE_", "DELETE_", "PUT_", "TAKE_")) or name.endswith("Command")]
