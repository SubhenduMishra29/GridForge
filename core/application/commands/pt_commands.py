"""Immutable Application commands for Potential Transformer lifecycle."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_PT = "model.create_potential_transformer"
UPDATE_PT = "model.update_potential_transformer"
DELETE_PT = "model.delete_potential_transformer"
PUT_PT_IN_SERVICE = "model.put_potential_transformer_in_service"
TAKE_PT_OUT_OF_SERVICE = "model.take_potential_transformer_out_of_service"


def _endpoint(value, name: str) -> None:
    if value is not None and not isinstance(value, EndpointReference): raise TypeError(f"{name} must be an EndpointReference or None.")


class CreatePTCommand(Command):
    def __init__(self, *, pt_id: str, name: str = "", primary_voltage_kv: float = 11.0, secondary_voltage_v: float = 110.0,
                 accuracy_class: str = "0.5", burden_va: float = 100.0, phase_displacement_deg: float = 0.0,
                 in_service: bool = True, primary_a: EndpointReference | None = None, primary_b: EndpointReference | None = None,
                 secondary_a: EndpointReference | None = None, secondary_b: EndpointReference | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        for value, field in ((primary_a, "primary_a"), (primary_b, "primary_b"), (secondary_a, "secondary_a"), (secondary_b, "secondary_b")): _endpoint(value, field)
        super().__init__(command_type=CREATE_PT, payload={"pt_id": pt_id, "name": name, "primary_voltage_kv": primary_voltage_kv, "secondary_voltage_v": secondary_voltage_v, "accuracy_class": accuracy_class, "burden_va": burden_va, "phase_displacement_deg": phase_displacement_deg, "in_service": in_service, "primary_a": primary_a, "primary_b": primary_b, "secondary_a": secondary_a, "secondary_b": secondary_b}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdatePTCommand(Command):
    def __init__(self, *, pt_id: str, name: str | None = None, primary_voltage_kv: float | None = None, secondary_voltage_v: float | None = None,
                 accuracy_class: str | None = None, burden_va: float | None = None, phase_displacement_deg: float | None = None,
                 in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (name, primary_voltage_kv, secondary_voltage_v, accuracy_class, burden_va, phase_displacement_deg, in_service)): raise ValueError("UpdatePTCommand requires at least one mutable PT field.")
        super().__init__(command_type=UPDATE_PT, payload={"pt_id": pt_id, "name": name, "primary_voltage_kv": primary_voltage_kv, "secondary_voltage_v": secondary_voltage_v, "accuracy_class": accuracy_class, "burden_va": burden_va, "phase_displacement_deg": phase_displacement_deg, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeletePTCommand(Command):
    def __init__(self, *, pt_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=DELETE_PT, payload={"pt_id": pt_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class PutPTInServiceCommand(Command):
    def __init__(self, *, pt_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=PUT_PT_IN_SERVICE, payload={"pt_id": pt_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class TakePTOutOfServiceCommand(Command):
    def __init__(self, *, pt_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=TAKE_PT_OUT_OF_SERVICE, payload={"pt_id": pt_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = ["CREATE_PT", "UPDATE_PT", "DELETE_PT", "PUT_PT_IN_SERVICE", "TAKE_PT_OUT_OF_SERVICE", "CreatePTCommand", "UpdatePTCommand", "DeletePTCommand", "PutPTInServiceCommand", "TakePTOutOfServiceCommand"]
