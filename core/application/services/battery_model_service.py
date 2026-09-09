"""Application service boundary for Battery mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.battery import Battery
from core.model.bus import Bus
from core.model.terminal import Terminal
from core.network.network import Network


class BatteryModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Battery equipment."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_battery(self, *, battery_id: str, name: str = "", endpoint: Bus | Terminal | None = None, p_mw: float = 0.0, q_mvar: float = 0.0, max_charge_mw: float = 0.0, max_discharge_mw: float = 0.0, energy_capacity_mwh: float = 0.0, soc: float = 1.0, soc_min: float = 0.0, soc_max: float = 1.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Battery]:
        self._require_transaction(transaction)
        self._require_id(battery_id, "battery_id")
        if endpoint is not None: self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("battery", battery_id, "Battery")
        battery = Battery(id=battery_id, name=name, endpoint=endpoint, p_mw=p_mw, q_mvar=q_mvar, max_charge_mw=max_charge_mw, max_discharge_mw=max_discharge_mw, energy_capacity_mwh=energy_capacity_mwh, soc=soc, soc_min=soc_min, soc_max=soc_max, in_service=in_service)
        self._network.add_battery(battery)
        transaction.record_undo(lambda battery=battery: self._network.remove_battery(battery))
        return self._success(battery, "battery", battery_id, f"Battery created: {battery_id}")

    def update_battery(self, *, battery_id: str, name: str | None = None, p_mw: float | None = None, q_mvar: float | None = None, max_charge_mw: float | None = None, max_discharge_mw: float | None = None, energy_capacity_mwh: float | None = None, soc: float | None = None, soc_min: float | None = None, soc_max: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Battery]:
        self._require_transaction(transaction); self._require_id(battery_id, "battery_id")
        battery = self._get_required("battery", battery_id, "Battery"); self._require_type(battery, Battery, battery_id, "Battery")
        values = (name, p_mw, q_mvar, max_charge_mw, max_discharge_mw, energy_capacity_mwh, soc, soc_min, soc_max, in_service)
        if all(value is None for value in values):
            raise DomainError(code="NO_BATTERY_UPDATE", message="At least one mutable Battery property must be specified.", details={"battery_id": battery_id})
        old = {"name": battery.name, "p_mw": battery.p_mw, "q_mvar": battery.q_mvar, "max_charge_mw": battery.max_charge_mw, "max_discharge_mw": battery.max_discharge_mw, "energy_capacity_mwh": battery.energy_capacity_mwh, "soc": battery.soc, "soc_min": battery.soc_min, "soc_max": battery.soc_max, "in_service": battery.in_service}
        if name is not None: battery.name = name
        if p_mw is not None: battery.p_mw = p_mw
        if q_mvar is not None: battery.q_mvar = q_mvar
        if max_charge_mw is not None: battery.max_charge_mw = max_charge_mw
        if max_discharge_mw is not None: battery.max_discharge_mw = max_discharge_mw
        if energy_capacity_mwh is not None: battery.energy_capacity_mwh = energy_capacity_mwh
        if soc_min is not None: battery.soc_min = soc_min
        if soc_max is not None: battery.soc_max = soc_max
        if soc is not None: battery.soc = soc
        if in_service is not None: battery.in_service = in_service

        def restore() -> None:
            battery.name = old["name"]
            battery.max_charge_mw = old["max_charge_mw"]
            battery.max_discharge_mw = old["max_discharge_mw"]
            battery.p_mw = old["p_mw"]
            battery.q_mvar = old["q_mvar"]
            battery.energy_capacity_mwh = old["energy_capacity_mwh"]
            battery.soc_min = old["soc_min"]
            battery.soc_max = old["soc_max"]
            battery.soc = old["soc"]
            battery.in_service = old["in_service"]

        transaction.record_undo(restore)
        return self._success(battery, "battery", battery_id, f"Battery updated: {battery_id}")

    def delete_battery(self, *, battery_id: str, transaction: Transaction) -> ApplicationResult[Battery]:
        self._require_transaction(transaction); self._require_id(battery_id, "battery_id")
        battery = self._get_required("battery", battery_id, "Battery"); self._require_type(battery, Battery, battery_id, "Battery")
        self._network.remove_battery(battery)
        transaction.record_undo(lambda battery=battery: self._network.add_battery(battery))
        return self._success(battery, "battery", battery_id, f"Battery deleted: {battery_id}")

    def put_battery_in_service(self, *, battery_id: str, transaction: Transaction) -> ApplicationResult[Battery]:
        return self._set_battery_service(battery_id=battery_id, in_service=True, transaction=transaction)

    def take_battery_out_of_service(self, *, battery_id: str, transaction: Transaction) -> ApplicationResult[Battery]:
        return self._set_battery_service(battery_id=battery_id, in_service=False, transaction=transaction)

    def _set_battery_service(self, *, battery_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Battery]:
        self._require_transaction(transaction); self._require_id(battery_id, "battery_id")
        battery = self._get_required("battery", battery_id, "Battery"); self._require_type(battery, Battery, battery_id, "Battery")
        old = battery.in_service
        battery.in_service = in_service
        transaction.record_undo(lambda battery=battery, old=old: setattr(battery, "in_service", old))
        message = "put in service" if in_service else "taken out of service"
        return self._success(battery, "battery", battery_id, f"Battery {message}: {battery_id}")


__all__ = ["BatteryModelService"]