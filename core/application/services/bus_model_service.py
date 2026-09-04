# ============================================================
# File: core/application/services/bus_model_service.py
# GridForge V2 — Bus Model Service Contract
# Author: Subhendu Mishra
# ============================================================

"""Canonical Bus creation contract layered over ModelService."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.network.network import Network

from .model_service import ModelService as _ModelService


class ModelService(_ModelService):
    """
    Bus-contract-correct ModelService facade.

    This preserves the existing ModelService implementation while making
    the Application Bus path explicit against the authoritative Core Bus
    constructor. Other model-service operations remain inherited.
    """

    def create_bus(
        self,
        *,
        bus_id: str,
        name: str | None = None,
        nominal_voltage_kv: float = 0.0,
        voltage_pu: float = 1.0,
        angle_deg: float = 0.0,
        frequency_hz: float = 50.0,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Bus]:
        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")

        self._ensure_not_exists(
            "bus",
            bus_id,
            "Bus",
        )

        bus = Bus(
            id=bus_id,
            name="" if name is None else name,
            nominal_voltage_kv=nominal_voltage_kv,
            voltage_pu=voltage_pu,
            angle_deg=angle_deg,
            frequency_hz=frequency_hz,
            in_service=in_service,
        )

        self._network.add_bus(bus)

        transaction.record_undo(
            lambda bus=bus: self._network.remove_bus(bus)
        )

        return self._success(
            bus,
            "bus",
            bus_id,
            f"Bus created: {bus_id}",
        )


__all__ = ["ModelService"]
