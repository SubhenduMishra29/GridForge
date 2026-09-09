"""Application-layer compatibility facade for model mutation.

ModelService preserves the public application mutation API while routing each
owned domain to its dedicated model service. The facade contains no domain
mutation logic; it preserves the existing public method signatures and
forwards calls to the owning service.
"""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.services.battery_model_service import BatteryModelService
from core.application.services.branch_model_service import BranchModelService
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
from core.model.battery import Battery
from core.model.branch import Branch
from core.model.bus import Bus
from core.model.cable import Cable
from core.model.capacitor import Capacitor
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
        self._measurement_service = MeasurementModelService(network)
        self._battery_service = BatteryModelService(network)

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
    def measurement_service(self) -> MeasurementModelService:
        return self._measurement_service

    @property
    def battery_service(self) -> BatteryModelService:
        return self._battery_service

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

    def create_bus(self, *, bus_id: str, name: str | None = None, nominal_voltage_kv: float = 0.0, voltage_pu: float = 1.0, angle_deg: float = 0.0, frequency_hz: float = 50.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Bus]:
        return self._bus_service.create_bus(bus_id=bus_id, name=name, nominal_voltage_kv=nominal_voltage_kv, voltage_pu=voltage_pu, angle_deg=angle_deg, frequency_hz=frequency_hz, in_service=in_service, transaction=transaction)

    def update_bus(self, *, bus_id: str, name: str | None = None, nominal_voltage_kv: float | None = None, voltage_pu: float | None = None, angle_deg: float | None = None, frequency_hz: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Bus]:
        return self._bus_service.update_bus(bus_id=bus_id, name=name, nominal_voltage_kv=nominal_voltage_kv, voltage_pu=voltage_pu, angle_deg=angle_deg, frequency_hz=frequency_hz, in_service=in_service, transaction=transaction)

    def delete_bus(self, *, bus_id: str, transaction: Transaction) -> ApplicationResult[Bus]:
        return self._bus_service.delete_bus(bus_id=bus_id, transaction=transaction)

    def create_grid(self, *, grid_id: str, endpoint: Bus | Terminal | None = None, name: str | None = None, nominal_voltage_kv: float = 0.0, frequency_hz: float = 50.0, voltage_pu: float = 1.0, angle_deg: float = 0.0, p_mw: float = 0.0, q_mvar: float = 0.0, short_circuit_mva: float = 0.0, x_over_r: float = 0.0, z1_pu: complex = 0j, z2_pu: complex = 0j, z0_pu: complex = 0j, in_service: bool = True, grounded: bool = True, transaction: Transaction) -> ApplicationResult[Grid]:
        return self._grid_service.create_grid(grid_id=grid_id, endpoint=endpoint, name=name, nominal_voltage_kv=nominal_voltage_kv, frequency_hz=frequency_hz, voltage_pu=voltage_pu, angle_deg=angle_deg, p_mw=p_mw, q_mvar=q_mvar, short_circuit_mva=short_circuit_mva, x_over_r=x_over_r, z1_pu=z1_pu, z2_pu=z2_pu, z0_pu=z0_pu, in_service=in_service, grounded=grounded, transaction=transaction)

    def update_grid(self, *, grid_id: str, name: str | None = None, nominal_voltage_kv: float | None = None, frequency_hz: float | None = None, voltage_pu: float | None = None, angle_deg: float | None = None, p_mw: float | None = None, q_mvar: float | None = None, short_circuit_mva: float | None = None, x_over_r: float | None = None, z1_pu: complex | None = None, z2_pu: complex | None = None, z0_pu: complex | None = None, in_service: bool | None = None, grounded: bool | None = None, transaction: Transaction) -> ApplicationResult[Grid]:
        return self._grid_service.update_grid(grid_id=grid_id, name=name, nominal_voltage_kv=nominal_voltage_kv, frequency_hz=frequency_hz, voltage_pu=voltage_pu, angle_deg=angle_deg, p_mw=p_mw, q_mvar=q_mvar, short_circuit_mva=short_circuit_mva, x_over_r=x_over_r, z1_pu=z1_pu, z2_pu=z2_pu, z0_pu=z0_pu, in_service=in_service, grounded=grounded, transaction=transaction)

    def delete_grid(self, *, grid_id: str, transaction: Transaction) -> ApplicationResult[Grid]:
        return self._grid_service.delete_grid(grid_id=grid_id, transaction=transaction)

    def create_generator(self, *, generator_id: str, endpoint: Bus | Terminal | None = None, p: float = 0.0, q: float = 0.0, V_setpoint: float = 1.0, q_limits: tuple[float, float] = (-float("inf"), float("inf")), name: str = "", in_service: bool = True, transaction: Transaction) -> ApplicationResult[Generator]:
        return self._generator_service.create_generator(generator_id=generator_id, endpoint=endpoint, p=p, q=q, V_setpoint=V_setpoint, q_limits=q_limits, name=name, in_service=in_service, transaction=transaction)

    def update_generator(self, *, generator_id: str, name: str | None = None, p: float | None = None, q: float | None = None, V_setpoint: float | None = None, q_limits: tuple[float, float] | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Generator]:
        return self._generator_service.update_generator(generator_id=generator_id, name=name, p=p, q=q, V_setpoint=V_setpoint, q_limits=q_limits, in_service=in_service, transaction=transaction)

    def delete_generator(self, *, generator_id: str, transaction: Transaction) -> ApplicationResult[Generator]:
        return self._generator_service.delete_generator(generator_id=generator_id, transaction=transaction)

    def create_load(self, *, load_id: str, p: float = 0.0, q: float = 0.0, name: str | None = None, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Load]:
        return self._load_service.create_load(load_id=load_id, p=p, q=q, name=name, in_service=in_service, transaction=transaction)

    def update_load(self, *, load_id: str, name: str | None = None, p: float | None = None, q: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Load]:
        return self._load_service.update_load(load_id=load_id, name=name, p=p, q=q, in_service=in_service, transaction=transaction)

    def delete_load(self, *, load_id: str, transaction: Transaction) -> ApplicationResult[Load]:
        return self._load_service.delete_load(load_id=load_id, transaction=transaction)

    def create_shunt(self, *, shunt_id: str, name: str = "", endpoint: Bus | Terminal | None = None, g_pu: float = 0.0, b_pu: float = 0.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Shunt]:
        return self._shunt_service.create_shunt(shunt_id=shunt_id, name=name, endpoint=endpoint, g_pu=g_pu, b_pu=b_pu, in_service=in_service, transaction=transaction)

    def update_shunt(self, *, shunt_id: str, name: str | None = None, g_pu: float | None = None, b_pu: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Shunt]:
        return self._shunt_service.update_shunt(shunt_id=shunt_id, name=name, g_pu=g_pu, b_pu=b_pu, in_service=in_service, transaction=transaction)

    def delete_shunt(self, *, shunt_id: str, transaction: Transaction) -> ApplicationResult[Shunt]:
        return self._shunt_service.delete_shunt(shunt_id=shunt_id, transaction=transaction)

    def create_capacitor(self, *, capacitor_id: str, endpoint: Bus | Terminal | None = None, name: str = "", q_mvar: float = 0.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Capacitor]:
        return self._shunt_service.create_capacitor(capacitor_id=capacitor_id, endpoint=endpoint, name=name, q_mvar=q_mvar, in_service=in_service, transaction=transaction)

    def update_capacitor(self, *, capacitor_id: str, endpoint: Bus | Terminal | None = None, name: str | None = None, q_mvar: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Capacitor]:
        return self._shunt_service.update_capacitor(capacitor_id=capacitor_id, endpoint=endpoint, name=name, q_mvar=q_mvar, in_service=in_service, transaction=transaction)

    def delete_capacitor(self, *, capacitor_id: str, transaction: Transaction) -> ApplicationResult[Capacitor]:
        return self._shunt_service.delete_capacitor(capacitor_id=capacitor_id, transaction=transaction)

    def put_capacitor_in_service(self, *, capacitor_id: str, transaction: Transaction) -> ApplicationResult[Capacitor]:
        return self._shunt_service.put_capacitor_in_service(capacitor_id=capacitor_id, transaction=transaction)

    def take_capacitor_out_of_service(self, *, capacitor_id: str, transaction: Transaction) -> ApplicationResult[Capacitor]:
        return self._shunt_service.take_capacitor_out_of_service(capacitor_id=capacitor_id, transaction=transaction)

    def create_line(self, *, line_id: str, endpoint_from: Bus | Terminal, endpoint_to: Bus | Terminal, r: float = 0.0, x: float = 0.0, b: float = 0.0, name: str | None = None, rate_mva: float | None = None, transaction: Transaction) -> ApplicationResult[Line]:
        return self._line_service.create_line(line_id=line_id, endpoint_from=endpoint_from, endpoint_to=endpoint_to, r=r, x=x, b=b, name=name, rate_mva=rate_mva, transaction=transaction)

    def delete_line(self, *, line_id: str, transaction: Transaction) -> ApplicationResult[Line]:
        return self._line_service.delete_line(line_id=line_id, transaction=transaction)

    def create_transformer(self, *, transformer_id: str, endpoint_from: Bus | Terminal, endpoint_to: Bus | Terminal, r: float = 0.0, x: float = 0.0, tap: float = 1.0, shift: float = 0.0, name: str | None = None, rate_mva: float | None = None, transaction: Transaction) -> ApplicationResult[Transformer]:
        return self._transformer_service.create_transformer(transformer_id=transformer_id, endpoint_from=endpoint_from, endpoint_to=endpoint_to, r=r, x=x, tap=tap, shift=shift, name=name, rate_mva=rate_mva, transaction=transaction)

    def delete_transformer(self, *, transformer_id: str, transaction: Transaction) -> ApplicationResult[Transformer]:
        return self._transformer_service.delete_transformer(transformer_id=transformer_id, transaction=transaction)

    def create_branch(self, *, branch_id: str, endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None, r: float | None = None, x: float | None = None, b: float | None = None, name: str = "", rate_mva: float | None = None, tap: float = 1.0, shift: float = 0.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Branch]:
        return self._branch_service.create_branch(branch_id=branch_id, endpoint_from=endpoint_from, endpoint_to=endpoint_to, r=r, x=x, b=b, name=name, rate_mva=rate_mva, tap=tap, shift=shift, in_service=in_service, transaction=transaction)

    def update_branch(self, *, branch_id: str, name: str | None = None, r: float | None = None, x: float | None = None, b: float | None = None, rate_mva: float | None = None, tap: float | None = None, shift: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Branch]:
        return self._branch_service.update_branch(branch_id=branch_id, name=name, r=r, x=x, b=b, rate_mva=rate_mva, tap=tap, shift=shift, in_service=in_service, transaction=transaction)

    def delete_branch(self, *, branch_id: str, transaction: Transaction) -> ApplicationResult[Branch]:
        return self._branch_service.delete_branch(branch_id=branch_id, transaction=transaction)

    def create_cable(self, *, cable_id: str, endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None, name: str = "", length_km: float = 0.0, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, r1_ohm_per_km: float = 0.0, x1_ohm_per_km: float = 0.0, b1_us_per_km: float = 0.0, r0_ohm_per_km: float | None = None, x0_ohm_per_km: float | None = None, b0_us_per_km: float | None = None, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Cable]:
        return self._cable_service.create_cable(cable_id=cable_id, endpoint_from=endpoint_from, endpoint_to=endpoint_to, name=name, length_km=length_km, rated_voltage_kv=rated_voltage_kv, rated_current_a=rated_current_a, r1_ohm_per_km=r1_ohm_per_km, x1_ohm_per_km=x1_ohm_per_km, b1_us_per_km=b1_us_per_km, r0_ohm_per_km=r0_ohm_per_km, x0_ohm_per_km=x0_ohm_per_km, b0_us_per_km=b0_us_per_km, in_service=in_service, transaction=transaction)

    def update_cable(self, *, cable_id: str, name: str | None = None, length_km: float | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, r1_ohm_per_km: float | None = None, x1_ohm_per_km: float | None = None, b1_us_per_km: float | None = None, r0_ohm_per_km: float | None = None, x0_ohm_per_km: float | None = None, b0_us_per_km: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Cable]:
        return self._cable_service.update_cable(cable_id=cable_id, name=name, length_km=length_km, rated_voltage_kv=rated_voltage_kv, rated_current_a=rated_current_a, r1_ohm_per_km=r1_ohm_per_km, x1_ohm_per_km=x1_ohm_per_km, b1_us_per_km=b1_us_per_km, r0_ohm_per_km=r0_ohm_per_km, x0_ohm_per_km=x0_ohm_per_km, b0_us_per_km=b0_us_per_km, in_service=in_service, transaction=transaction)

    def delete_cable(self, *, cable_id: str, transaction: Transaction) -> ApplicationResult[Cable]:
        return self._cable_service.delete_cable(cable_id=cable_id, transaction=transaction)

    def create_switch(self, *, switch_id: str, name: str = "", endpoint_a: Bus | Terminal | None = None, endpoint_b: Bus | Terminal | None = None, closed: bool = False, in_service: bool = True, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.create_switch(switch_id=switch_id, name=name, endpoint_a=endpoint_a, endpoint_b=endpoint_b, closed=closed, in_service=in_service, normally_closed=normally_closed, rated_voltage_kv=rated_voltage_kv, rated_current_a=rated_current_a, transaction=transaction)

    def update_switch(self, *, switch_id: str, name: str | None = None, closed: bool | None = None, in_service: bool | None = None, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.update_switch(switch_id=switch_id, name=name, closed=closed, in_service=in_service, normally_closed=normally_closed, rated_voltage_kv=rated_voltage_kv, rated_current_a=rated_current_a, transaction=transaction)

    def delete_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.delete_switch(switch_id=switch_id, transaction=transaction)

    def open_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.open_switch(switch_id=switch_id, transaction=transaction)

    def close_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.close_switch(switch_id=switch_id, transaction=transaction)

    def put_switch_in_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.put_switch_in_service(switch_id=switch_id, transaction=transaction)

    def take_switch_out_of_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        return self._switching_service.take_switch_out_of_service(switch_id=switch_id, transaction=transaction)

    def create_disconnector(self, *, disconnector_id: str, voltage_kv: float, rated_current_a: float, endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None, operating_time: float = 1.0, closed: bool = True, in_service: bool = True, name: str = "", transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.create_disconnector(disconnector_id=disconnector_id, voltage_kv=voltage_kv, rated_current_a=rated_current_a, endpoint_from=endpoint_from, endpoint_to=endpoint_to, operating_time=operating_time, closed=closed, in_service=in_service, name=name, transaction=transaction)

    def update_disconnector(self, *, disconnector_id: str, voltage_kv: float | None = None, rated_current_a: float | None = None, operating_time: float | None = None, closed: bool | None = None, in_service: bool | None = None, name: str | None = None, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.update_disconnector(disconnector_id=disconnector_id, voltage_kv=voltage_kv, rated_current_a=rated_current_a, operating_time=operating_time, closed=closed, in_service=in_service, name=name, transaction=transaction)

    def delete_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.delete_disconnector(disconnector_id=disconnector_id, transaction=transaction)

    def open_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.open_disconnector(disconnector_id=disconnector_id, transaction=transaction)

    def close_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.close_disconnector(disconnector_id=disconnector_id, transaction=transaction)

    def put_disconnector_in_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.put_disconnector_in_service(disconnector_id=disconnector_id, transaction=transaction)

    def take_disconnector_out_of_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        return self._switching_service.take_disconnector_out_of_service(disconnector_id=disconnector_id, transaction=transaction)

    def create_fuse(self, *, fuse_id: str, name: str = "", rated_current_a: float = 1.0, rated_voltage_v: float = 1.0, interrupting_rating_ka: float = 0.0, in_service: bool = True, blown: bool = False, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.create_fuse(fuse_id=fuse_id, name=name, rated_current_a=rated_current_a, rated_voltage_v=rated_voltage_v, interrupting_rating_ka=interrupting_rating_ka, in_service=in_service, blown=blown, transaction=transaction)

    def update_fuse(self, *, fuse_id: str, name: str | None = None, rated_current_a: float | None = None, rated_voltage_v: float | None = None, interrupting_rating_ka: float | None = None, in_service: bool | None = None, blown: bool | None = None, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.update_fuse(fuse_id=fuse_id, name=name, rated_current_a=rated_current_a, rated_voltage_v=rated_voltage_v, interrupting_rating_ka=interrupting_rating_ka, in_service=in_service, blown=blown, transaction=transaction)

    def delete_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.delete_fuse(fuse_id=fuse_id, transaction=transaction)

    def blow_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.blow_fuse(fuse_id=fuse_id, transaction=transaction)

    def reset_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.reset_fuse(fuse_id=fuse_id, transaction=transaction)

    def put_fuse_in_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.put_fuse_in_service(fuse_id=fuse_id, transaction=transaction)

    def take_fuse_out_of_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        return self._switching_service.take_fuse_out_of_service(fuse_id=fuse_id, transaction=transaction)

    def create_battery(self, *, battery_id: str, name: str = "", endpoint: Bus | Terminal | None = None, p_mw: float = 0.0, q_mvar: float = 0.0, max_charge_mw: float = 0.0, max_discharge_mw: float = 0.0, energy_capacity_mwh: float = 0.0, soc: float = 1.0, soc_min: float = 0.0, soc_max: float = 1.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Battery]:
        return self._battery_service.create_battery(battery_id=battery_id, name=name, endpoint=endpoint, p_mw=p_mw, q_mvar=q_mvar, max_charge_mw=max_charge_mw, max_discharge_mw=max_discharge_mw, energy_capacity_mwh=energy_capacity_mwh, soc=soc, soc_min=soc_min, soc_max=soc_max, in_service=in_service, transaction=transaction)

    def update_battery(self, *, battery_id: str, name: str | None = None, p_mw: float | None = None, q_mvar: float | None = None, max_charge_mw: float | None = None, max_discharge_mw: float | None = None, energy_capacity_mwh: float | None = None, soc: float | None = None, soc_min: float | None = None, soc_max: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Battery]:
        return self._battery_service.update_battery(battery_id=battery_id, name=name, p_mw=p_mw, q_mvar=q_mvar, max_charge_mw=max_charge_mw, max_discharge_mw=max_discharge_mw, energy_capacity_mwh=energy_capacity_mwh, soc=soc, soc_min=soc_min, soc_max=soc_max, in_service=in_service, transaction=transaction)

    def delete_battery(self, *, battery_id: str, transaction: Transaction) -> ApplicationResult[Battery]:
        return self._battery_service.delete_battery(battery_id=battery_id, transaction=transaction)

    def put_battery_in_service(self, *, battery_id: str, transaction: Transaction) -> ApplicationResult[Battery]:
        return self._battery_service.put_battery_in_service(battery_id=battery_id, transaction=transaction)

    def take_battery_out_of_service(self, *, battery_id: str, transaction: Transaction) -> ApplicationResult[Battery]:
        return self._battery_service.take_battery_out_of_service(battery_id=battery_id, transaction=transaction)


__all__ = ["ModelService"]
