# ============================================================
# File: core/application/commands/create_bus.py
# GridForge V2 — Create Bus Application Command
# ============================================================
"""
GridForge V2
============

Module:
    core.application.commands.create_bus

Purpose
-------
Defines the Application command used to request creation of a
canonical electrical Bus.

This command represents INTENT.

It does not construct or register the Core Bus itself.

Execution is performed by the Application service layer.

Architectural Flow
------------------

    Caller
      |
      v
    CreateBusCommand
      |
      v
    CommandManager
      |
      v
    create_bus_handler()
      |
      v
    ModelService.create_bus()
      |
      v
    core.model.Bus
      |
      v
    core.network.Network.add_bus()

Headless Boundary
-----------------
This module contains no dependency on:

    * PySide6;
    * PyQt;
    * Qt;
    * QGraphicsScene;
    * QGraphicsItem;
    * SLD;
    * Canvas;
    * UI controllers;
    * renderers.

The command may therefore be created and executed from:

    * UI;
    * plugins;
    * automation;
    * CLI;
    * batch processing.

Payload
-------
The command payload contains only Application-level data.

No UI object may be inserted into the payload.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from core.model import BusType

from ..command import Command
from ..context import ApplicationContext
from ..results import ApplicationResult
from ..services.model_service import ModelService


@dataclass(frozen=True)
class CreateBusCommand(Command):
    """
    Application command representing the intent to create a Bus.

    The command is immutable and contains no Core mutation logic.

    Parameters
    ----------
    bus_id:
        Identifier for the new Bus.

    name:
        Human-readable Bus name.

    bus_type:
        Canonical Core BusType.

    voltage:
        Initial voltage magnitude.

    angle:
        Initial voltage angle.

    p_spec:
        Specified active power.

    q_spec:
        Specified reactive power.

    v_setpoint:
        Optional voltage setpoint.

    q_min:
        Minimum reactive power.

    q_max:
        Maximum reactive power.
    """

    def __init__(
        self,
        *,
        bus_id: str,
        name: str = "",
        bus_type: BusType = BusType.PQ,
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
        payload: dict[str, Any] = {
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

        # Command is frozen, so all semantic input is stored in the
        # inherited immutable payload.
        #
        # The base Command creates command_id automatically when
        # none is supplied. A private construction path is avoided
        # here so Python 3.10/3.11 compatibility remains simple.

        if command_id is None:
            super().__init__(
                command_type="bus.create",
                payload=payload,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
        else:
            super().__init__(
                command_type="bus.create",
                payload=payload,
                command_id=command_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )


def create_bus_handler(
    command: Command,
    context: ApplicationContext,
) -> ApplicationResult:
    """
    Execute a CreateBusCommand through ModelService.

    This function is the Application command-handler boundary.

    It deliberately does not construct ``Bus`` directly.

    The handler:

        1. validates the command type;
        2. extracts command payload;
        3. delegates to ModelService;
        4. returns the ApplicationResult.

    Parameters
    ----------
    command:
        Application command dispatched by CommandManager.

    context:
        Headless ApplicationContext.

    Returns
    -------
    ApplicationResult
        Result produced by ModelService.
    """

    if not isinstance(command, CreateBusCommand):
        raise TypeError(
            "create_bus_handler requires CreateBusCommand."
        )

    service = ModelService(context)

    payload = command.payload

    return service.create_bus(
        bus_id=payload["bus_id"],
        name=payload["name"],
        bus_type=payload["bus_type"],
        voltage=payload["voltage"],
        angle=payload["angle"],
        p_spec=payload["p_spec"],
        q_spec=payload["q_spec"],
        v_setpoint=payload["v_setpoint"],
        q_min=payload["q_min"],
        q_max=payload["q_max"],
    )


__all__ = [
    "CreateBusCommand",
    "create_bus_handler",
]
