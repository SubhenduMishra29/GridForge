"""Immutable Application commands for canonical model mutations.

Commands carry intent and value objects only. Endpoint resolution is owned by
handlers through the canonical Application endpoint resolver.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_BUS = "model.create_bus"
UPDATE_BUS = "model.update_bus"
DELETE_BUS = "model.delete_bus"
CREATE_GRID = "model.create_grid"
DELETE_GRID = "model.delete_grid"
UPDATE_GRID = "model.update_grid"
CREATE_GENERATOR = "model.create_generator"
UPDATE_GENERATOR = "model.update_generator"
DELETE_GENERATOR = "model.delete_generator"
CREATE_LOAD = "model.create_load"
DELETE_LOAD = "model.delete_load"
UPDATE_LOAD = "model.update_load"
CREATE_SHUNT = "model.create_shunt"
UPDATE_SHUNT = "model.update_shunt"
DELETE_SHUNT = "model.delete_shunt"
CREATE_LINE = "model.create_line"
DELETE_LINE = "model.delete_line"
CREATE_TRANSFORMER = "model.create_transformer"
DELETE_TRANSFORMER = "model.delete_transformer"
CREATE_CABLE = "model.create_cable"
UPDATE_CABLE = "model.update_cable"
DELETE_CABLE = "model.delete_cable"
CREATE_SWITCH = "model.create_switch"
UPDATE_SWITCH = "model.update_switch"
DELETE_SWITCH = "model.delete_switch"
OPEN_SWITCH = "model.open_switch"
CLOSE_SWITCH = "model.close_switch"
PUT_SWITCH_IN_SERVICE = "model.put_switch_in_service"
TAKE_SWITCH_OUT_OF_SERVICE = "model.take_switch_out_of_service"
CREATE_DISCONNECTOR = "model.create_disconnector"
UPDATE_DISCONNECTOR = "model.update_disconnector"
DELETE_DISCONNECTOR = "model.delete_disconnector"
OPEN_DISCONNECTOR = "model.open_disconnector"
CLOSE_DISCONNECTOR = "model.close_disconnector"
PUT_DISCONNECTOR_IN_SERVICE = "model.put_disconnector_in_service"
TAKE_DISCONNECTOR_OUT_OF_SERVICE = "model.take_disconnector_out_of_service"
CREATE_FUSE = "model.create_fuse"
UPDATE_FUSE = "model.update_fuse"
DELETE_FUSE = "model.delete_fuse"
BLOW_FUSE = "model.blow_fuse"
RESET_FUSE = "model.reset_fuse"
PUT_FUSE_IN_SERVICE = "model.put_fuse_in_service"
TAKE_FUSE_OUT_OF_SERVICE = "model.take_fuse_out_of_service"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


def _endpoint(value: EndpointReference | None, name: str) -> None:
    if value is not None and not isinstance(value, EndpointReference):
        raise TypeError(f"{name} must be an EndpointReference or None.")


class CreateBusCommand(Command):
    def __init__(self, *, bus_id: str, name: str = "", nominal_voltage_kv: float = 0.0, voltage_pu: float = 1.0,
                 angle_deg: float = 0.0, frequency_hz: float = 50.0, in_service: bool = True,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(CREATE_BUS, {"bus_id": bus_id, "name": name, "nominal_voltage_kv": nominal_voltage_kv,
            "voltage_pu": voltage_pu, "angle_deg": angle_deg, "frequency_hz": frequency_hz, "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class UpdateBusCommand(Command):
    def __init__(self, *, bus_id: str, name: str | None = None, nominal_voltage_kv: float | None = None,
                 voltage_pu: float | None = None, angle_deg: float | None = None, frequency_hz: float | None = None,
                 in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if all(v is None for v in (name, nominal_voltage_kv, voltage_pu, angle_deg, frequency_hz, in_service)):
            raise ValueError("UpdateBusCommand requires at least one mutable Bus field.")
        super().__init__(**_command(UPDATE_BUS, {"bus_id": bus_id, "name": name, "nominal_voltage_kv": nominal_voltage_kv,
            "voltage_pu": voltage_pu, "angle_deg": angle_deg, "frequency_hz": frequency_hz, "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class DeleteBusCommand(Command):
    def __init__(self, *, bus_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_BUS, {"bus_id": bus_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateGridCommand(Command):
    def __init__(self, *, grid_id: str, name: str = "", nominal_voltage_kv: float = 0.0, frequency_hz: float = 50.0,
                 voltage_pu: float = 1.0, angle_deg: float = 0.0, p_mw: float = 0.0, q_mvar: float = 0.0,
                 short_circuit_mva: float | None = None, x_over_r: float | None = None, z1_pu: complex | None = None,
                 z2_pu: complex | None = None, z0_pu: complex | None = None, in_service: bool = True,
                 grounded: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(**_command(CREATE_GRID, {"grid_id": grid_id, "name": name, "nominal_voltage_kv": nominal_voltage_kv,
            "frequency_hz": frequency_hz, "voltage_pu": voltage_pu, "angle_deg": angle_deg, "p_mw": p_mw, "q_mvar": q_mvar,
            "short_circuit_mva": short_circuit_mva, "x_over_r": x_over_r, "z1_pu": z1_pu, "z2_pu": z2_pu, "z0_pu": z0_pu,
            "in_service": in_service, "grounded": grounded}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class DeleteGridCommand(Command):
    def __init__(self, *, grid_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_GRID, {"grid_id": grid_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class UpdateGridCommand(Command):
    def __init__(self, *, grid_id: str, name: str | None = None, nominal_voltage_kv: float | None = None,
                 frequency_hz: float | None = None, voltage_pu: float | None = None, angle_deg: float | None = None,
                 p_mw: float | None = None, q_mvar: float | None = None, short_circuit_mva: float | None = None,
                 x_over_r: float | None = None, z1_pu: complex | None = None, z2_pu: complex | None = None,
                 z0_pu: complex | None = None, in_service: bool | None = None, grounded: bool | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        values = (name, nominal_voltage_kv, frequency_hz, voltage_pu, angle_deg, p_mw, q_mvar, short_circuit_mva, x_over_r, z1_pu, z2_pu, z0_pu, in_service, grounded)
        if all(v is None for v in values): raise ValueError("UpdateGridCommand requires at least one mutable Grid field.")
        super().__init__(**_command(UPDATE_GRID, {"grid_id": grid_id, "name": name, "nominal_voltage_kv": nominal_voltage_kv,
            "frequency_hz": frequency_hz, "voltage_pu": voltage_pu, "angle_deg": angle_deg, "p_mw": p_mw, "q_mvar": q_mvar,
            "short_circuit_mva": short_circuit_mva, "x_over_r": x_over_r, "z1_pu": z1_pu, "z2_pu": z2_pu, "z0_pu": z0_pu,
            "in_service": in_service, "grounded": grounded}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateGeneratorCommand(Command):
    def __init__(self, *, generator_id: str, endpoint: EndpointReference | None = None, p: float = 0.0, q: float = 0.0,
                 V_setpoint: float = 1.0, q_limits: tuple[float, float] = (-float("inf"), float("inf")), name: str = "",
                 in_service: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint, "endpoint")
        super().__init__(**_command(CREATE_GENERATOR, {"generator_id": generator_id, "endpoint": endpoint, "p": p, "q": q,
            "V_setpoint": V_setpoint, "q_limits": q_limits, "name": name, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class UpdateGeneratorCommand(Command):
    def __init__(self, *, generator_id: str, p: float | None = None, q: float | None = None, V_setpoint: float | None = None,
                 q_limits: tuple[float, float] | None = None, name: str | None = None, in_service: bool | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (p, q, V_setpoint, q_limits, name, in_service)): raise ValueError("UpdateGeneratorCommand requires at least one mutable Generator field.")
        super().__init__(**_command(UPDATE_GENERATOR, {"generator_id": generator_id, "p": p, "q": q, "V_setpoint": V_setpoint,
            "q_limits": q_limits, "name": name, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class DeleteGeneratorCommand(Command):
    def __init__(self, *, generator_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_GENERATOR, {"generator_id": generator_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateLoadCommand(Command):
    def __init__(self, *, load_id: str, p: float = 0.0, q: float = 0.0, name: str = "", in_service: bool = True,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(CREATE_LOAD, {"load_id": load_id, "p": p, "q": q, "name": name, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteLoadCommand(Command):
    def __init__(self, *, load_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_LOAD, {"load_id": load_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class UpdateLoadCommand(Command):
    def __init__(self, *, load_id: str, name: str | None = None, p: float | None = None, q: float | None = None, in_service: bool | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (name, p, q, in_service)): raise ValueError("UpdateLoadCommand requires at least one mutable Load field.")
        super().__init__(**_command(UPDATE_LOAD, {"load_id": load_id, "name": name, "p": p, "q": q, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateShuntCommand(Command):
    def __init__(self, *, shunt_id: str, name: str = "", endpoint: EndpointReference | None = None, g_pu: float = 0.0, b_pu: float = 0.0, in_service: bool = True,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint, "endpoint")
        super().__init__(**_command(CREATE_SHUNT, {"shunt_id": shunt_id, "name": name, "endpoint": endpoint, "g_pu": g_pu, "b_pu": b_pu, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class UpdateShuntCommand(Command):
    def __init__(self, *, shunt_id: str, name: str | None = None, g_pu: float | None = None, b_pu: float | None = None, in_service: bool | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (name, g_pu, b_pu, in_service)): raise ValueError("UpdateShuntCommand requires at least one mutable Shunt field.")
        super().__init__(**_command(UPDATE_SHUNT, {"shunt_id": shunt_id, "name": name, "g_pu": g_pu, "b_pu": b_pu, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteShuntCommand(Command):
    def __init__(self, *, shunt_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_SHUNT, {"shunt_id": shunt_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateLineCommand(Command):
    def __init__(self, *, line_id: str, endpoint_from: EndpointReference, endpoint_to: EndpointReference, r: float, x: float, b: float = 0.0, name: str = "", rate_mva: float = 100.0,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(endpoint_from, EndpointReference) or not isinstance(endpoint_to, EndpointReference): raise TypeError("Line endpoints must be EndpointReference values.")
        super().__init__(**_command(CREATE_LINE, {"line_id": line_id, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "r": r, "x": x, "b": b, "name": name, "rate_mva": rate_mva}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteLineCommand(Command):
    def __init__(self, *, line_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_LINE, {"line_id": line_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class CreateTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, endpoint_from: EndpointReference, endpoint_to: EndpointReference, r: float, x: float, tap: float = 1.0, shift: float = 0.0, name: str = "", rate_mva: float = 100.0,
                 command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if not isinstance(endpoint_from, EndpointReference) or not isinstance(endpoint_to, EndpointReference): raise TypeError("Transformer endpoints must be EndpointReference values.")
        super().__init__(**_command(CREATE_TRANSFORMER, {"transformer_id": transformer_id, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "r": r, "x": x, "tap": tap, "shift": shift, "name": name, "rate_mva": rate_mva}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteTransformerCommand(Command):
    def __init__(self, *, transformer_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_TRANSFORMER, {"transformer_id": transformer_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateCableCommand(Command):
    def __init__(self, *, cable_id: str, endpoint_from: EndpointReference | None = None, endpoint_to: EndpointReference | None = None, name: str = "", length_km: float = 0.0, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, r1_ohm_per_km: float = 0.0, x1_ohm_per_km: float = 0.0, b1_us_per_km: float = 0.0, r0_ohm_per_km: float | None = None, x0_ohm_per_km: float | None = None, b0_us_per_km: float | None = None, in_service: bool = True, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint_from, "endpoint_from"); _endpoint(endpoint_to, "endpoint_to")
        super().__init__(**_command(CREATE_CABLE, {"cable_id": cable_id, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "name": name, "length_km": length_km, "rated_voltage_kv": rated_voltage_kv, "rated_current_a": rated_current_a, "r1_ohm_per_km": r1_ohm_per_km, "x1_ohm_per_km": x1_ohm_per_km, "r1_ohm_per_km": r1_ohm_per_km, "x1_ohm_per_km": x1_ohm_per_km, "b1_us_per_km": b1_us_per_km, "r0_ohm_per_km": r0_ohm_per_km, "x0_ohm_per_km": x0_ohm_per_km, "b0_us_per_km": b0_us_per_km, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class UpdateCableCommand(Command):
    def __init__(self, *, cable_id: str, name: str | None = None, length_km: float | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, r1_ohm_per_km: float | None = None, x1_ohm_per_km: float | None = None, b1_us_per_km: float | None = None, r0_ohm_per_km: float | None = None, x0_ohm_per_km: float | None = None, b0_us_per_km: float | None = None, in_service: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (name, length_km, rated_voltage_kv, rated_current_a, r1_ohm_per_km, x1_ohm_per_km, b1_us_per_km, r0_ohm_per_km, x0_ohm_per_km, b0_us_per_km, in_service)): raise ValueError("UpdateCableCommand requires at least one mutable Cable field.")
        super().__init__(**_command(UPDATE_CABLE, {"cable_id": cable_id, "name": name, "length_km": length_km, "rated_voltage_kv": rated_voltage_kv, "rated_current_a": rated_current_a, "r1_ohm_per_km": r1_ohm_per_km, "x1_ohm_per_km": x1_ohm_per_km, "b1_us_per_km": b1_us_per_km, "r0_ohm_per_km": r0_ohm_per_km, "x0_ohm_per_km": x0_ohm_per_km, "b0_us_per_km": b0_us_per_km, "in_service": in_service}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteCableCommand(Command):
    def __init__(self, *, cable_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_CABLE, {"cable_id": cable_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateSwitchCommand(Command):
    def __init__(self, *, switch_id: str, endpoint_a: EndpointReference | None = None, endpoint_b: EndpointReference | None = None, name: str = "", closed: bool = False, in_service: bool = True, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint_a, "endpoint_a"); _endpoint(endpoint_b, "endpoint_b")
        super().__init__(**_command(CREATE_SWITCH, {"switch_id": switch_id, "endpoint_a": endpoint_a, "endpoint_b": endpoint_b, "name": name, "closed": closed, "in_service": in_service, "normally_closed": normally_closed, "rated_voltage_kv": rated_voltage_kv, "rated_current_a": rated_current_a}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class UpdateSwitchCommand(Command):
    def __init__(self, *, switch_id: str, name: str | None = None, closed: bool | None = None, in_service: bool | None = None, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (name, closed, in_service, normally_closed, rated_voltage_kv, rated_current_a)): raise ValueError("UpdateSwitchCommand requires at least one mutable Switch field.")
        super().__init__(**_command(UPDATE_SWITCH, {"switch_id": switch_id, "name": name, "closed": closed, "in_service": in_service, "normally_closed": normally_closed, "rated_voltage_kv": rated_voltage_kv, "rated_current_a": rated_current_a}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteSwitchCommand(Command):
    def __init__(self, *, switch_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_SWITCH, {"switch_id": switch_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class OpenSwitchCommand(Command):
    def __init__(self, *, switch_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(OPEN_SWITCH, {"switch_id": switch_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class CloseSwitchCommand(Command):
    def __init__(self, *, switch_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(CLOSE_SWITCH, {"switch_id": switch_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class PutSwitchInServiceCommand(Command):
    def __init__(self, *, switch_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(PUT_SWITCH_IN_SERVICE, {"switch_id": switch_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class TakeSwitchOutOfServiceCommand(Command):
    def __init__(self, *, switch_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(TAKE_SWITCH_OUT_OF_SERVICE, {"switch_id": switch_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateDisconnectorCommand(Command):
    def __init__(self, *, disconnector_id: str, voltage_kv: float, rated_current_a: float, endpoint_from: EndpointReference | None = None, endpoint_to: EndpointReference | None = None, operating_time: float = 1.0, closed: bool = True, in_service: bool = True, name: str = "", command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint_from, "endpoint_from"); _endpoint(endpoint_to, "endpoint_to")
        super().__init__(**_command(CREATE_DISCONNECTOR, {"disconnector_id": disconnector_id, "voltage_kv": voltage_kv, "rated_current_a": rated_current_a, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "operating_time": operating_time, "closed": closed, "in_service": in_service, "name": name}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class UpdateDisconnectorCommand(Command):
    def __init__(self, *, disconnector_id: str, voltage_kv: float | None = None, rated_current_a: float | None = None, operating_time: float | None = None, closed: bool | None = None, in_service: bool | None = None, name: str | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (voltage_kv, rated_current_a, operating_time, closed, in_service, name)): raise ValueError("UpdateDisconnectorCommand requires at least one mutable Disconnector field.")
        super().__init__(**_command(UPDATE_DISCONNECTOR, {"disconnector_id": disconnector_id, "voltage_kv": voltage_kv, "rated_current_a": rated_current_a, "operating_time": operating_time, "closed": closed, "in_service": in_service, "name": name}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteDisconnectorCommand(Command):
    def __init__(self, *, disconnector_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_DISCONNECTOR, {"disconnector_id": disconnector_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class OpenDisconnectorCommand(Command):
    def __init__(self, *, disconnector_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(OPEN_DISCONNECTOR, {"disconnector_id": disconnector_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class CloseDisconnectorCommand(Command):
    def __init__(self, *, disconnector_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(CLOSE_DISCONNECTOR, {"disconnector_id": disconnector_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class PutDisconnectorInServiceCommand(Command):
    def __init__(self, *, disconnector_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(PUT_DISCONNECTOR_IN_SERVICE, {"disconnector_id": disconnector_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class TakeDisconnectorOutOfServiceCommand(Command):
    def __init__(self, *, disconnector_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(TAKE_DISCONNECTOR_OUT_OF_SERVICE, {"disconnector_id": disconnector_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

class CreateFuseCommand(Command):
    def __init__(self, *, fuse_id: str, endpoint_from: EndpointReference | None = None, endpoint_to: EndpointReference | None = None, name: str = "", rated_current_a: float = 1.0, rated_voltage_v: float = 1.0, interrupting_rating_ka: float = 0.0, in_service: bool = True, blown: bool = False, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint_from, "endpoint_from"); _endpoint(endpoint_to, "endpoint_to")
        super().__init__(**_command(CREATE_FUSE, {"fuse_id": fuse_id, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "name": name, "rated_current_a": rated_current_a, "rated_voltage_v": rated_voltage_v, "interrupting_rating_ka": interrupting_rating_ka, "in_service": in_service, "blown": blown}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class UpdateFuseCommand(Command):
    def __init__(self, *, fuse_id: str, name: str | None = None, rated_current_a: float | None = None, rated_voltage_v: float | None = None, interrupting_rating_ka: float | None = None, in_service: bool | None = None, blown: bool | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(v is None for v in (name, rated_current_a, rated_voltage_v, interrupting_rating_ka, in_service, blown)): raise ValueError("UpdateFuseCommand requires at least one mutable Fuse field.")
        super().__init__(**_command(UPDATE_FUSE, {"fuse_id": fuse_id, "name": name, "rated_current_a": rated_current_a, "rated_voltage_v": rated_voltage_v, "interrupting_rating_ka": interrupting_rating_ka, "in_service": in_service, "blown": blown}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class DeleteFuseCommand(Command):
    def __init__(self, *, fuse_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_FUSE, {"fuse_id": fuse_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class BlowFuseCommand(Command):
    def __init__(self, *, fuse_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(BLOW_FUSE, {"fuse_id": fuse_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class ResetFuseCommand(Command):
    def __init__(self, *, fuse_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(RESET_FUSE, {"fuse_id": fuse_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class PutFuseInServiceCommand(Command):
    def __init__(self, *, fuse_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(PUT_FUSE_IN_SERVICE, {"fuse_id": fuse_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))
class TakeFuseOutOfServiceCommand(Command):
    def __init__(self, *, fuse_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(TAKE_FUSE_OUT_OF_SERVICE, {"fuse_id": fuse_id}, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))

__all__ = [
    "CREATE_BUS", "UPDATE_BUS", "DELETE_BUS", "CreateBusCommand", "UpdateBusCommand", "DeleteBusCommand",
    "CREATE_GRID", "DELETE_GRID", "UPDATE_GRID", "CreateGridCommand", "DeleteGridCommand", "UpdateGridCommand",
    "CREATE_GENERATOR", "UPDATE_GENERATOR", "DELETE_GENERATOR", "CreateGeneratorCommand", "UpdateGeneratorCommand", "DeleteGeneratorCommand",
    "CREATE_LOAD", "DELETE_LOAD", "UPDATE_LOAD", "CreateLoadCommand", "DeleteLoadCommand", "UpdateLoadCommand",
    "CREATE_SHUNT", "UPDATE_SHUNT", "DELETE_SHUNT", "CreateShuntCommand", "UpdateShuntCommand", "DeleteShuntCommand",
    "CREATE_LINE", "DELETE_LINE", "CreateLineCommand", "DeleteLineCommand", "CREATE_TRANSFORMER", "DELETE_TRANSFORMER", "CreateTransformerCommand", "DeleteTransformerCommand",
    "CREATE_CABLE", "UPDATE_CABLE", "DELETE_CABLE", "CreateCableCommand", "UpdateCableCommand", "DeleteCableCommand",
    "CREATE_SWITCH", "UPDATE_SWITCH", "DELETE_SWITCH", "OPEN_SWITCH", "CLOSE_SWITCH", "PUT_SWITCH_IN_SERVICE", "TAKE_SWITCH_OUT_OF_SERVICE", "CreateSwitchCommand", "UpdateSwitchCommand", "DeleteSwitchCommand", "OpenSwitchCommand", "CloseSwitchCommand", "PutSwitchInServiceCommand", "TakeSwitchOutOfServiceCommand",
    "CREATE_DISCONNECTOR", "UPDATE_DISCONNECTOR", "DELETE_DISCONNECTOR", "OPEN_DISCONNECTOR", "CLOSE_DISCONNECTOR", "PUT_DISCONNECTOR_IN_SERVICE", "TAKE_DISCONNECTOR_OUT_OF_SERVICE", "CreateDisconnectorCommand", "UpdateDisconnectorCommand", "DeleteDisconnectorCommand", "OpenDisconnectorCommand", "CloseDisconnectorCommand", "PutDisconnectorInServiceCommand", "TakeDisconnectorOutOfServiceCommand",
    "CREATE_FUSE", "UPDATE_FUSE", "DELETE_FUSE", "BLOW_FUSE", "RESET_FUSE", "PUT_FUSE_IN_SERVICE", "TAKE_FUSE_OUT_OF_SERVICE", "CreateFuseCommand", "UpdateFuseCommand", "DeleteFuseCommand", "BlowFuseCommand", "ResetFuseCommand", "PutFuseInServiceCommand", "TakeFuseOutOfServiceCommand",
]
