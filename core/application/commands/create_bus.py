# ============================================================
# File: core/application/commands/create_bus.py
# GridForge V2 — Create Bus Application Command
# Author: Subhendu Mishra
# ============================================================

"""Canonical Application command for creating a Core Bus."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command

CREATE_BUS = "model.create_bus"


class CreateBusCommand(Command):
    """
    Application intent to create the authoritative Core Bus.

    Contract mirrors ``core.model.Bus``:
        bus_id
        name
        nominal_voltage_kv

    No study-specific bus classification or power-flow fields belong
    in this physical model creation command.
    """

    def __init__(
        self,
        *,
        bus_id: str,
        name: str = "",
        nominal_voltage_kv: float = 0.0,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        super().__init__(
            command_type=CREATE_BUS,
            payload={
                "bus_id": bus_id,
                "name": name,
                "nominal_voltage_kv": nominal_voltage_kv,
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


__all__ = ["CREATE_BUS", "CreateBusCommand"]
