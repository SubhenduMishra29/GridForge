# ============================================================
# File: core/application/commands/model_commands.py
# GridForge V2 — Headless Model Commands
# ============================================================
"""
GridForge V2
============

Module:
    core.application.commands.model_commands

Purpose
-------
Defines immutable Application commands for canonical electrical
model creation and removal.

Architectural flow
------------------

    UI / Plugin / Automation
              |
              v
       Model Command
              |
              v
       CommandManager
              |
              v
         ModelService
              |
              v
             Core

Command objects represent intent only.

They do NOT:

    * mutate Core;
    * mutate Network;
    * manipulate terminals;
    * manipulate topology;
    * build Y-bus;
    * access Qt;
    * access graphics objects;
    * own services;
    * own CommandManager.

Execution belongs to CommandManager handlers.

Current commands
----------------

    CreateBusCommand
    DeleteBusCommand

    CreateLineCommand
    DeleteLineCommand

The command payload contains Application-level input only.

Canonical Core objects are intentionally NOT stored in command
payloads for creation/deletion requests. Commands use stable IDs
where the operation is based on an already registered object.

Line creation is the exception in that its endpoints must be
resolved before the canonical Line can be constructed. The
command therefore carries endpoint identifiers, not Core objects.

The handler resolves those identifiers against the canonical
Application/Core Network before calling ModelService.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ..command import Command


# =====================================================================
# COMMAND TYPE CONSTANTS
# =====================================================================

CREATE_BUS = "model.create_bus"
DELETE_BUS = "model.delete_bus"

CREATE_LINE = "model.create_line"
DELETE_LINE = "model.delete_line"


# =====================================================================
# CREATE BUS
# =====================================================================

@dataclass(frozen=True)
class CreateBusCommand(Command):
    """
    Application intent to create a canonical Bus.

    The payload is kept in the base Command mapping because the
    Application command contract deliberately uses immutable,
    transport-friendly payloads.
    """

    command_type: str = CREATE_BUS

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
        payload = {
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
        }

        # Command is frozen, therefore object.__setattr__ is used
        # to construct the immutable base object explicitly.
        object.__setattr__(
            self,
            "command_type",
            CREATE_BUS,
        )
        object.__setattr__(
            self,
            "payload",
            payload,
        )

        from uuid import uuid4

        object.__setattr__(
            self,
            "command_id",
            command_id if command_id is not None else uuid4(),
        )

        object.__setattr__(
            self,
            "correlation_id",
            correlation_id,
        )

        object.__setattr__(
            self,
            "causation_id",
            causation_id,
        )

        Command.__post_init__(self)


# =====================================================================
# DELETE BUS
# =====================================================================

@dataclass(frozen=True)
class DeleteBusCommand(Command):
    """
    Application intent to delete a canonical Bus.

    Only the stable Bus ID is carried.

    The handler resolves the canonical Bus through the Network
    before invoking ModelService.delete_bus().
    """

    command_type: str = DELETE_BUS

    def __init__(
        self,
        *,
        bus_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        from uuid import uuid4

        object.__setattr__(
            self,
            "command_type",
            DELETE_BUS,
        )

        object.__setattr__(
            self,
            "payload",
            {
                "bus_id": bus_id,
            },
        )

        object.__setattr__(
            self,
            "command_id",
            command_id if command_id is not None else uuid4(),
        )

        object.__setattr__(
            self,
            "correlation_id",
            correlation_id,
        )

        object.__setattr__(
            self,
            "causation_id",
            causation_id,
        )

        Command.__post_init__(self)


# =====================================================================
# CREATE LINE
# =====================================================================

@dataclass(frozen=True)
class CreateLineCommand(Command):
    """
    Application intent to create a canonical Line.

    Endpoint references are carried as stable identifiers.

    The command never carries Qt objects or canonical model objects.

    Endpoint resolution is performed by the command handler against
    the canonical Application/Core Network.
    """

    command_type: str = CREATE_LINE

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
        from uuid import uuid4

        object.__setattr__(
            self,
            "command_type",
            CREATE_LINE,
        )

        object.__setattr__(
            self,
            "payload",
            {
                "line_id": line_id,
                "endpoint_from_id": endpoint_from_id,
                "endpoint_to_id": endpoint_to_id,
                "r": r,
                "x": x,
                "b": b,
                "name": name,
                "rate_mva": rate_mva,
            },
        )

        object.__setattr__(
            self,
            "command_id",
            command_id if command_id is not None else uuid4(),
        )

        object.__setattr__(
            self,
            "correlation_id",
            correlation_id,
        )

        object.__setattr__(
            self,
            "causation_id",
            causation_id,
        )

        Command.__post_init__(self)


# =====================================================================
# DELETE LINE
# =====================================================================

@dataclass(frozen=True)
class DeleteLineCommand(Command):
    """
    Application intent to delete a canonical Line.

    Only the stable Line ID is carried.

    The handler resolves the canonical Line and delegates deletion
    to ModelService.
    """

    command_type: str = DELETE_LINE

    def __init__(
        self,
        *,
        line_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        from uuid import uuid4

        object.__setattr__(
            self,
            "command_type",
            DELETE_LINE,
        )

        object.__setattr__(
            self,
            "payload",
            {
                "line_id": line_id,
            },
        )

        object.__setattr__(
            self,
            "command_id",
            command_id if command_id is not None else uuid4(),
        )

        object.__setattr__(
            self,
            "correlation_id",
            correlation_id,
        )

        object.__setattr__(
            self,
            "causation_id",
            causation_id,
        )

        Command.__post_init__(self)


# =====================================================================
# EXPORTS
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
