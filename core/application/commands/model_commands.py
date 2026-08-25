# ============================================================
# File: core/application/commands/model_commands.py
# GridForge V2 — Model Commands
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Application Model Commands
==========================================

Immutable commands representing model-level application intent.

Commands:

    CreateBusCommand
    DeleteBusCommand
    CreateLineCommand
    DeleteLineCommand
    CreateTransformerCommand
    DeleteTransformerCommand
    CreateLoadCommand
    DeleteLoadCommand
    UpdateLoadCommand

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

Endpoint references
-------------------

Line and Transformer commands use:

    EndpointReference

An endpoint can therefore be:

    Bus
        EndpointReference.bus(...)

or:

    Terminal
        EndpointReference.terminal(...)

The complete endpoint identity remains inside the immutable
EndpointReference.

Load commands
-------------

A Load is a single-terminal injection model.

Creation therefore carries only the Load's model/value data:

    load_id
    p
    q
    name
    in_service

Update carries only mutable Load state:

    load_id
    name
    p
    q
    in_service

The commands deliberately do not contain:

    * a Core Load object;
    * a Core Terminal object;
    * a Core Bus object;
    * resolved topology;
    * UI state.

Load connectivity is handled separately through the
application/topology command workflow.

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

CREATE_LINE = "model.create_line"
DELETE_LINE = "model.delete_line"

CREATE_TRANSFORMER = "model.create_transformer"
DELETE_TRANSFORMER = "model.delete_transformer"

CREATE_LOAD = "model.create_load"
DELETE_LOAD = "model.delete_load"
UPDATE_LOAD = "model.update_load"


# ============================================================
# CREATE BUS
# ============================================================

class CreateBusCommand(Command):
    """
    Request creation of a canonical Core Bus.
    """

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
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# DELETE BUS
# ============================================================

class DeleteBusCommand(Command):
    """
    Request deletion of a canonical Core Bus.
    """

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
            payload={
                "bus_id": bus_id,
            },
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# CREATE LINE
# ============================================================

class CreateLineCommand(Command):
    """
    Request creation of a canonical Core Line.

    endpoint_from and endpoint_to are complete immutable
    EndpointReference objects.

    They are intentionally not named *_id because an endpoint
    may be either:

        * a Bus; or
        * a Terminal.
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

        if not isinstance(
            endpoint_from,
            EndpointReference,
        ):
            raise TypeError(
                "endpoint_from must be an "
                "EndpointReference."
            )

        if not isinstance(
            endpoint_to,
            EndpointReference,
        ):
            raise TypeError(
                "endpoint_to must be an "
                "EndpointReference."
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
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# DELETE LINE
# ============================================================

class DeleteLineCommand(Command):
    """
    Request deletion of a canonical Core Line.
    """

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
            payload={
                "line_id": line_id,
            },
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# CREATE TRANSFORMER
# ============================================================

class CreateTransformerCommand(Command):
    """
    Request creation of a canonical Core Transformer.

    Endpoint references identify the actual connection
    endpoints without embedding Core objects.
    """

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

        if not isinstance(
            endpoint_from,
            EndpointReference,
        ):
            raise TypeError(
                "endpoint_from must be an "
                "EndpointReference."
            )

        if not isinstance(
            endpoint_to,
            EndpointReference,
        ):
            raise TypeError(
                "endpoint_to must be an "
                "EndpointReference."
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
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# DELETE TRANSFORMER
# ============================================================

class DeleteTransformerCommand(Command):
    """
    Request deletion of a canonical Core Transformer.
    """

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
            payload={
                "transformer_id": transformer_id,
            },
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# CREATE LOAD
# ============================================================

class CreateLoadCommand(Command):
    """
    Request creation of a canonical Core Load.

    A Load is initially created as a model object. The command
    does not embed a Core Terminal or Core Bus.

    Connectivity/topology is resolved by the appropriate
    application/topology workflow.
    """

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
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# DELETE LOAD
# ============================================================

class DeleteLoadCommand(Command):
    """
    Request deletion of a canonical Core Load.
    """

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
            payload={
                "load_id": load_id,
            },
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# UPDATE LOAD
# ============================================================

class UpdateLoadCommand(Command):
    """
    Request mutation of an existing canonical Core Load.

    Supported mutable Load state:

        name
        p
        q
        in_service

    ``None`` means that the corresponding field is not part
    of this update request.

    At least one mutable field must be supplied.

    This command does not:

        * contain a Core Load object;
        * contain a Core Terminal object;
        * contain a Core Bus object;
        * resolve topology;
        * connect or disconnect terminals;
        * perform engineering calculations;
        * mutate Core directly;
        * access UI state.

    Connectivity and topology changes belong to the topology
    command family.
    """

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

        if (
            name is None
            and p is None
            and q is None
            and in_service is None
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
            command_id=(
                command_id
                if command_id is not None
                else uuid4()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CREATE_BUS",
    "DELETE_BUS",
    "CREATE_LINE",
    "DELETE_LINE",
    "CREATE_TRANSFORMER",
    "DELETE_TRANSFORMER",
    "CREATE_LOAD",
    "DELETE_LOAD",
    "UPDATE_LOAD",
    "CreateBusCommand",
    "DeleteBusCommand",
    "CreateLineCommand",
    "DeleteLineCommand",
    "CreateTransformerCommand",
    "DeleteTransformerCommand",
    "CreateLoadCommand",
    "DeleteLoadCommand",
    "UpdateLoadCommand",
]
