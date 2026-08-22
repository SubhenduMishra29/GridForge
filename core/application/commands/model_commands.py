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
         Command Handler
              |
              v
         ModelService
              |
              v
             Core

Command objects represent Application intent only.

They do NOT:

    * mutate Core;
    * mutate Network;
    * manipulate terminals;
    * manipulate topology;
    * build Y-bus;
    * access Qt;
    * access graphics objects;
    * own Application services;
    * own CommandManager.

The command manager dispatches the command to a registered
handler. The handler performs Application-level orchestration.

Current commands
----------------

    CreateBusCommand
    DeleteBusCommand
    CreateLineCommand
    DeleteLineCommand

Line endpoint rule
------------------
CreateLineCommand carries endpoint identifiers, not Core model
objects.

The handler resolves those identifiers against the canonical
Application/Core Network before calling ModelService.

This preserves the headless Application boundary.

Immutability
------------
Command payloads use MappingProxyType so callers cannot mutate
the command payload after construction.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import Any, Mapping
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
# INTERNAL PAYLOAD HELPER
# =====================================================================

def _immutable_payload(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    """
    Convert an Application command payload into an immutable mapping.

    MappingProxyType prevents mutation of the mapping itself.

    The values are Application-level values only and must not contain
    UI objects or graphics objects.
    """

    return MappingProxyType(dict(payload))


# =====================================================================
# CREATE BUS
# =====================================================================

class CreateBusCommand(Command):
    """
    Application intent to create a canonical Core Bus.

    Parameters
    ----------
    bus_id:
        Stable Bus identifier.

    name:
        Human-readable Bus name.

    bus_type:
        BusType value expected by ModelService.

    voltage:
        Initial voltage magnitude.

    angle:
        Initial voltage angle.

    p_spec:
        Active-power specification.

    q_spec:
        Reactive-power specification.

    v_setpoint:
        Optional voltage setpoint.

    q_min:
        Minimum reactive-power limit.

    q_max:
        Maximum reactive-power limit.

    The command itself does not construct the Core Bus.
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
            payload=_immutable_payload(
                {
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
            ),
            command_id=(
                command_id
                if command_id is not None
                else Command.__dataclass_fields__["command_id"]
                .default_factory()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# =====================================================================
# DELETE BUS
# =====================================================================

class DeleteBusCommand(Command):
    """
    Application intent to remove a canonical Core Bus.

    Only the stable Bus identifier is carried.

    The handler resolves the canonical Bus through the Network and
    delegates removal to ModelService.
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
            payload=_immutable_payload(
                {
                    "bus_id": bus_id,
                }
            ),
            command_id=(
                command_id
                if command_id is not None
                else Command.__dataclass_fields__["command_id"]
                .default_factory()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# =====================================================================
# CREATE LINE
# =====================================================================

class CreateLineCommand(Command):
    """
    Application intent to create a canonical Core Line.

    Endpoint references are stable identifiers.

    The command does not contain:

        * Bus objects;
        * Terminal objects;
        * Line objects;
        * Qt objects;
        * QGraphicsItems.

    The handler resolves endpoint identifiers against the canonical
    Network before invoking ModelService.create_line().
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
            payload=_immutable_payload(
                {
                    "line_id": line_id,
                    "endpoint_from_id": endpoint_from_id,
                    "endpoint_to_id": endpoint_to_id,
                    "r": r,
                    "x": x,
                    "b": b,
                    "name": name,
                    "rate_mva": rate_mva,
                }
            ),
            command_id=(
                command_id
                if command_id is not None
                else Command.__dataclass_fields__["command_id"]
                .default_factory()
            ),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


# =====================================================================
# DELETE LINE
# =====================================================================

class DeleteLineCommand(Command):
    """
    Application intent to remove a canonical Core Line.

    Only the stable Line identifier is carried.

    The handler resolves the canonical Line and delegates removal
    to ModelService.delete_line().
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
            payload=_immutable_payload(
                {
                    "line_id": line_id,
                }
            ),
            command_id=(
                command_id
                if command_id is not None
                else Command.__dataclass_fields__["command_id"]
                .default_factory()
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
