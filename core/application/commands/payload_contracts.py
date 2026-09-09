"""Corrected application command payload contracts for endpoint-bearing models.

This module provides the B6.6 contract surface without changing Core models.
EndpointReference values remain unresolved until the command-handler boundary.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference
from .model_commands import (
    CREATE_BRANCH, CREATE_CABLE, CREATE_SWITCH, CREATE_DISCONNECTOR,
    UPDATE_GENERATOR, UPDATE_SHUNT,
)


class CreateBranchCommand(Command):
    def __init__(self, *, branch_id: str, endpoint_from: EndpointReference | None = None, endpoint_to: EndpointReference | None = None, r: float | None = None, x: float | None = None, b: float | None = None, name: str = "", rate_mva: float | None = None, tap: float = 1.0, shift: float = 0.0, in_service: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        for value, label in ((endpoint_from, "endpoint_from"), (endpoint_to, "endpoint_to")):
            if value is not None and not isinstance(value, EndpointReference):
                raise TypeError(f"{label} must be an EndpointReference or None.")
        super().__init__(command_type=CREATE_BRANCH, payload={"branch_id": branch_id, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "r": r, "x": x, "b": b, "name": name, "rate_mva": rate_mva, "tap": tap, "shift": shift, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class CreateCableCommand(Command):
    def __init__(self, *, cable_id: str, endpoint_from: EndpointReference | None = None, endpoint_to: EndpointReference | None = None, name: str = "", length_km: float = 0.0, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, r1_ohm_per_km: float = 0.0, x1_ohm_per_km: float = 0.0, b1_us_per_km: float = 0.0, r0_ohm_per_km: float | None = None, x0_ohm_per_km: float | None = None, b0_us_per_km: float | None = None, in_service: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        for value, label in ((endpoint_from, "endpoint_from"), (endpoint_to, "endpoint_to")):
            if value is not None and not isinstance(value, EndpointReference):
                raise TypeError(f"{label} must be an EndpointReference or None.")
        super().__init__(command_type=CREATE_CABLE, payload={"cable_id": cable_id, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "name": name, "length_km": length_km, "rated_voltage_kv": rated_voltage_kv, "rated_current_a": rated_current_a, "r1_ohm_per_km": r1_ohm_per_km, "x1_ohm_per_km": x1_ohm_per_km, "b1_us_per_km": b1_us_per_km, "r0_ohm_per_km": r0_ohm_per_km, "x0_ohm_per_km": x0_ohm_per_km, "b0_us_per_km": b0_us_per_km, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class CreateSwitchCommand(Command):
    def __init__(self, *, switch_id: str, endpoint_a: EndpointReference | None = None, endpoint_b: EndpointReference | None = None, name: str = "", closed: bool = False, in_service: bool = True, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        for value, label in ((endpoint_a, "endpoint_a"), (endpoint_b, "endpoint_b")):
            if value is not None and not isinstance(value, EndpointReference):
                raise TypeError(f"{label} must be an EndpointReference or None.")
        super().__init__(command_type=CREATE_SWITCH, payload={"switch_id": switch_id, "endpoint_a": endpoint_a, "endpoint_b": endpoint_b, "name": name, "closed": closed, "in_service": in_service, "normally_closed": normally_closed, "rated_voltage_kv": rated_voltage_kv, "rated_current_a": rated_current_a}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class CreateDisconnectorCommand(Command):
    def __init__(self, *, disconnector_id: str, voltage_kv: float, rated_current_a: float, endpoint_from: EndpointReference | None = None, endpoint_to: EndpointReference | None = None, operating_time: float = 1.0, closed: bool = True, in_service: bool = True, name: str = "", command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        for value, label in ((endpoint_from, "endpoint_from"), (endpoint_to, "endpoint_to")):
            if value is not None and not isinstance(value, EndpointReference):
                raise TypeError(f"{label} must be an EndpointReference or None.")
        super().__init__(command_type=CREATE_DISCONNECTOR, payload={"disconnector_id": disconnector_id, "voltage_kv": voltage_kv, "rated_current_a": rated_current_a, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "operating_time": operating_time, "closed": closed, "in_service": in_service, "name": name}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateGeneratorCommand(Command):
    def __init__(self, *, generator_id: str, p: float | None = None, q: float | None = None, V_setpoint: float | None = None, q_limits: tuple[float, float] | None = None, name: str | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        values = (p, q, V_setpoint, q_limits, name, in_service)
        if all(value is None for value in values):
            raise ValueError("UpdateGeneratorCommand requires at least one mutable Generator field.")
        if q_limits is not None and (not isinstance(q_limits, tuple) or len(q_limits) != 2):
            raise TypeError("q_limits must be a two-element tuple.")
        super().__init__(command_type=UPDATE_GENERATOR, payload={"generator_id": generator_id, "p": p, "q": q, "V_setpoint": V_setpoint, "q_limits": q_limits, "name": name, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateShuntCommand(Command):
    def __init__(self, *, shunt_id: str, name: str | None = None, g_pu: float | None = None, b_pu: float | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(value is None for value in (name, g_pu, b_pu, in_service)):
            raise ValueError("UpdateShuntCommand requires at least one mutable Shunt field.")
        super().__init__(command_type=UPDATE_SHUNT, payload={"shunt_id": shunt_id, "name": name, "g_pu": g_pu, "b_pu": b_pu, "in_service": in_service}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = [
    "CreateBranchCommand", "CreateCableCommand", "CreateSwitchCommand",
    "CreateDisconnectorCommand", "UpdateGeneratorCommand", "UpdateShuntCommand",
]
