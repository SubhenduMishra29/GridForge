# ============================================================
# File: core/application/commands/battery_commands.py
# GridForge V2 — Battery Command Contracts
# Author: Subhendu Mishra
# ============================================================

"""Immutable Application commands for Battery mutations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from ..command import Command
from core.model import EndpointReference

CREATE_BATTERY = "model.create_battery"
UPDATE_BATTERY = "model.update_battery"
DELETE_BATTERY = "model.delete_battery"
PUT_BATTERY_IN_SERVICE = "model.put_battery_in_service"
TAKE_BATTERY_OUT_OF_SERVICE = "model.take_battery_out_of_service"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


def _endpoint(value: EndpointReference | None) -> None:
    if value is not None and not isinstance(value, EndpointReference):
        raise TypeError("endpoint must be an EndpointReference or None.")


class CreateBatteryCommand(Command):
    def __init__(self, *, battery_id: str, name: str = "", endpoint: EndpointReference | None = None,
                 p_mw: float = 0.0, q_mvar: float = 0.0, max_charge_mw: float = 0.0,
                 max_discharge_mw: float = 0.0, energy_capacity_mwh: float = 0.0,
                 soc: float = 1.0, soc_min: float = 0.0, soc_max: float = 1.0,
                 in_service: bool = True, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint)
        super().__init__(**_command(CREATE_BATTERY, {
            "battery_id": battery_id, "name": name, "endpoint": endpoint, "p_mw": p_mw,
            "q_mvar": q_mvar, "max_charge_mw": max_charge_mw, "max_discharge_mw": max_discharge_mw,
            "energy_capacity_mwh": energy_capacity_mwh, "soc": soc, "soc_min": soc_min,
            "soc_max": soc_max, "in_service": in_service,
        }, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class UpdateBatteryCommand(Command):
    def __init__(self, *, battery_id: str, name: str | None = None, p_mw: float | None = None,
                 q_mvar: float | None = None, max_charge_mw: float | None = None,
                 max_discharge_mw: float | None = None, energy_capacity_mwh: float | None = None,
                 soc: float | None = None, soc_min: float | None = None, soc_max: float | None = None,
                 in_service: bool | None = None, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(value is None for value in (name, p_mw, q_mvar, max_charge_mw, max_discharge_mw,
                                           energy_capacity_mwh, soc, soc_min, soc_max, in_service)):
            raise ValueError("UpdateBatteryCommand requires at least one mutable field.")
        super().__init__(**_command(UPDATE_BATTERY, {
            "battery_id": battery_id, "name": name, "p_mw": p_mw, "q_mvar": q_mvar,
            "max_charge_mw": max_charge_mw, "max_discharge_mw": max_discharge_mw,
            "energy_capacity_mwh": energy_capacity_mwh, "soc": soc, "soc_min": soc_min,
            "soc_max": soc_max, "in_service": in_service,
        }, command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class DeleteBatteryCommand(Command):
    def __init__(self, *, battery_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(DELETE_BATTERY, {"battery_id": battery_id},
                                    command_id=command_id, correlation_id=correlation_id,
                                    causation_id=causation_id))


class PutBatteryInServiceCommand(Command):
    def __init__(self, *, battery_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(PUT_BATTERY_IN_SERVICE, {"battery_id": battery_id},
                                    command_id=command_id, correlation_id=correlation_id,
                                    causation_id=causation_id))


class TakeBatteryOutOfServiceCommand(Command):
    def __init__(self, *, battery_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(TAKE_BATTERY_OUT_OF_SERVICE, {"battery_id": battery_id},
                                    command_id=command_id, correlation_id=correlation_id,
                                    causation_id=causation_id))


__all__ = [
    "CREATE_BATTERY", "UPDATE_BATTERY", "DELETE_BATTERY",
    "PUT_BATTERY_IN_SERVICE", "TAKE_BATTERY_OUT_OF_SERVICE",
    "CreateBatteryCommand", "UpdateBatteryCommand", "DeleteBatteryCommand",
    "PutBatteryInServiceCommand", "TakeBatteryOutOfServiceCommand",
]
