# ============================================================
# File: core/application/commands/model_commands.py
# GridForge V2 — Model Commands
# Author: Subhendu Mishra
# ============================================================
"""
GridForge V2
============

Application commands for canonical electrical model operations.

Architectural role
------------------
These classes represent immutable Application intent.

They do NOT:

    - mutate Core models;
    - mutate Network;
    - manipulate terminals;
    - manipulate topology;
    - build Y-bus;
    - access Qt;
    - access graphics objects;
    - execute services.

Execution is performed by CommandManager through registered
Application handlers.

Current commands
----------------

    CreateBusCommand
    DeleteBusCommand
    CreateLineCommand
    DeleteLineCommand

Line endpoint policy
--------------------
CreateLineCommand carries endpoint identifiers rather than
Core model objects.

The corresponding handler resolves those identifiers against
the canonical Network before invoking ModelService.

This keeps commands transport-friendly and prevents Core/UI
objects from leaking into the command payload.

Python compatibility
---------------------
Python 3.10 / 3.11.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4

from ..command import Command


# =====================================================================
# COMMAND TYPES
# =====================================================================

CREATE_BUS = "model.create_bus"
DELETE_BUS = "model.delete_bus"

CREATE_LINE = "model.create_line"
DELETE_LINE = "model.delete_line"


# =====================================================================
# PAYLOAD HELPER
# =====================================================================

def _payload(**values: Any) -> MappingProxyType:
    """
    Create an immutable command payload.

    The command payload contains only Application-level values.
    """

    return MappingProxyType(values)


# =====================================================================
# CREATE BUS
# =====================================================================

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


# =====================================================================
# DELETE BUS
# =====================================================================

class DeleteBusCommand(Command):
    """
    Request removal of a canonical Core Bus.
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


# =====================================================================
# CREATE LINE
# =====================================================================

class CreateLineCommand(Command):
    """
    Request creation of a canonical Core Line.

    Endpoint identifiers refer to canonical Core endpoint objects.

    The command does not contain actual Bus, Terminal, or Line
    instances.
    """

    def __init__(
        self,
        *,
        line_id: str,
        endpoint_from_id: str,
        endpoint_to_id: str,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:

        super().__init__(
            command_type=CREATE_LINE,
            payload=_payload(
                line_id=line_id,
                endpoint_from_id=endpoint_from_id,
                endpoint_to_id=endpoint_to_id,
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


# =====================================================================
# DELETE LINE
# =====================================================================

class DeleteLineCommand(Command):
    """
    Request removal of a canonical Core Line.
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


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "CREATE_BUS",
    "DELETE_BUS",
    "CREATE_LINE",
    "DELETE_LINE",
    "CreateBusCommand",
    "DeleteBusCommand",
    "CreateLineCommand",
    "DeleteLineCommand",
]
