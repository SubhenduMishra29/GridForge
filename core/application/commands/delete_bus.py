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
Defines the headless Application command representing the intent
to remove a Bus from the assembled electrical Network.

Architecture
------------

    DeleteBusCommand
            |
            v
       ModelService
            |
            v
       Network.remove_bus()
            |
            v
           Core

Responsibilities
----------------
This command:

    * represents deletion intent;
    * carries the stable Bus identifier;
    * contains no UI state;
    * contains no Qt dependency;
    * contains no Network implementation details;
    * contains no topology mutation logic.

The command does NOT:

    * access Network collections directly;
    * manipulate bus_index;
    * manipulate topology;
    * manipulate Y-bus;
    * manipulate SLD objects;
    * perform engineering calculations.

Those responsibilities belong to the appropriate Application/Core
layers.

Python Compatibility
--------------------
GridForge V2 targets Python 3.10/3.11.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..command import Command


@dataclass(frozen=True)
class DeleteBusCommand(Command):
    """
    Application command requesting deletion of a Bus.

    Parameters
    ----------
    bus_id:
        Stable identifier of the canonical Core Bus to remove.

    Notes
    -----
    The command carries an identifier rather than a Bus object.

    This is deliberate.

    Application commands should represent user/application intent,
    while canonical Core objects remain owned by the Core Network.
    """

    bus_id: str

    @property
    def command_type(self) -> str:
        """
        Return the canonical Application command type.
        """
        return "delete_bus"


__all__ = [
    "DeleteBusCommand",
]
