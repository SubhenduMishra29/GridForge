# ============================================================
# File: core/application/commands/model_commands.py
# GridForge V2 — Model Commands
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Model Commands
==========================================

Immutable commands representing model-level application intent.

Architectural rules
-------------------

Commands:

    * contain Application intent only;
    * may contain immutable value objects;
    * do not contain Core model objects;
    * do not resolve endpoints;
    * do not mutate Core;
    * do not perform engineering calculations;
    * do not access UI state.

Topology
--------

Where an equipment model explicitly has electrical endpoints, the command
carries EndpointReference value objects.

Endpoint resolution belongs to the Application handler boundary.

Commands never contain:

    * Bus objects;
    * Terminal objects;
    * Network objects;
    * SLD objects;
    * solver indices;
    * Y-bus indices;
    * numerical matrix data.

Author:
    Subhendu Mishra
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference


# ============================================================
# COMMAND TYPES
# ============================================================

CREATE_BUS = "model.create_bus"
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

CREATE_BRANCH = "model.create_branch"
UPDATE_BRANCH = "model.update_branch"
DELETE_BRANCH = "model.delete_branch"

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
TAKE_DISCONNECTOR_OUT_OF_SERVICE = (
    "model.take_disconnector_out_of_service"
)

CREATE_FUSE = "model.create_fuse"
UPDATE_FUSE = "model.update_fuse"
DELETE_FUSE = "model.delete_fuse"
BLOW_FUSE = "model.blow_fuse"
RESET_FUSE = "model.reset_fuse"
PUT_FUSE_IN_SERVICE = "model.put_fuse_in_service"
TAKE_FUSE_OUT_OF_SERVICE = "model.take_fuse_out_of_service"


# ============================================================
# BUS
# ============================================================

