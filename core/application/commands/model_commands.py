# ============================================================
# File: core/application/commands/model_commands.py
# GridForge V2 — Model Commands
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Application model commands.

Commands carry immutable Application intent.

Commands do not:

    * contain Core model objects;
    * mutate Core;
    * mutate Network;
    * resolve endpoints;
    * manipulate terminals;
    * access Qt/UI;
    * perform engineering calculations.

Endpoint references
-------------------
Line and Transformer commands use EndpointReference.

EndpointReference is an Application value object identifying
either:

    * a canonical Bus; or
    * a terminal belonging to canonical equipment.

The command therefore transports endpoint identity without
embedding mutable Core state.

Resolution is performed by command handlers.

Author:
    Subhendu Mishra

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from types import MappingProxyType
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


# ============================================================
# PAYLOAD HELPER
# ============================================================

def _payload(
    **values: Any,
) -> MappingProxyType:
    """
    Build the immutable top-level command payload.

    Command is responsible for recursively freezing payload
    values.
    """

    return MappingProxyType(values)


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
            payload=_payload(
                bus_id=bus_id,
                name=name,
                bus_type=bus_type,
                voltage=voltage,
                angle=angle,
                p_spec=p_spec,
                q_spec=q_spec,
                v_setpoint=v_setpoint,
                q_min=q_min,
                q_max=q_max,
            ),
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
            payload=_payload(
                bus_id=bus_id,
            ),
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

    Endpoint references remain Application-layer immutable
    references.

    No Core endpoint object is stored in the command.
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
            payload=_payload(
                line_id=line_id,
                endpoint_from=endpoint_from,
                endpoint_to=endpoint_to,
                r=r,
                x=x,
                b=b,
                name=name,
                rate_mva=rate_mva,
            ),
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
            payload=_payload(
                line_id=line_id,
            ),
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

    Endpoint references remain Application-layer immutable
    references.
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
            payload=_payload(
                transformer_id=transformer_id,
                endpoint_from=endpoint_from,
                endpoint_to=endpoint_to,
                r=r,
                x=x,
                tap=tap,
                shift=shift,
                name=name,
                rate_mva=rate_mva,
            ),
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
            payload=_payload(
                transformer_id=transformer_id,
            ),
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
    "CreateBusCommand",
    "DeleteBusCommand",
    "CreateLineCommand",
    "DeleteLineCommand",
    "CreateTransformerCommand",
    "DeleteTransformerCommand",
]
