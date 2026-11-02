# ============================================================
# File: core/application/services/bus_model_service.py
# GridForge V2 — Bus Model Service
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from core.application.errors import DomainError
from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.network.network import Network


class BusModelService(ModelServiceSupport):
    """Application service owning Bus mutation within the model boundary."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

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
        self._ensure_not_exists("bus", bus_id, "Bus")

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
        transaction.record_undo(lambda bus=bus: self._network.remove_bus(bus))
        return self._success(bus, "bus", bus_id, f"Bus created: {bus_id}")

    def update_bus(
        self,
        *,
        bus_id: str,
        name: str | None = None,
        nominal_voltage_kv: float | None = None,
        voltage_pu: float | None = None,
        angle_deg: float | None = None,
        frequency_hz: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Bus]:
        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")
        bus = self._get_required("bus", bus_id, "Bus")
        self._require_type(bus, Bus, bus_id, "Bus")

        if all(value is None for value in (name, nominal_voltage_kv, voltage_pu, angle_deg, frequency_hz, in_service)):
            raise DomainError(
                code="NO_BUS_UPDATE",
                message="At least one mutable Bus property must be specified.",
                details={"bus_id": bus_id},
            )

        old = {
            "name": bus.name,
            "nominal_voltage_kv": bus.nominal_voltage_kv,
            "voltage_pu": bus.voltage_pu,
            "angle_deg": bus.angle_deg,
            "frequency_hz": bus.frequency_hz,
            "in_service": bus.in_service,
        }
        candidate = {
            "name": old["name"] if name is None else name,
            "nominal_voltage_kv": old["nominal_voltage_kv"] if nominal_voltage_kv is None else nominal_voltage_kv,
            "voltage_pu": old["voltage_pu"] if voltage_pu is None else voltage_pu,
            "angle_deg": old["angle_deg"] if angle_deg is None else angle_deg,
            "frequency_hz": old["frequency_hz"] if frequency_hz is None else frequency_hz,
            "in_service": old["in_service"] if in_service is None else in_service,
        }
        service_state_changed = (
            in_service is not None and in_service != old["in_service"]
        )

        def apply(state: dict[str, object]) -> None:
            bus.name = state["name"]
            bus.nominal_voltage_kv = bus._validate_non_negative(
                state["nominal_voltage_kv"], "nominal_voltage_kv"
            )
            bus.frequency_hz = bus._validate_positive(
                state["frequency_hz"], "frequency_hz"
            )
            bus.set_voltage(state["voltage_pu"], state["angle_deg"])
            bus.set_in_service(state["in_service"])
            bus.validate_parameters()

        try:
            apply(candidate)
        except BaseException:
            apply(old)
            raise

        if service_state_changed:
            self._network.invalidate_topology()

        def restore() -> None:
            apply(old)
            if service_state_changed:
                self._network.invalidate_topology()

        transaction.record_undo(restore)
        return self._success(bus, "bus", bus_id, f"Bus updated: {bus_id}")

    def delete_bus(self, *, bus_id: str, transaction: Transaction) -> ApplicationResult[Bus]:
        self._require_transaction(transaction)
        self._require_id(bus_id, "bus_id")
        bus = self._get_required("bus", bus_id, "Bus")
        self._require_type(bus, Bus, bus_id, "Bus")
        self._network.remove_bus(bus)
        transaction.record_undo(lambda bus=bus: self._network.add_bus(bus))
        return self._success(bus, "bus", bus_id, f"Bus deleted: {bus_id}")


__all__ = ["BusModelService"]