class CreateBusCommand(Command):
    """Request creation of a canonical Core Bus."""

    def __init__(
        self,
        *,
        bus_id: str,
        name: str = "",
        bus_type: Any = None,
        voltage: float = 1.0,
        angle: float = 0.0,
        p_spec: float = 0.0,
        q_spec: float = 0.0,
        v_setpoint: float | None = None,
        q_min: float = float("-inf"),
        q_max: float = float("inf"),
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_BUS,
            payload={
                "bus_id": bus_id,
                "name": name,
                "bus_type": bus_type,
                "voltage": voltage,
                "angle": angle,
                "p_spec": p_spec,
                "q_spec": q_spec,
                "v_setpoint": v_setpoint,
                "q_min": q_min,
                "q_max": q_max,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteBusCommand(Command):
    """Request deletion of a canonical Core Bus."""

    def __init__(
        self,
        *,
        bus_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_BUS,
            payload={"bus_id": bus_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# GRID
# ============================================================

class CreateGridCommand(Command):
    """Request creation of a canonical Core Grid."""

    def __init__(
        self,
        *,
        grid_id: str,
        name: str = "",
        nominal_voltage_kv: float = 0.0,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        angle_deg: float = 0.0,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        short_circuit_mva: float | None = None,
        x_over_r: float | None = None,
        z1_pu: complex | None = None,
        z2_pu: complex | None = None,
        z0_pu: complex | None = None,
        in_service: bool = True,
        grounded: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_GRID,
            payload={
                "grid_id": grid_id,
                "name": name,
                "nominal_voltage_kv": nominal_voltage_kv,
                "frequency_hz": frequency_hz,
                "voltage_pu": voltage_pu,
                "angle_deg": angle_deg,
                "p_mw": p_mw,
                "q_mvar": q_mvar,
                "short_circuit_mva": short_circuit_mva,
                "x_over_r": x_over_r,
                "z1_pu": z1_pu,
                "z2_pu": z2_pu,
                "z0_pu": z0_pu,
                "in_service": in_service,
                "grounded": grounded,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteGridCommand(Command):
    """Request deletion of a canonical Core Grid."""

    def __init__(
        self,
        *,
        grid_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_GRID,
            payload={"grid_id": grid_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateGridCommand(Command):
    """Request mutation of an existing canonical Core Grid."""

    def __init__(
        self,
        *,
        grid_id: str,
        name: str | None = None,
        nominal_voltage_kv: float | None = None,
        frequency_hz: float | None = None,
        voltage_pu: float | None = None,
        angle_deg: float | None = None,
        p_mw: float | None = None,
        q_mvar: float | None = None,
        short_circuit_mva: float | None = None,
        x_over_r: float | None = None,
        z1_pu: complex | None = None,
        z2_pu: complex | None = None,
        z0_pu: complex | None = None,
        in_service: bool | None = None,
        grounded: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        values = (
            name,
            nominal_voltage_kv,
            frequency_hz,
            voltage_pu,
            angle_deg,
            p_mw,
            q_mvar,
            short_circuit_mva,
            x_over_r,
            z1_pu,
            z2_pu,
            z0_pu,
            in_service,
            grounded,
        )

        if all(value is None for value in values):
            raise ValueError(
                "UpdateGridCommand requires at least one "
                "mutable Grid field."
            )

        super().__init__(
            command_type=UPDATE_GRID,
            payload={
                "grid_id": grid_id,
                "name": name,
                "nominal_voltage_kv": nominal_voltage_kv,
                "frequency_hz": frequency_hz,
                "voltage_pu": voltage_pu,
                "angle_deg": angle_deg,
                "p_mw": p_mw,
                "q_mvar": q_mvar,
                "short_circuit_mva": short_circuit_mva,
                "x_over_r": x_over_r,
                "z1_pu": z1_pu,
                "z2_pu": z2_pu,
                "z0_pu": z0_pu,
                "in_service": in_service,
                "grounded": grounded,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# GENERATOR
# ============================================================

class CreateGeneratorCommand(Command):
    """
    Request creation of a canonical Core Generator.

    The endpoint is represented only by an EndpointReference.
    Endpoint resolution is performed outside the command.
    """

    def __init__(
        self,
        *,
        generator_id: str,
        endpoint: EndpointReference | None = None,
        p: float = 0.0,
        q: float = 0.0,
        V_setpoint: float = 1.0,
        q_limits: tuple[float, float] = (
            -float("inf"),
            float("inf"),
        ),
        name: str = "",
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if (
            endpoint is not None
            and not isinstance(endpoint, EndpointReference)
        ):
            raise TypeError(
                "endpoint must be an EndpointReference or None."
            )

        if (
            not isinstance(q_limits, tuple)
            or len(q_limits) != 2
        ):
            raise TypeError(
                "q_limits must be a two-element tuple."
            )

        super().__init__(
            command_type=CREATE_GENERATOR,
            payload={
                "generator_id": generator_id,
                "endpoint": endpoint,
                "p": p,
                "q": q,
                "V_setpoint": V_setpoint,
                "q_limits": q_limits,
                "name": name,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateGeneratorCommand(Command):
    """Request mutation of an existing Core Generator."""

    def __init__(
        self,
        *,
        generator_id: str,
        p: float | None = None,
        q: float | None = None,
        V_setpoint: float | None = None,
        q_limits: tuple[float, float] | None = None,
        name: str | None = None,
        in_service: bool | None = None,
        endpoint: EndpointReference | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if (
            endpoint is not None
            and not isinstance(endpoint, EndpointReference)
        ):
            raise TypeError(
                "endpoint must be an EndpointReference or None."
            )

        values = (
            p,
            q,
            V_setpoint,
            q_limits,
            name,
            in_service,
            endpoint,
        )

        if all(value is None for value in values):
            raise ValueError(
                "UpdateGeneratorCommand requires at least one "
                "mutable Generator field."
            )

        if (
            q_limits is not None
            and (
                not isinstance(q_limits, tuple)
                or len(q_limits) != 2
            )
        ):
            raise TypeError(
                "q_limits must be a two-element tuple."
            )

        super().__init__(
            command_type=UPDATE_GENERATOR,
            payload={
                "generator_id": generator_id,
                "p": p,
                "q": q,
                "V_setpoint": V_setpoint,
                "q_limits": q_limits,
                "name": name,
                "in_service": in_service,
                "endpoint": endpoint,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteGeneratorCommand(Command):
    """Request deletion of a canonical Core Generator."""

    def __init__(
        self,
        *,
        generator_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_GENERATOR,
            payload={"generator_id": generator_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# LOAD
# ============================================================

class CreateLoadCommand(Command):
    """Request creation of a canonical Core Load."""

    def __init__(
        self,
        *,
        load_id: str,
        p: float = 0.0,
        q: float = 0.0,
        name: str = "",
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_LOAD,
            payload={
                "load_id": load_id,
                "p": p,
                "q": q,
                "name": name,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteLoadCommand(Command):
    """Request deletion of a canonical Core Load."""

    def __init__(
        self,
        *,
        load_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_LOAD,
            payload={"load_id": load_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateLoadCommand(Command):
    """Request mutation of an existing canonical Core Load."""

    def __init__(
        self,
        *,
        load_id: str,
        name: str | None = None,
        p: float | None = None,
        q: float | None = None,
        in_service: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (name, p, q, in_service)
        ):
            raise ValueError(
                "UpdateLoadCommand requires at least one "
                "mutable Load field."
            )

        super().__init__(
            command_type=UPDATE_LOAD,
            payload={
                "load_id": load_id,
                "name": name,
                "p": p,
                "q": q,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# SHUNT
# ============================================================

class CreateShuntCommand(Command):
    """
    Request creation of a canonical Core Shunt.

    The endpoint is represented only by an EndpointReference.
    """

    def __init__(
        self,
        *,
        shunt_id: str,
        name: str = "",
        endpoint: EndpointReference | None = None,
        g_pu: float = 0.0,
        b_pu: float = 0.0,
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if (
            endpoint is not None
            and not isinstance(endpoint, EndpointReference)
        ):
            raise TypeError(
                "endpoint must be an EndpointReference or None."
            )

        super().__init__(
            command_type=CREATE_SHUNT,
            payload={
                "shunt_id": shunt_id,
                "name": name,
                "endpoint": endpoint,
                "g_pu": g_pu,
                "b_pu": b_pu,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateShuntCommand(Command):
    """Request mutation of an existing Core Shunt."""

    def __init__(
        self,
        *,
        shunt_id: str,
        name: str | None = None,
        endpoint: EndpointReference | None = None,
        g_pu: float | None = None,
        b_pu: float | None = None,
        in_service: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if (
            endpoint is not None
            and not isinstance(endpoint, EndpointReference)
        ):
            raise TypeError(
                "endpoint must be an EndpointReference or None."
            )

        if all(
            value is None
            for value in (
                name,
                endpoint,
                g_pu,
                b_pu,
                in_service,
            )
        ):
            raise ValueError(
                "UpdateShuntCommand requires at least one "
                "mutable Shunt field."
            )

        super().__init__(
            command_type=UPDATE_SHUNT,
            payload={
                "shunt_id": shunt_id,
                "name": name,
                "endpoint": endpoint,
                "g_pu": g_pu,
                "b_pu": b_pu,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteShuntCommand(Command):
    """Request deletion of a canonical Core Shunt."""

    def __init__(
        self,
        *,
        shunt_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_SHUNT,
            payload={"shunt_id": shunt_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# LINE
# ============================================================

class CreateLineCommand(Command):
    """
    Request creation of a canonical Core Line.

    Endpoints remain immutable EndpointReference values.
    """

    def __init__(
        self,
        *,
        line_id: str,
        endpoint_from: EndpointReference,
        endpoint_to: EndpointReference,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(endpoint_from, EndpointReference):
            raise TypeError(
                "endpoint_from must be an EndpointReference."
            )

        if not isinstance(endpoint_to, EndpointReference):
            raise TypeError(
                "endpoint_to must be an EndpointReference."
            )

        super().__init__(
            command_type=CREATE_LINE,
            payload={
                "line_id": line_id,
                "endpoint_from": endpoint_from,
                "endpoint_to": endpoint_to,
                "r": r,
                "x": x,
                "b": b,
                "name": name,
                "rate_mva": rate_mva,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteLineCommand(Command):
    """Request deletion of a canonical Core Line."""

    def __init__(
        self,
        *,
        line_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_LINE,
            payload={"line_id": line_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# TRANSFORMER
# ============================================================

class CreateTransformerCommand(Command):
    """Request creation of a canonical Core Transformer."""

    def __init__(
        self,
        *,
        transformer_id: str,
        endpoint_from: EndpointReference,
        endpoint_to: EndpointReference,
        r: float,
        x: float,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(endpoint_from, EndpointReference):
            raise TypeError(
                "endpoint_from must be an EndpointReference."
            )

        if not isinstance(endpoint_to, EndpointReference):
            raise TypeError(
                "endpoint_to must be an EndpointReference."
            )

        super().__init__(
            command_type=CREATE_TRANSFORMER,
            payload={
                "transformer_id": transformer_id,
                "endpoint_from": endpoint_from,
                "endpoint_to": endpoint_to,
                "r": r,
                "x": x,
                "tap": tap,
                "shift": shift,
                "name": name,
                "rate_mva": rate_mva,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteTransformerCommand(Command):
    """Request deletion of a canonical Core Transformer."""

    def __init__(
        self,
        *,
        transformer_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_TRANSFORMER,
            payload={"transformer_id": transformer_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# BRANCH
# ============================================================

class CreateBranchCommand(Command):
    """Request creation of a generic Core Branch."""

    def __init__(
        self,
        *,
        branch_id: str,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        name: str = "",
        rate_mva: float | None = None,
        tap: float = 1.0,
        shift: float = 0.0,
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_BRANCH,
            payload={
                "branch_id": branch_id,
                "r": r,
                "x": x,
                "b": b,
                "name": name,
                "rate_mva": rate_mva,
                "tap": tap,
                "shift": shift,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateBranchCommand(Command):
    """Request mutation of an existing Core Branch."""

    def __init__(
        self,
        *,
        branch_id: str,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None,
        name: str | None = None,
        rate_mva: float | None = None,
        tap: float | None = None,
        shift: float | None = None,
        in_service: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                r,
                x,
                b,
                name,
                rate_mva,
                tap,
                shift,
                in_service,
            )
        ):
            raise ValueError(
                "UpdateBranchCommand requires at least one "
                "mutable Branch field."
            )

        super().__init__(
            command_type=UPDATE_BRANCH,
            payload={
                "branch_id": branch_id,
                "r": r,
                "x": x,
                "b": b,
                "name": name,
                "rate_mva": rate_mva,
                "tap": tap,
                "shift": shift,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteBranchCommand(Command):
    """Request deletion of a Core Branch."""

    def __init__(
        self,
        *,
        branch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_BRANCH,
            payload={"branch_id": branch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# CABLE
# ============================================================

class CreateCableCommand(Command):
    """Request creation of a physical Core Cable."""

    def __init__(
        self,
        *,
        cable_id: str,
        name: str = "",
        length_km: float = 0.0,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float = 0.0,
        x1_ohm_per_km: float = 0.0,
        b1_us_per_km: float = 0.0,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool = True,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_CABLE,
            payload={
                "cable_id": cable_id,
                "name": name,
                "length_km": length_km,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
                "r1_ohm_per_km": r1_ohm_per_km,
                "x1_ohm_per_km": x1_ohm_per_km,
                "b1_us_per_km": b1_us_per_km,
                "r0_ohm_per_km": r0_ohm_per_km,
                "x0_ohm_per_km": x0_ohm_per_km,
                "b0_us_per_km": b0_us_per_km,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateCableCommand(Command):
    """Request mutation of an existing Core Cable."""

    def __init__(
        self,
        *,
        cable_id: str,
        name: str | None = None,
        length_km: float | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float | None = None,
        x1_ohm_per_km: float | None = None,
        b1_us_per_km: float | None = None,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                name,
                length_km,
                rated_voltage_kv,
                rated_current_a,
                r1_ohm_per_km,
                x1_ohm_per_km,
                b1_us_per_km,
                r0_ohm_per_km,
                x0_ohm_per_km,
                b0_us_per_km,
                in_service,
            )
        ):
            raise ValueError(
                "UpdateCableCommand requires at least one "
                "mutable Cable field."
            )

        super().__init__(
            command_type=UPDATE_CABLE,
            payload={
                "cable_id": cable_id,
                "name": name,
                "length_km": length_km,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
                "r1_ohm_per_km": r1_ohm_per_km,
                "x1_ohm_per_km": x1_ohm_per_km,
                "b1_us_per_km": b1_us_per_km,
                "r0_ohm_per_km": r0_ohm_per_km,
                "x0_ohm_per_km": x0_ohm_per_km,
                "b0_us_per_km": b0_us_per_km,
                "in_service": in_service,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteCableCommand(Command):
    """Request deletion of a Core Cable."""

    def __init__(
        self,
        *,
        cable_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_CABLE,
            payload={"cable_id": cable_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# SWITCH
# ============================================================

class CreateSwitchCommand(Command):
    """Request creation of a Core Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        name: str = "",
        closed: bool = False,
        in_service: bool = True,
        normally_closed: bool | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_SWITCH,
            payload={
                "switch_id": switch_id,
                "name": name,
                "closed": closed,
                "in_service": in_service,
                "normally_closed": normally_closed,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateSwitchCommand(Command):
    """Request mutation of local Switch configuration/state."""

    def __init__(
        self,
        *,
        switch_id: str,
        name: str | None = None,
        closed: bool | None = None,
        in_service: bool | None = None,
        normally_closed: bool | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                name,
                closed,
                in_service,
                normally_closed,
                rated_voltage_kv,
                rated_current_a,
            )
        ):
            raise ValueError(
                "UpdateSwitchCommand requires at least one "
                "mutable Switch field."
            )

        super().__init__(
            command_type=UPDATE_SWITCH,
            payload={
                "switch_id": switch_id,
                "name": name,
                "closed": closed,
                "in_service": in_service,
                "normally_closed": normally_closed,
                "rated_voltage_kv": rated_voltage_kv,
                "rated_current_a": rated_current_a,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteSwitchCommand(Command):
    """Request deletion of a Core Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_SWITCH,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class OpenSwitchCommand(Command):
    """Request opening a Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=OPEN_SWITCH,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class CloseSwitchCommand(Command):
    """Request closing a Switch."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CLOSE_SWITCH,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class PutSwitchInServiceCommand(Command):
    """Request placing a Switch in service."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=PUT_SWITCH_IN_SERVICE,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class TakeSwitchOutOfServiceCommand(Command):
    """Request taking a Switch out of service."""

    def __init__(
        self,
        *,
        switch_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=TAKE_SWITCH_OUT_OF_SERVICE,
            payload={"switch_id": switch_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# DISCONNECTOR
# ============================================================

class CreateDisconnectorCommand(Command):
    """Request creation of a Core Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        voltage_kv: float,
        rated_current_a: float,
        operating_time: float = 1.0,
        closed: bool = True,
        in_service: bool = True,
        name: str = "",
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_DISCONNECTOR,
            payload={
                "disconnector_id": disconnector_id,
                "voltage_kv": voltage_kv,
                "rated_current_a": rated_current_a,
                "operating_time": operating_time,
                "closed": closed,
                "in_service": in_service,
                "name": name,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateDisconnectorCommand(Command):
    """Request mutation of local Disconnector state/configuration."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        operating_time: float | None = None,
        closed: bool | None = None,
        in_service: bool | None = None,
        name: str | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                voltage_kv,
                rated_current_a,
                operating_time,
                closed,
                in_service,
                name,
            )
        ):
            raise ValueError(
                "UpdateDisconnectorCommand requires at least one "
                "mutable Disconnector field."
            )

        super().__init__(
            command_type=UPDATE_DISCONNECTOR,
            payload={
                "disconnector_id": disconnector_id,
                "voltage_kv": voltage_kv,
                "rated_current_a": rated_current_a,
                "operating_time": operating_time,
                "closed": closed,
                "in_service": in_service,
                "name": name,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteDisconnectorCommand(Command):
    """Request deletion of a Core Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_DISCONNECTOR,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class OpenDisconnectorCommand(Command):
    """Request opening a Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=OPEN_DISCONNECTOR,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class CloseDisconnectorCommand(Command):
    """Request closing a Disconnector."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CLOSE_DISCONNECTOR,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class PutDisconnectorInServiceCommand(Command):
    """Request placing a Disconnector in service."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=PUT_DISCONNECTOR_IN_SERVICE,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class TakeDisconnectorOutOfServiceCommand(Command):
    """Request taking a Disconnector out of service."""

    def __init__(
        self,
        *,
        disconnector_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=TAKE_DISCONNECTOR_OUT_OF_SERVICE,
            payload={"disconnector_id": disconnector_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# FUSE
# ============================================================

class CreateFuseCommand(Command):
    """Request creation of a Core Fuse."""

    def __init__(
        self,
        *,
        fuse_id: str,
        name: str = "",
        rated_current_a: float = 1.0,
        rated_voltage_v: float = 1.0,
        interrupting_rating_ka: float = 0.0,
        in_service: bool = True,
        blown: bool = False,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_FUSE,
            payload={
                "fuse_id": fuse_id,
                "name": name,
                "rated_current_a": rated_current_a,
                "rated_voltage_v": rated_voltage_v,
                "interrupting_rating_ka": interrupting_rating_ka,
                "in_service": in_service,
                "blown": blown,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class UpdateFuseCommand(Command):
    """Request mutation of local Fuse state/configuration."""

    def __init__(
        self,
        *,
        fuse_id: str,
        name: str | None = None,
        rated_current_a: float | None = None,
        rated_voltage_v: float | None = None,
        interrupting_rating_ka: float | None = None,
        in_service: bool | None = None,
        blown: bool | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if all(
            value is None
            for value in (
                name,
                rated_current_a,
                rated_voltage_v,
                interrupting_rating_ka,
                in_service,
                blown,
            )
        ):
            raise ValueError(
                "UpdateFuseCommand requires at least one "
                "mutable Fuse field."
            )

        super().__init__(
            command_type=UPDATE_FUSE,
            payload={
                "fuse_id": fuse_id,
                "name": name,
                "rated_current_a": rated_current_a,
                "rated_voltage_v": rated_voltage_v,
                "interrupting_rating_ka": interrupting_rating_ka,
                "in_service": in_service,
                "blown": blown,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class DeleteFuseCommand(Command):
    """Request deletion of a Core Fuse."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=DELETE_FUSE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class BlowFuseCommand(Command):
    """Request operation of a Fuse element."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=BLOW_FUSE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class ResetFuseCommand(Command):
    """Request reset of a Fuse element."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=RESET_FUSE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class PutFuseInServiceCommand(Command):
    """Request placing a Fuse in service."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=PUT_FUSE_IN_SERVICE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


class TakeFuseOutOfServiceCommand(Command):
    """Request taking a Fuse out of service."""

    def __init__(
        self,
        *,
        fuse_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=TAKE_FUSE_OUT_OF_SERVICE,
            payload={"fuse_id": fuse_id},
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    # Bus
    "CREATE_BUS",
    "DELETE_BUS",
    "CreateBusCommand",
    "DeleteBusCommand",

    # Grid
    "CREATE_GRID",
    "DELETE_GRID",
    "UPDATE_GRID",
    "CreateGridCommand",
    "DeleteGridCommand",
    "UpdateGridCommand",

    # Generator
    "CREATE_GENERATOR",
    "UPDATE_GENERATOR",
    "DELETE_GENERATOR",
    "CreateGeneratorCommand",
    "UpdateGeneratorCommand",
    "DeleteGeneratorCommand",

    # Load
    "CREATE_LOAD",
    "DELETE_LOAD",
    "UPDATE_LOAD",
    "CreateLoadCommand",
    "DeleteLoadCommand",
    "UpdateLoadCommand",

    # Shunt
    "CREATE_SHUNT",
    "UPDATE_SHUNT",
    "DELETE_SHUNT",
    "CreateShuntCommand",
    "UpdateShuntCommand",
    "DeleteShuntCommand",

    # Line
    "CREATE_LINE",
    "DELETE_LINE",
    "CreateLineCommand",
    "DeleteLineCommand",

    # Transformer
    "CREATE_TRANSFORMER",
    "DELETE_TRANSFORMER",
    "CreateTransformerCommand",
    "DeleteTransformerCommand",

    # Branch
    "CREATE_BRANCH",
    "UPDATE_BRANCH",
    "DELETE_BRANCH",
    "CreateBranchCommand",
    "UpdateBranchCommand",
    "DeleteBranchCommand",

    # Cable
    "CREATE_CABLE",
    "UPDATE_CABLE",
    "DELETE_CABLE",
    "CreateCableCommand",
    "UpdateCableCommand",
    "DeleteCableCommand",

    # Switch
    "CREATE_SWITCH",
    "UPDATE_SWITCH",
    "DELETE_SWITCH",
    "OPEN_SWITCH",
    "CLOSE_SWITCH",
    "PUT_SWITCH_IN_SERVICE",
    "TAKE_SWITCH_OUT_OF_SERVICE",
    "CreateSwitchCommand",
    "UpdateSwitchCommand",
    "DeleteSwitchCommand",
    "OpenSwitchCommand",
    "CloseSwitchCommand",
    "PutSwitchInServiceCommand",
    "TakeSwitchOutOfServiceCommand",

    # Disconnector
    "CREATE_DISCONNECTOR",
    "UPDATE_DISCONNECTOR",
    "DELETE_DISCONNECTOR",
    "OPEN_DISCONNECTOR",
    "CLOSE_DISCONNECTOR",
    "PUT_DISCONNECTOR_IN_SERVICE",
    "TAKE_DISCONNECTOR_OUT_OF_SERVICE",
    "CreateDisconnectorCommand",
    "UpdateDisconnectorCommand",
    "DeleteDisconnectorCommand",
    "OpenDisconnectorCommand",
    "CloseDisconnectorCommand",
    "PutDisconnectorInServiceCommand",
    "TakeDisconnectorOutOfServiceCommand",

    # Fuse
    "CREATE_FUSE",
    "UPDATE_FUSE",
    "DELETE_FUSE",
    "BLOW_FUSE",
    "RESET_FUSE",
    "PUT_FUSE_IN_SERVICE",
    "TAKE_FUSE_OUT_OF_SERVICE",
    "CreateFuseCommand",
    "UpdateFuseCommand",
    "DeleteFuseCommand",
    "BlowFuseCommand",
    "ResetFuseCommand",
    "PutFuseInServiceCommand",
    "TakeFuseOutOfServiceCommand",
]
