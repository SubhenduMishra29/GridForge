# ============================================================
# File: core/application/commands/delete_bus.py
# GridForge V2 — Delete Bus Application Command
# ============================================================
"""
GridForge V2
============

Module:
    core.application.commands.delete_bus

Purpose
-------
Defines the Application command used to request deletion of a
canonical electrical Bus.

This command represents INTENT.

It does not remove the Bus itself.

Execution is performed through:

    DeleteBusCommand
          |
          v
    CommandManager
          |
          v
    delete_bus_handler()
          |
          v
    ModelService.delete_bus()
          |
          v
    core.network.Network.remove_bus()

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

The command therefore remains usable from:

    * UI;
    * plugins;
    * automation;
    * CLI;
    * batch processing.

Payload
-------
The command payload contains only Application-level data.

No Core collection, Network instance, terminal object, or UI
object is stored in the command payload.

The stable Bus identifier is sufficient to identify the intended
canonical Core object.

Command Type
------------
The semantic command type is:

    "bus.delete"

This follows the existing CreateBusCommand convention:

    "bus.create"

Command Contract
----------------
The command conforms to the frozen Application Command contract:

    core.application.command.Command

The inherited immutable fields are preserved:

    * command_type;
    * payload;
    * command_id;
    * correlation_id;
    * causation_id.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from ..command import Command
from ..context import ApplicationContext
from ..results import ApplicationResult
from ..services.model_service import ModelService


class DeleteBusCommand(Command):
    """
    Application command representing the intent to delete a Bus.

    Parameters
    ----------
    bus_id:
        Stable identifier of the canonical Core Bus.

    command_id:
        Optional unique command instance identifier.

    correlation_id:
        Optional identifier associating this command with a larger
        Application operation.

    causation_id:
        Optional identifier identifying the command/event that
        caused this command.

    Notes
    -----
    This class intentionally follows the same construction pattern
    as CreateBusCommand.

    It does not store the Core Bus object.

    The canonical Bus remains owned by Network.
    """

    def __init__(
        self,
        *,
        bus_id: str,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        """
        Construct an immutable DeleteBusCommand.
        """

        payload: dict[str, Any] = {
            "bus_id": bus_id,
        }

        if command_id is None:
            super().__init__(
                command_type="bus.delete",
                payload=payload,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

        else:
            super().__init__(
                command_type="bus.delete",
                payload=payload,
                command_id=command_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )


def delete_bus_handler(
    command: Command,
    context: ApplicationContext,
) -> ApplicationResult:
    """
    Execute a DeleteBusCommand through ModelService.

    This function is the Application command-handler boundary.

    It deliberately does not:

        * access Network collections;
        * search topology;
        * manipulate bus_index;
        * remove the Bus directly;
        * manipulate terminal references.

    The handler:

        1. validates the command type;
        2. extracts the stable Bus identifier;
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

    Raises
    ------
    TypeError
        If the supplied command is not DeleteBusCommand.
    """

    if not isinstance(command, DeleteBusCommand):
        raise TypeError(
            "delete_bus_handler requires DeleteBusCommand."
        )

    service = ModelService(context)

    payload = command.payload

    return service.delete_bus(
        bus_id=payload["bus_id"],
    )


__all__ = [
    "DeleteBusCommand",
    "delete_bus_handler",
]
