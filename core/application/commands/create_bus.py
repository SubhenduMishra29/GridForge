# ============================================================
# File: core/application/commands/create_bus.py
# GridForge V2 — Create Bus Application Command
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Create Bus Application Command
==============================================

Compatibility module for the canonical model CreateBusCommand.

The authoritative command contract mirrors the authoritative Core
Bus constructor:

    bus_id
    name
    nominal_voltage_kv

The command contains Application intent only. It does not construct,
register, or mutate a Core Bus.

Execution flow:

    CreateBusCommand
        -> CommandManager
        -> ModelCommandHandlers.create_bus()
        -> ModelService.create_bus()
        -> core.model.Bus
        -> core.network.Network.add_bus()

This module deliberately contains no UI, Qt, SLD, Canvas, renderer,
or QGraphics dependency.
"""

from __future__ import annotations

from uuid import UUID

from ..command import Command
from .model_commands import CREATE_BUS, CreateBusCommand


# Keep the dedicated module as a compatibility import surface while
# preserving one canonical command definition in model_commands.py.


def build_create_bus_command(
    *,
    bus_id: str,
    name: str = "",
    nominal_voltage_kv: float = 0.0,
    command_id: UUID | None = None,
    correlation_id: UUID | None = None,
    causation_id: UUID | None = None,
) -> CreateBusCommand:
    """Build the canonical CreateBusCommand."""

    return CreateBusCommand(
        bus_id=bus_id,
        name=name,
        nominal_voltage_kv=nominal_voltage_kv,
        command_id=command_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


__all__ = [
    "CREATE_BUS",
    "CreateBusCommand",
    "build_create_bus_command",
]
