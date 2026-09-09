"""Application-layer compatibility facade for model mutation.

ModelService preserves the public application mutation API while routing each
owned domain to its dedicated model service. The facade contains no domain
mutation logic; it preserves valid public method signatures and forwards calls
to the owning service.
"""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.services.battery_model_service import BatteryModelService
from core.application.services.bus_model_service import BusModelService
from core.application.services.cable_model_service import CableModelService
from core.application.services.generator_model_service import GeneratorModelService
from core.application.services.grid_model_service import GridModelService
from core.application.services.line_model_service import LineModelService
from core.application.services.load_model_service import LoadModelService
from core.application.services.measurement_model_service import MeasurementModelService
from core.application.services.shunt_model_service import ShuntModelService
from core.application.services.switching_model_service import SwitchingModelService
from core.application.services.transformer_model_service import TransformerModelService
from core.application.transaction import Transaction
from core.model.breaker import Breaker
from core.model.bus import Bus
from core.model.transformer import Transformer
from core.network.network import Network


class ModelService(ModelServiceSupport):
    """Thin compatibility facade over domain-specific model services."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network
        self._bus_service = BusModelService(network)
        self._grid_service = GridModelService(network)
        self._generator_service = GeneratorModelService(network)
        self._load_service = LoadModelService(network)
        self._shunt_service = ShuntModelService(network)
        self._line_service = LineModelService(network)
        self._transformer_service = TransformerModelService(network)
        self._cable_service = CableModelService(network)
        self._switching_service = SwitchingModelService(network)
        self._measurement_service = MeasurementModelService(network)
        self._battery_service = BatteryModelService(network)

    @property
    def bus_service(self) -> BusModelService: return self._bus_service
    @property
    def grid_service(self) -> GridModelService: return self._grid_service
    @property
    def generator_service(self) -> GeneratorModelService: return self._generator_service
    @property
    def load_service(self) -> LoadModelService: return self._load_service
    @property
    def shunt_service(self) -> ShuntModelService: return self._shunt_service
    @property
    def measurement_service(self) -> MeasurementModelService: return self._measurement_service
    @property
    def battery_service(self) -> BatteryModelService: return self._battery_service
    @property
    def line_service(self) -> LineModelService: return self._line_service
    @property
    def transformer_service(self) -> TransformerModelService: return self._transformer_service
    @property
    def cable_service(self) -> CableModelService: return self._cable_service
    @property
    def switching_service(self) -> SwitchingModelService: return self._switching_service

    def create_bus(self, **kwargs): return self._bus_service.create_bus(**kwargs)
    def update_bus(self, **kwargs): return self._bus_service.update_bus(**kwargs)
    def delete_bus(self, **kwargs): return self._bus_service.delete_bus(**kwargs)
    def create_grid(self, **kwargs): return self._grid_service.create_grid(**kwargs)
    def update_grid(self, **kwargs): return self._grid_service.update_grid(**kwargs)
    def delete_grid(self, **kwargs): return self._grid_service.delete_grid(**kwargs)
    def create_generator(self, **kwargs): return self._generator_service.create_generator(**kwargs)
    def update_generator(self, **kwargs): return self._generator_service.update_generator(**kwargs)
    def delete_generator(self, **kwargs): return self._generator_service.delete_generator(**kwargs)
    def create_load(self, **kwargs): return self._load_service.create_load(**kwargs)
    def update_load(self, **kwargs): return self._load_service.update_load(**kwargs)
    def delete_load(self, **kwargs): return self._load_service.delete_load(**kwargs)
    def create_shunt(self, **kwargs): return self._shunt_service.create_shunt(**kwargs)
    def update_shunt(self, **kwargs): return self._shunt_service.update_shunt(**kwargs)
    def delete_shunt(self, **kwargs): return self._shunt_service.delete_shunt(**kwargs)
    def create_capacitor(self, **kwargs): return self._shunt_service.create_capacitor(**kwargs)
    def update_capacitor(self, **kwargs): return self._shunt_service.update_capacitor(**kwargs)
    def delete_capacitor(self, **kwargs): return self._shunt_service.delete_capacitor(**kwargs)
    def put_capacitor_in_service(self, **kwargs): return self._shunt_service.put_capacitor_in_service(**kwargs)
    def take_capacitor_out_of_service(self, **kwargs): return self._shunt_service.take_capacitor_out_of_service(**kwargs)
    def create_line(self, **kwargs): return self._line_service.create_line(**kwargs)
    def delete_line(self, **kwargs): return self._line_service.delete_line(**kwargs)
    def create_transformer(self, **kwargs): return self._transformer_service.create_transformer(**kwargs)
    def delete_transformer(self, **kwargs): return self._transformer_service.delete_transformer(**kwargs)
    def create_cable(self, **kwargs): return self._cable_service.create_cable(**kwargs)
    def update_cable(self, **kwargs): return self._cable_service.update_cable(**kwargs)
    def delete_cable(self, **kwargs): return self._cable_service.delete_cable(**kwargs)

    def create_switch(self, **kwargs): return self._switching_service.create_switch(**kwargs)
    def update_switch(self, **kwargs): return self._switching_service.update_switch(**kwargs)
    def delete_switch(self, **kwargs): return self._switching_service.delete_switch(**kwargs)
    def open_switch(self, **kwargs): return self._switching_service.open_switch(**kwargs)
    def close_switch(self, **kwargs): return self._switching_service.close_switch(**kwargs)
    def put_switch_in_service(self, **kwargs): return self._switching_service.put_switch_in_service(**kwargs)
    def take_switch_out_of_service(self, **kwargs): return self._switching_service.take_switch_out_of_service(**kwargs)

    def create_breaker(self, *, breaker_id: str, endpoint_from: Bus | None = None, endpoint_to: Bus | None = None, name: str = "", in_service: bool = True, closed: bool = True, failed: bool = False, voltage_kv: float | None = None, current_a: float | None = None, interrupting_ka: float | None = None, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.create_breaker(breaker_id=breaker_id, endpoint_from=endpoint_from, endpoint_to=endpoint_to, name=name, in_service=in_service, closed=closed, failed=failed, voltage_kv=voltage_kv, current_a=current_a, interrupting_ka=interrupting_ka, transaction=transaction)

    def update_breaker(self, *, breaker_id: str, name: str | None = None, in_service: bool | None = None, closed: bool | None = None, failed: bool | None = None, voltage_kv: float | None = None, current_a: float | None = None, interrupting_ka: float | None = None, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.update_breaker(breaker_id=breaker_id, name=name, in_service=in_service, closed=closed, failed=failed, voltage_kv=voltage_kv, current_a=current_a, interrupting_ka=interrupting_ka, transaction=transaction)

    def delete_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.delete_breaker(breaker_id=breaker_id, transaction=transaction)

    def open_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.open_breaker(breaker_id=breaker_id, transaction=transaction)

    def close_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.close_breaker(breaker_id=breaker_id, transaction=transaction)

    def put_breaker_in_service(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.put_breaker_in_service(breaker_id=breaker_id, transaction=transaction)

    def take_breaker_out_of_service(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.take_breaker_out_of_service(breaker_id=breaker_id, transaction=transaction)

    def trip_breaker(self, *, breaker_id: str, transaction: Transaction) -> ApplicationResult[Breaker]:
        return self._switching_service.trip_breaker(breaker_id=breaker_id, transaction=transaction)

    def create_disconnector(self, **kwargs): return self._switching_service.create_disconnector(**kwargs)
    def update_disconnector(self, **kwargs): return self._switching_service.update_disconnector(**kwargs)
    def delete_disconnector(self, **kwargs): return self._switching_service.delete_disconnector(**kwargs)
    def open_disconnector(self, **kwargs): return self._switching_service.open_disconnector(**kwargs)
    def close_disconnector(self, **kwargs): return self._switching_service.close_disconnector(**kwargs)
    def put_disconnector_in_service(self, **kwargs): return self._switching_service.put_disconnector_in_service(**kwargs)
    def take_disconnector_out_of_service(self, **kwargs): return self._switching_service.take_disconnector_out_of_service(**kwargs)
    def create_fuse(self, **kwargs): return self._switching_service.create_fuse(**kwargs)
    def update_fuse(self, **kwargs): return self._switching_service.update_fuse(**kwargs)
    def delete_fuse(self, **kwargs): return self._switching_service.delete_fuse(**kwargs)
    def blow_fuse(self, **kwargs): return self._switching_service.blow_fuse(**kwargs)
    def reset_fuse(self, **kwargs): return self._switching_service.reset_fuse(**kwargs)
    def put_fuse_in_service(self, **kwargs): return self._switching_service.put_fuse_in_service(**kwargs)
    def take_fuse_out_of_service(self, **kwargs): return self._switching_service.take_fuse_out_of_service(**kwargs)
    def create_battery(self, **kwargs): return self._battery_service.create_battery(**kwargs)
    def update_battery(self, **kwargs): return self._battery_service.update_battery(**kwargs)
    def delete_battery(self, **kwargs): return self._battery_service.delete_battery(**kwargs)
    def put_battery_in_service(self, **kwargs): return self._battery_service.put_battery_in_service(**kwargs)
    def take_battery_out_of_service(self, **kwargs): return self._battery_service.take_battery_out_of_service(**kwargs)


__all__ = ["ModelService"]
