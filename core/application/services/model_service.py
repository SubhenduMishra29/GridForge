"""Application-layer compatibility facade for model mutation.

ModelService preserves the public application mutation API while routing each
owned domain to its dedicated model service. The facade contains no domain
mutation logic.
"""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.services.branch_model_service import BranchModelService
from core.application.services.bus_model_service import BusModelService
from core.application.services.cable_model_service import CableModelService
from core.application.services.generator_model_service import GeneratorModelService
from core.application.services.grid_model_service import GridModelService
from core.application.services.line_model_service import LineModelService
from core.application.services.load_model_service import LoadModelService
from core.application.services.shunt_model_service import ShuntModelService
from core.application.services.switching_model_service import SwitchingModelService
from core.application.services.transformer_model_service import TransformerModelService
from core.application.transaction import Transaction
from core.model.branch import Branch
from core.model.bus import Bus
from core.model.cable import Cable
from core.model.disconnector import Disconnector
from core.model.fuse import Fuse
from core.model.generator import Generator
from core.model.grid import Grid
from core.model.line import Line
from core.model.load import Load
from core.model.shunt import Shunt
from core.model.switch import Switch
from core.model.terminal import Terminal
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
        self._branch_service = BranchModelService(network)
        self._cable_service = CableModelService(network)
        self._switching_service = SwitchingModelService(network)

    @property
    def bus_service(self) -> BusModelService:
        return self._bus_service

    @property
    def grid_service(self) -> GridModelService:
        return self._grid_service

    @property
    def generator_service(self) -> GeneratorModelService:
        return self._generator_service

    @property
    def load_service(self) -> LoadModelService:
        return self._load_service

    @property
    def shunt_service(self) -> ShuntModelService:
        return self._shunt_service

    @property
    def line_service(self) -> LineModelService:
        return self._line_service

    @property
    def transformer_service(self) -> TransformerModelService:
        return self._transformer_service

    @property
    def branch_service(self) -> BranchModelService:
        return self._branch_service

    @property
    def cable_service(self) -> CableModelService:
        return self._cable_service

    @property
    def switching_service(self) -> SwitchingModelService:
        return self._switching_service

    # The following compatibility methods intentionally preserve the existing
    # public signatures while delegating all mutation to the owning service.
    def create_bus(self, **kwargs) -> ApplicationResult[Bus]: return self._bus_service.create_bus(**kwargs)
    def update_bus(self, **kwargs) -> ApplicationResult[Bus]: return self._bus_service.update_bus(**kwargs)
    def delete_bus(self, **kwargs) -> ApplicationResult[Bus]: return self._bus_service.delete_bus(**kwargs)
    def create_grid(self, **kwargs) -> ApplicationResult[Grid]: return self._grid_service.create_grid(**kwargs)
    def update_grid(self, **kwargs) -> ApplicationResult[Grid]: return self._grid_service.update_grid(**kwargs)
    def delete_grid(self, **kwargs) -> ApplicationResult[Grid]: return self._grid_service.delete_grid(**kwargs)
    def create_generator(self, **kwargs) -> ApplicationResult[Generator]: return self._generator_service.create_generator(**kwargs)
    def update_generator(self, **kwargs) -> ApplicationResult[Generator]: return self._generator_service.update_generator(**kwargs)
    def delete_generator(self, **kwargs) -> ApplicationResult[Generator]: return self._generator_service.delete_generator(**kwargs)
    def create_load(self, **kwargs) -> ApplicationResult[Load]: return self._load_service.create_load(**kwargs)
    def update_load(self, **kwargs) -> ApplicationResult[Load]: return self._load_service.update_load(**kwargs)
    def delete_load(self, **kwargs) -> ApplicationResult[Load]: return self._load_service.delete_load(**kwargs)
    def create_shunt(self, **kwargs) -> ApplicationResult[Shunt]: return self._shunt_service.create_shunt(**kwargs)
    def update_shunt(self, **kwargs) -> ApplicationResult[Shunt]: return self._shunt_service.update_shunt(**kwargs)
    def delete_shunt(self, **kwargs) -> ApplicationResult[Shunt]: return self._shunt_service.delete_shunt(**kwargs)
    def create_line(self, **kwargs) -> ApplicationResult[Line]: return self._line_service.create_line(**kwargs)
    def delete_line(self, **kwargs) -> ApplicationResult[Line]: return self._line_service.delete_line(**kwargs)
    def create_transformer(self, **kwargs) -> ApplicationResult[Transformer]: return self._transformer_service.create_transformer(**kwargs)
    def delete_transformer(self, **kwargs) -> ApplicationResult[Transformer]: return self._transformer_service.delete_transformer(**kwargs)
    def create_branch(self, **kwargs) -> ApplicationResult[Branch]: return self._branch_service.create_branch(**kwargs)
    def update_branch(self, **kwargs) -> ApplicationResult[Branch]: return self._branch_service.update_branch(**kwargs)
    def delete_branch(self, **kwargs) -> ApplicationResult[Branch]: return self._branch_service.delete_branch(**kwargs)
    def create_cable(self, **kwargs) -> ApplicationResult[Cable]: return self._cable_service.create_cable(**kwargs)
    def update_cable(self, **kwargs) -> ApplicationResult[Cable]: return self._cable_service.update_cable(**kwargs)
    def delete_cable(self, **kwargs) -> ApplicationResult[Cable]: return self._cable_service.delete_cable(**kwargs)

    def create_switch(self, *, switch_id: str, name: str = "", endpoint_a: Bus | Terminal | None = None, endpoint_b: Bus | Terminal | None = None, closed: bool = False, in_service: bool = True, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.create_switch(switch_id=switch_id, name=name, endpoint_a=endpoint_a, endpoint_b=endpoint_b, closed=closed, in_service=in_service, normally_closed=normally_closed, rated_voltage_kv=rated_voltage_kv, rated_current_a=rated_current_a, transaction=transaction)

    def update_switch(self, *, switch_id: str, name: str | None = None, closed: bool | None = None, in_service: bool | None = None, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.update_switch(switch_id=switch_id, name=name, closed=closed, in_service=in_service, normally_closed=normally_closed, rated_voltage_kv=rated_voltage_kv, rated_current_a=rated_current_a, transaction=transaction)

    def delete_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.delete_switch(switch_id=switch_id, transaction=transaction)

    def open_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]: return self._switching_service.open_switch(switch_id=switch_id, transaction=transaction)
    def close_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]: return self._switching_service.close_switch(switch_id=switch_id, transaction=transaction)
    def put_switch_in_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]: return self._switching_service.put_switch_in_service(switch_id=switch_id, transaction=transaction)
    def take_switch_out_of_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]: return self._switching_service.take_switch_out_of_service(switch_id=switch_id, transaction=transaction)

    def create_disconnector(self, *, disconnector_id: str, voltage_kv: float, rated_current_a: float, endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None, operating_time: float = 1.0, closed: bool = True, in_service: bool = True, name: str = "", transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.create_disconnector(disconnector_id=disconnector_id, voltage_kv=voltage_kv, rated_current_a=rated_current_a, endpoint_from=endpoint_from, endpoint_to=endpoint_to, operating_time=operating_time, closed=closed, in_service=in_service, name=name, transaction=transaction)

    def update_disconnector(self, *, disconnector_id: str, voltage_kv: float | None = None, rated_current_a: float | None = None, operating_time: float | None = None, closed: bool | None = None, in_service: bool | None = None, name: str | None = None, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.update_disconnector(disconnector_id=disconnector_id, voltage_kv=voltage_kv, rated_current_a=rated_current_a, operating_time=operating_time, closed=closed, in_service=in_service, name=name, transaction=transaction)

    def delete_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]: return self._switching_service.delete_disconnector(disconnector_id=disconnector_id, transaction=transaction)
    def open_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]: return self._switching_service.open_disconnector(disconnector_id=disconnector_id, transaction=transaction)
    def close_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]: return self._switching_service.close_disconnector(disconnector_id=disconnector_id, transaction=transaction)
    def put_disconnector_in_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]: return self._switching_service.put_disconnector_in_service(disconnector_id=disconnector_id, transaction=transaction)
    def take_disconnector_out_of_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]: return self._switching_service.take_disconnector_out_of_service(disconnector_id=disconnector_id, transaction=transaction)

    def create_fuse(self, *, fuse_id: str, name: str = "", rated_current_a: float = 1.0, rated_voltage_v: float = 1.0, interrupting_rating_ka: float = 0.0, in_service: bool = True, blown: bool = False, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.create_fuse(fuse_id=fuse_id, name=name, rated_current_a=rated_current_a, rated_voltage_v=rated_voltage_v, interrupting_rating_ka=interrupting_rating_ka, in_service=in_service, blown=blown, transaction=transaction)

    def update_fuse(self, *, fuse_id: str, name: str | None = None, rated_current_a: float | None = None, rated_voltage_v: float | None = None, interrupting_rating_ka: float | None = None, in_service: bool | None = None, blown: bool | None = None, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.update_fuse(fuse_id=fuse_id, name=name, rated_current_a=rated_current_a, rated_voltage_v=rated_voltage_v, interrupting_rating_ka=interrupting_rating_ka, in_service=in_service, blown=blown, transaction=transaction)

    def delete_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]: return self._switching_service.delete_fuse(fuse_id=fuse_id, transaction=transaction)
    def blow_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]: return self._switching_service.blow_fuse(fuse_id=fuse_id, transaction=transaction)
    def reset_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]: return self._switching_service.reset_fuse(fuse_id=fuse_id, transaction=transaction)
    def put_fuse_in_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]: return self._switching_service.put_fuse_in_service(fuse_id=fuse_id, transaction=transaction)
    def take_fuse_out_of_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]: return self._switching_service.take_fuse_out_of_service(fuse_id=fuse_id, transaction=transaction)


__all__ = ["ModelService"]
