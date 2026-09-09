# ============================================================
# File: core/application/services/model_service.py
# GridForge V2 — Application Model Service
# Author: Subhendu Mishra
# ============================================================

"""Application-layer compatibility facade for model mutation.

ModelService preserves the public application mutation API while
routing each domain to its owning model service. Network remains the
authority for canonical membership and Transaction remains the
authority for inverse operations.
"""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.services.bus_model_service import BusModelService
from core.application.services.grid_model_service import GridModelService
from core.application.services.generator_model_service import GeneratorModelService
from core.application.transaction import Transaction
from core.errors import DomainError
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

    @property
    def bus_service(self) -> BusModelService:
        return self._bus_service

    @property
    def grid_service(self) -> GridModelService:
        return self._grid_service

    @property
    def generator_service(self) -> GeneratorModelService:
        return self._generator_service

    # ============================================================
    # BUS — compatibility facade
    # ============================================================

    def create_bus(self, *, bus_id: str, name: str | None = None, nominal_voltage_kv: float = 0.0, voltage_pu: float = 1.0, angle_deg: float = 0.0, frequency_hz: float = 50.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Bus]:
        return self._bus_service.create_bus(bus_id=bus_id, name=name, nominal_voltage_kv=nominal_voltage_kv, voltage_pu=voltage_pu, angle_deg=angle_deg, frequency_hz=frequency_hz, in_service=in_service, transaction=transaction)

    def update_bus(self, *, bus_id: str, name: str | None = None, nominal_voltage_kv: float | None = None, voltage_pu: float | None = None, angle_deg: float | None = None, frequency_hz: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Bus]:
        return self._bus_service.update_bus(bus_id=bus_id, name=name, nominal_voltage_kv=nominal_voltage_kv, voltage_pu=voltage_pu, angle_deg=angle_deg, frequency_hz=frequency_hz, in_service=in_service, transaction=transaction)

    def delete_bus(self, *, bus_id: str, transaction: Transaction) -> ApplicationResult[Bus]:
        return self._bus_service.delete_bus(bus_id=bus_id, transaction=transaction)

    # ============================================================
    # GRID — compatibility facade
    # ============================================================

    def create_grid(self, *, grid_id: str, endpoint: Bus | Terminal | None = None, name: str | None = None, nominal_voltage_kv: float = 0.0, frequency_hz: float = 50.0, voltage_pu: float = 1.0, angle_deg: float = 0.0, p_mw: float = 0.0, q_mvar: float = 0.0, short_circuit_mva: float = 0.0, x_over_r: float = 0.0, z1_pu: complex = 0j, z2_pu: complex = 0j, z0_pu: complex = 0j, in_service: bool = True, grounded: bool = True, transaction: Transaction) -> ApplicationResult[Grid]:
        return self._grid_service.create_grid(grid_id=grid_id, endpoint=endpoint, name=name, nominal_voltage_kv=nominal_voltage_kv, frequency_hz=frequency_hz, voltage_pu=voltage_pu, angle_deg=angle_deg, p_mw=p_mw, q_mvar=q_mvar, short_circuit_mva=short_circuit_mva, x_over_r=x_over_r, z1_pu=z1_pu, z2_pu=z2_pu, z0_pu=z0_pu, in_service=in_service, grounded=grounded, transaction=transaction)

    def update_grid(self, *, grid_id: str, name: str | None = None, nominal_voltage_kv: float | None = None, frequency_hz: float | None = None, voltage_pu: float | None = None, angle_deg: float | None = None, p_mw: float | None = None, q_mvar: float | None = None, short_circuit_mva: float | None = None, x_over_r: float | None = None, z1_pu: complex | None = None, z2_pu: complex | None = None, z0_pu: complex | None = None, in_service: bool | None = None, grounded: bool | None = None, transaction: Transaction) -> ApplicationResult[Grid]:
        return self._grid_service.update_grid(grid_id=grid_id, name=name, nominal_voltage_kv=nominal_voltage_kv, frequency_hz=frequency_hz, voltage_pu=voltage_pu, angle_deg=angle_deg, p_mw=p_mw, q_mvar=q_mvar, short_circuit_mva=short_circuit_mva, x_over_r=x_over_r, z1_pu=z1_pu, z2_pu=z2_pu, z0_pu=z0_pu, in_service=in_service, grounded=grounded, transaction=transaction)

    def delete_grid(self, *, grid_id: str, transaction: Transaction) -> ApplicationResult[Grid]:
        return self._grid_service.delete_grid(grid_id=grid_id, transaction=transaction)

    # ============================================================
    # GENERATOR — compatibility facade
    # ============================================================

    def create_generator(self, *, generator_id: str, endpoint: Bus | Terminal | None = None, p: float = 0.0, q: float = 0.0, V_setpoint: float = 1.0, q_limits: tuple[float, float] = (-float("inf"), float("inf")), name: str = "", in_service: bool = True, transaction: Transaction) -> ApplicationResult[Generator]:
        return self._generator_service.create_generator(generator_id=generator_id, endpoint=endpoint, p=p, q=q, V_setpoint=V_setpoint, q_limits=q_limits, name=name, in_service=in_service, transaction=transaction)

    def update_generator(self, *, generator_id: str, name: str | None = None, p: float | None = None, q: float | None = None, V_setpoint: float | None = None, q_limits: tuple[float, float] | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Generator]:
        return self._generator_service.update_generator(generator_id=generator_id, name=name, p=p, q=q, V_setpoint=V_setpoint, q_limits=q_limits, in_service=in_service, transaction=transaction)

    def delete_generator(self, *, generator_id: str, transaction: Transaction) -> ApplicationResult[Generator]:
        return self._generator_service.delete_generator(generator_id=generator_id, transaction=transaction)

    # ============================================================
    # LOAD / SHUNT
    # ============================================================

    def create_load(self, *, load_id: str, p: float = 0.0, q: float = 0.0, name: str | None = None, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Load]:
        self._require_transaction(transaction); self._require_id(load_id,"load_id"); self._ensure_not_exists("load",load_id,"Load"); load=Load(id=load_id,p=p,q=q,name="" if name is None else name,in_service=in_service); self._network.add_load(load); transaction.record_undo(lambda load=load:self._network.remove_load(load)); return self._success(load,"load",load_id,f"Load created: {load_id}")
    def update_load(self, *, load_id: str, name: str | None = None, p: float | None = None, q: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Load]:
        self._require_transaction(transaction); self._require_id(load_id,"load_id"); load=self._get_required("load",load_id,"Load"); self._require_type(load,Load,load_id,"Load")
        if all(v is None for v in (name,p,q,in_service)): raise DomainError(code="NO_LOAD_UPDATE",message="At least one mutable Load property must be specified.",details={"load_id":load_id})
        old={"name":load.name,"p":load.p,"q":load.q,"in_service":load.in_service}
        if name is not None: load.name=name
        if p is not None: load.p=p
        if q is not None: load.q=q
        if in_service is not None: load.set_in_service(in_service)
        def restore(): load.name=old["name"]; load.p=old["p"]; load.q=old["q"]; load.set_in_service(old["in_service"])
        transaction.record_undo(restore); return self._success(load,"load",load_id,f"Load updated: {load_id}")
    def delete_load(self, *, load_id: str, transaction: Transaction) -> ApplicationResult[Load]:
        self._require_transaction(transaction); self._require_id(load_id,"load_id"); load=self._get_required("load",load_id,"Load"); self._require_type(load,Load,load_id,"Load"); self._network.remove_load(load); transaction.record_undo(lambda load=load:self._network.add_load(load)); return self._success(load,"load",load_id,f"Load deleted: {load_id}")

    def create_shunt(self, *, shunt_id: str, name: str = "", endpoint: Bus | Terminal | None = None, g_pu: float = 0.0, b_pu: float = 0.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Shunt]:
        self._require_transaction(transaction); self._require_id(shunt_id,"shunt_id");
        if endpoint is not None: self._validate_endpoint(endpoint,"endpoint")
        self._ensure_not_exists("shunt",shunt_id,"Shunt"); shunt=Shunt(id=shunt_id,name=name,endpoint=endpoint,g_pu=g_pu,b_pu=b_pu,in_service=in_service); self._network.add_shunt(shunt); transaction.record_undo(lambda shunt=shunt:self._network.remove_shunt(shunt)); return self._success(shunt,"shunt",shunt_id,f"Shunt created: {shunt_id}")
    def update_shunt(self, *, shunt_id: str, name: str | None = None, g_pu: float | None = None, b_pu: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Shunt]:
        self._require_transaction(transaction); self._require_id(shunt_id,"shunt_id"); shunt=self._get_required("shunt",shunt_id,"Shunt"); self._require_type(shunt,Shunt,shunt_id,"Shunt")
        if all(v is None for v in (name,g_pu,b_pu,in_service)): raise DomainError(code="NO_SHUNT_UPDATE",message="At least one mutable Shunt property must be specified.",details={"shunt_id":shunt_id})
        old={"name":shunt.name,"g_pu":shunt.g_pu,"b_pu":shunt.b_pu,"in_service":shunt.in_service}
        if name is not None: shunt.name=name
        if g_pu is not None: shunt.g_pu=g_pu
        if b_pu is not None: shunt.b_pu=b_pu
        if in_service is not None: shunt.set_in_service(in_service)
        def restore(): shunt.name=old["name"];shunt.g_pu=old["g_pu"];shunt.b_pu=old["b_pu"];shunt.set_in_service(old["in_service"])
        transaction.record_undo(restore);return self._success(shunt,"shunt",shunt_id,f"Shunt updated: {shunt_id}")
    def delete_shunt(self, *, shunt_id: str, transaction: Transaction) -> ApplicationResult[Shunt]:
        self._require_transaction(transaction); self._require_id(shunt_id,"shunt_id"); shunt=self._get_required("shunt",shunt_id,"Shunt"); self._require_type(shunt,Shunt,shunt_id,"Shunt"); self._network.remove_shunt(shunt); transaction.record_undo(lambda shunt=shunt:self._network.add_shunt(shunt)); return self._success(shunt,"shunt",shunt_id,f"Shunt deleted: {shunt_id}")

    # ============================================================
    # LINE / TRANSFORMER / BRANCH / CABLE
    # ============================================================

    def create_line(self, *, line_id: str, endpoint_from: Bus | Terminal, endpoint_to: Bus | Terminal, r: float = 0.0, x: float = 0.0, b: float = 0.0, name: str | None = None, rate_mva: float | None = None, transaction: Transaction) -> ApplicationResult[Line]:
        self._require_transaction(transaction);self._require_id(line_id,"line_id");self._validate_endpoint(endpoint_from,"endpoint_from");self._validate_endpoint(endpoint_to,"endpoint_to");self._require_distinct_endpoints(endpoint_from,endpoint_to,"INVALID_LINE_ENDPOINTS","Line",line_id);self._ensure_not_exists("line",line_id,"Line");line=Line(id=line_id,endpoint_from=endpoint_from,endpoint_to=endpoint_to,r=r,x=x,b=b,name="" if name is None else name,rate_mva=rate_mva);self._network.add_line(line);transaction.record_undo(lambda line=line:self._network.remove_line(line));return self._success(line,"line",line_id,f"Line created: {line_id}")
    def delete_line(self, *, line_id: str, transaction: Transaction) -> ApplicationResult[Line]:
        self._require_transaction(transaction);self._require_id(line_id,"line_id");line=self._get_required("line",line_id,"Line");self._require_type(line,Line,line_id,"Line");self._network.remove_line(line);transaction.record_undo(lambda line=line:self._network.add_line(line));return self._success(line,"line",line_id,f"Line deleted: {line_id}")
    def create_transformer(self, *, transformer_id: str, endpoint_from: Bus | Terminal, endpoint_to: Bus | Terminal, r: float = 0.0, x: float = 0.0, tap: float = 1.0, shift: float = 0.0, name: str | None = None, rate_mva: float | None = None, transaction: Transaction) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction);self._require_id(transformer_id,"transformer_id");self._validate_endpoint(endpoint_from,"endpoint_from");self._validate_endpoint(endpoint_to,"endpoint_to");self._require_distinct_endpoints(endpoint_from,endpoint_to,"INVALID_TRANSFORMER_ENDPOINTS","Transformer",transformer_id);self._ensure_not_exists("transformer",transformer_id,"Transformer");transformer=Transformer(id=transformer_id,endpoint_from=endpoint_from,endpoint_to=endpoint_to,r=r,x=x,tap=tap,shift=shift,name="" if name is None else name,rate_mva=rate_mva);self._network.add_transformer(transformer);transaction.record_undo(lambda transformer=transformer:self._network.remove_transformer(transformer));return self._success(transformer,"transformer",transformer_id,f"Transformer created: {transformer_id}")
    def delete_transformer(self, *, transformer_id: str, transaction: Transaction) -> ApplicationResult[Transformer]:
        self._require_transaction(transaction);self._require_id(transformer_id,"transformer_id");transformer=self._get_required("transformer",transformer_id,"Transformer");self._require_type(transformer,Transformer,transformer_id,"Transformer");self._network.remove_transformer(transformer);transaction.record_undo(lambda transformer=transformer:self._network.add_transformer(transformer));return self._success(transformer,"transformer",transformer_id,f"Transformer deleted: {transformer_id}")
    def create_branch(self, *, branch_id: str, endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None, r: float | None = None, x: float | None = None, b: float | None = None, name: str = "", rate_mva: float | None = None, tap: float = 1.0, shift: float = 0.0, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Branch]:
        self._require_transaction(transaction);self._require_id(branch_id,"branch_id");
        if endpoint_from is not None:self._validate_endpoint(endpoint_from,"endpoint_from")
        if endpoint_to is not None:self._validate_endpoint(endpoint_to,"endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:self._require_distinct_endpoints(endpoint_from,endpoint_to,"INVALID_BRANCH_ENDPOINTS","Branch",branch_id)
        self._ensure_not_exists("branch",branch_id,"Branch");branch=Branch(id=branch_id,endpoint_from=endpoint_from,endpoint_to=endpoint_to,r=r,x=x,b=b,name=name,rate_mva=rate_mva,tap=tap,shift=shift,in_service=in_service);self._network.add_branch(branch);transaction.record_undo(lambda branch=branch:self._network.remove_branch(branch));return self._success(branch,"branch",branch_id,f"Branch created: {branch_id}")
    def update_branch(self, *, branch_id: str, name: str | None = None, r: float | None = None, x: float | None = None, b: float | None = None, rate_mva: float | None = None, tap: float | None = None, shift: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Branch]:
        self._require_transaction(transaction);self._require_id(branch_id,"branch_id");branch=self._get_required("branch",branch_id,"Branch");self._require_type(branch,Branch,branch_id,"Branch")
        if all(v is None for v in (name,r,x,b,rate_mva,tap,shift,in_service)):raise DomainError(code="NO_BRANCH_UPDATE",message="At least one mutable Branch property must be specified.",details={"branch_id":branch_id})
        old={"name":branch.name,"r":branch.r,"x":branch.x,"b":branch.b,"rate_mva":branch.rate_mva,"tap":branch.tap,"shift":branch.shift,"in_service":branch.in_service}
        if name is not None:branch.name=name
        if r is not None:branch.r=r
        if x is not None:branch.x=x
        if b is not None:branch.b=b
        if rate_mva is not None:branch.rate_mva=rate_mva
        if tap is not None:branch.tap=tap
        if shift is not None:branch.shift=shift
        if in_service is not None:branch.set_in_service(in_service)
        def restore(): branch.name=old["name"];branch.r=old["r"];branch.x=old["x"];branch.b=old["b"];branch.rate_mva=old["rate_mva"];branch.tap=old["tap"];branch.shift=old["shift"];branch.set_in_service(old["in_service"])
        transaction.record_undo(restore);return self._success(branch,"branch",branch_id,f"Branch updated: {branch_id}")
    def delete_branch(self, *, branch_id: str, transaction: Transaction) -> ApplicationResult[Branch]:
        self._require_transaction(transaction);self._require_id(branch_id,"branch_id");branch=self._get_required("branch",branch_id,"Branch");self._require_type(branch,Branch,branch_id,"Branch");self._network.remove_branch(branch);transaction.record_undo(lambda branch=branch:self._network.add_branch(branch));return self._success(branch,"branch",branch_id,f"Branch deleted: {branch_id}")
    def create_cable(self, *, cable_id: str, endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None, name: str = "", length_km: float = 0.0, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, r1_ohm_per_km: float = 0.0, x1_ohm_per_km: float = 0.0, b1_us_per_km: float = 0.0, r0_ohm_per_km: float | None = None, x0_ohm_per_km: float | None = None, b0_us_per_km: float | None = None, in_service: bool = True, transaction: Transaction) -> ApplicationResult[Cable]:
        self._require_transaction(transaction);self._require_id(cable_id,"cable_id")
        if endpoint_from is not None:self._validate_endpoint(endpoint_from,"endpoint_from")
        if endpoint_to is not None:self._validate_endpoint(endpoint_to,"endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:self._require_distinct_endpoints(endpoint_from,endpoint_to,"INVALID_CABLE_ENDPOINTS","Cable",cable_id)
        self._ensure_not_exists("cable",cable_id,"Cable");cable=Cable(id=cable_id,endpoint_from=endpoint_from,endpoint_to=endpoint_to,name=name,length_km=length_km,rated_voltage_kv=rated_voltage_kv,rated_current_a=rated_current_a,r1_ohm_per_km=r1_ohm_per_km,x1_ohm_per_km=x1_ohm_per_km,b1_us_per_km=b1_us_per_km,r0_ohm_per_km=r0_ohm_per_km,x0_ohm_per_km=x0_ohm_per_km,b0_us_per_km=b0_us_per_km,in_service=in_service);self._network.add_cable(cable);transaction.record_undo(lambda cable=cable:self._network.remove_cable(cable));return self._success(cable,"cable",cable_id,f"Cable created: {cable_id}")
    def update_cable(self, *, cable_id: str, name: str | None = None, length_km: float | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, r1_ohm_per_km: float | None = None, x1_ohm_per_km: float | None = None, b1_us_per_km: float | None = None, r0_ohm_per_km: float | None = None, x0_ohm_per_km: float | None = None, b0_us_per_km: float | None = None, in_service: bool | None = None, transaction: Transaction) -> ApplicationResult[Cable]:
        self._require_transaction(transaction);self._require_id(cable_id,"cable_id");cable=self._get_required("cable",cable_id,"Cable");self._require_type(cable,Cable,cable_id,"Cable")
        if all(v is None for v in (name,length_km,rated_voltage_kv,rated_current_a,r1_ohm_per_km,x1_ohm_per_km,b1_us_per_km,r0_ohm_per_km,x0_ohm_per_km,b0_us_per_km,in_service)):raise DomainError(code="NO_CABLE_UPDATE",message="At least one mutable Cable property must be specified.",details={"cable_id":cable_id})
        old={k:getattr(cable,k) for k in ("name","length_km","rated_voltage_kv","rated_current_a","r1_ohm_per_km","x1_ohm_per_km","b1_us_per_km","r0_ohm_per_km","x0_ohm_per_km","b0_us_per_km","in_service")}
        for key,value in (("name",name),("length_km",length_km),("rated_voltage_kv",rated_voltage_kv),("rated_current_a",rated_current_a),("r1_ohm_per_km",r1_ohm_per_km),("x1_ohm_per_km",x1_ohm_per_km),("b1_us_per_km",b1_us_per_km),("r0_ohm_per_km",r0_ohm_per_km),("x0_ohm_per_km",x0_ohm_per_km),("b0_us_per_km",b0_us_per_km)):
            if value is not None:setattr(cable,key,value)
        if in_service is not None:cable.set_in_service(in_service)
        transaction.record_undo(lambda cable=cable,old=old:[setattr(cable,k,v) for k,v in old.items()]);return self._success(cable,"cable",cable_id,f"Cable updated: {cable_id}")
    def delete_cable(self, *, cable_id: str, transaction: Transaction) -> ApplicationResult[Cable]:
        self._require_transaction(transaction);self._require_id(cable_id,"cable_id");cable=self._get_required("cable",cable_id,"Cable");self._require_type(cable,Cable,cable_id,"Cable");self._network.remove_cable(cable);transaction.record_undo(lambda cable=cable:self._network.add_cable(cable));return self._success(cable,"cable",cable_id,f"Cable deleted: {cable_id}")

    # ============================================================
    # SWITCHING — retained here until the dedicated extraction
    # ============================================================

    def create_switch(self, *, switch_id: str, name: str = "", endpoint_a: Bus | Terminal | None = None, endpoint_b: Bus | Terminal | None = None, closed: bool = False, in_service: bool = True, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction);self._require_id(switch_id,"switch_id")
        if endpoint_a is not None:self._validate_endpoint(endpoint_a,"endpoint_a")
        if endpoint_b is not None:self._validate_endpoint(endpoint_b,"endpoint_b")
        if endpoint_a is not None and endpoint_b is not None:self._require_distinct_endpoints(endpoint_a,endpoint_b,"INVALID_SWITCH_ENDPOINTS","Switch",switch_id)
        self._ensure_not_exists("switch",switch_id,"Switch");switch=Switch(id=switch_id,name=name,endpoint_a=endpoint_a,endpoint_b=endpoint_b,closed=closed,in_service=in_service,normally_closed=normally_closed,rated_voltage_kv=rated_voltage_kv,rated_current_a=rated_current_a);self._network.add_switch(switch);transaction.record_undo(lambda switch=switch:self._network.remove_switch(switch));return self._success(switch,"switch",switch_id,f"Switch created: {switch_id}")
    def update_switch(self, *, switch_id: str, name: str | None = None, closed: bool | None = None, in_service: bool | None = None, normally_closed: bool | None = None, rated_voltage_kv: float | None = None, rated_current_a: float | None = None, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction);self._require_id(switch_id,"switch_id");switch=self._get_required("switch",switch_id,"Switch");self._require_type(switch,Switch,switch_id,"Switch")
        if all(v is None for v in (name,closed,in_service,normally_closed,rated_voltage_kv,rated_current_a)):raise DomainError(code="NO_SWITCH_UPDATE",message="At least one mutable Switch property must be specified.",details={"switch_id":switch_id})
        old={"name":switch.name,"closed":switch.closed,"in_service":switch.in_service,"normally_closed":switch.normally_closed,"rated_voltage_kv":switch.rated_voltage_kv,"rated_current_a":switch.rated_current_a}
        if name is not None:switch.name=name
        if closed is not None:switch.set_closed(closed)
        if in_service is not None:switch.set_in_service(in_service)
        if normally_closed is not None:switch.set_normally_closed(normally_closed)
        if rated_voltage_kv is not None:switch.rated_voltage_kv=rated_voltage_kv
        if rated_current_a is not None:switch.rated_current_a=rated_current_a
        def restore(): switch.name=old["name"];switch.set_closed(old["closed"]);switch.set_in_service(old["in_service"]);switch.set_normally_closed(old["normally_closed"]);switch.rated_voltage_kv=old["rated_voltage_kv"];switch.rated_current_a=old["rated_current_a"]
        transaction.record_undo(restore);return self._success(switch,"switch",switch_id,f"Switch updated: {switch_id}")
    def delete_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction);self._require_id(switch_id,"switch_id");switch=self._get_required("switch",switch_id,"Switch");self._require_type(switch,Switch,switch_id,"Switch");self._network.remove_switch(switch);transaction.record_undo(lambda switch=switch:self._network.add_switch(switch));return self._success(switch,"switch",switch_id,f"Switch deleted: {switch_id}")
    def open_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:return self._set_switch_closed(switch_id=switch_id,closed=False,transaction=transaction)
    def close_switch(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:return self._set_switch_closed(switch_id=switch_id,closed=True,transaction=transaction)
    def put_switch_in_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:return self._set_switch_service(switch_id=switch_id,in_service=True,transaction=transaction)
    def take_switch_out_of_service(self, *, switch_id: str, transaction: Transaction) -> ApplicationResult[Switch]:return self._set_switch_service(switch_id=switch_id,in_service=False,transaction=transaction)
    def _set_switch_closed(self, *, switch_id: str, closed: bool, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction);self._require_id(switch_id,"switch_id");switch=self._get_required("switch",switch_id,"Switch");self._require_type(switch,Switch,switch_id,"Switch");old=switch.closed;switch.set_closed(closed);transaction.record_undo(lambda switch=switch,old=old:switch.set_closed(old));return self._success(switch,"switch",switch_id,f"Switch {'closed' if closed else 'opened'}: {switch_id}")
    def _set_switch_service(self, *, switch_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Switch]:
        self._require_transaction(transaction);self._require_id(switch_id,"switch_id");switch=self._get_required("switch",switch_id,"Switch");self._require_type(switch,Switch,switch_id,"Switch");old=switch.in_service;switch.set_in_service(in_service);transaction.record_undo(lambda switch=switch,old=old:switch.set_in_service(old));return self._success(switch,"switch",switch_id,f"Switch {'put in service' if in_service else 'taken out of service'}: {switch_id}")

    def create_disconnector(self, *, disconnector_id: str, voltage_kv: float, rated_current_a: float, endpoint_from: Bus | Terminal | None = None, endpoint_to: Bus | Terminal | None = None, operating_time: float = 1.0, closed: bool = True, in_service: bool = True, name: str = "", transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction);self._require_id(disconnector_id,"disconnector_id")
        if endpoint_from is not None:self._validate_endpoint(endpoint_from,"endpoint_from")
        if endpoint_to is not None:self._validate_endpoint(endpoint_to,"endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:self._require_distinct_endpoints(endpoint_from,endpoint_to,"INVALID_DISCONNECTOR_ENDPOINTS","Disconnector",disconnector_id)
        self._ensure_not_exists("disconnector",disconnector_id,"Disconnector");disconnector=Disconnector(id=disconnector_id,voltage_kv=voltage_kv,rated_current_a=rated_current_a,endpoint_from=endpoint_from,endpoint_to=endpoint_to,operating_time=operating_time,closed=closed,in_service=in_service,name=name);self._network.add_disconnector(disconnector);transaction.record_undo(lambda disconnector=disconnector:self._network.remove_disconnector(disconnector));return self._success(disconnector,"disconnector",disconnector_id,f"Disconnector created: {disconnector_id}")
    def update_disconnector(self, *, disconnector_id: str, voltage_kv: float | None = None, rated_current_a: float | None = None, operating_time: float | None = None, closed: bool | None = None, in_service: bool | None = None, name: str | None = None, transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction);self._require_id(disconnector_id,"disconnector_id");disconnector=self._get_required("disconnector",disconnector_id,"Disconnector");self._require_type(disconnector,Disconnector,disconnector_id,"Disconnector")
        if all(v is None for v in (voltage_kv,rated_current_a,operating_time,closed,in_service,name)):raise DomainError(code="NO_DISCONNECTOR_UPDATE",message="At least one mutable Disconnector property must be specified.",details={"disconnector_id":disconnector_id})
        old={"voltage_kv":disconnector.voltage_kv,"rated_current_a":disconnector.rated_current_a,"operating_time":disconnector.operating_time,"closed":disconnector.closed,"in_service":disconnector.in_service,"name":disconnector.name}
        for k,v in (("voltage_kv",voltage_kv),("rated_current_a",rated_current_a),("operating_time",operating_time),("name",name)):
            if v is not None:setattr(disconnector,k,v)
        if closed is not None:disconnector.set_closed(closed)
        if in_service is not None:disconnector.set_in_service(in_service)
        def restore(): disconnector.voltage_kv=old["voltage_kv"];disconnector.rated_current_a=old["rated_current_a"];disconnector.operating_time=old["operating_time"];disconnector.set_closed(old["closed"]);disconnector.set_in_service(old["in_service"]);disconnector.name=old["name"]
        transaction.record_undo(restore);return self._success(disconnector,"disconnector",disconnector_id,f"Disconnector updated: {disconnector_id}")
    def delete_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction);self._require_id(disconnector_id,"disconnector_id");disconnector=self._get_required("disconnector",disconnector_id,"Disconnector");self._require_type(disconnector,Disconnector,disconnector_id,"Disconnector");self._network.remove_disconnector(disconnector);transaction.record_undo(lambda disconnector=disconnector:self._network.add_disconnector(disconnector));return self._success(disconnector,"disconnector",disconnector_id,f"Disconnector deleted: {disconnector_id}")
    def open_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:return self._set_disconnector_closed(disconnector_id=disconnector_id,closed=False,transaction=transaction)
    def close_disconnector(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:return self._set_disconnector_closed(disconnector_id=disconnector_id,closed=True,transaction=transaction)
    def put_disconnector_in_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:return self._set_disconnector_service(disconnector_id=disconnector_id,in_service=True,transaction=transaction)
    def take_disconnector_out_of_service(self, *, disconnector_id: str, transaction: Transaction) -> ApplicationResult[Disconnector]:return self._set_disconnector_service(disconnector_id=disconnector_id,in_service=False,transaction=transaction)
    def _set_disconnector_closed(self, *, disconnector_id: str, closed: bool, transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction);self._require_id(disconnector_id,"disconnector_id");disconnector=self._get_required("disconnector",disconnector_id,"Disconnector");self._require_type(disconnector,Disconnector,disconnector_id,"Disconnector");old=disconnector.closed;disconnector.set_closed(closed);transaction.record_undo(lambda disconnector=disconnector,old=old:disconnector.set_closed(old));return self._success(disconnector,"disconnector",disconnector_id,f"Disconnector {'closed' if closed else 'opened'}: {disconnector_id}")
    def _set_disconnector_service(self, *, disconnector_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Disconnector]:
        self._require_transaction(transaction);self._require_id(disconnector_id,"disconnector_id");disconnector=self._get_required("disconnector",disconnector_id,"Disconnector");self._require_type(disconnector,Disconnector,disconnector_id,"Disconnector");old=disconnector.in_service;disconnector.set_in_service(in_service);transaction.record_undo(lambda disconnector=disconnector,old=old:disconnector.set_in_service(old));return self._success(disconnector,"disconnector",disconnector_id,f"Disconnector {'put in service' if in_service else 'taken out of service'}: {disconnector_id}")

    def create_fuse(self, *, fuse_id: str, name: str = "", rated_current_a: float = 1.0, rated_voltage_v: float = 1.0, interrupting_rating_ka: float = 0.0, in_service: bool = True, blown: bool = False, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction);self._require_id(fuse_id,"fuse_id");self._ensure_not_exists("fuse",fuse_id,"Fuse");fuse=Fuse(id=fuse_id,name=name,rated_current_a=rated_current_a,rated_voltage_v=rated_voltage_v,interrupting_rating_ka=interrupting_rating_ka,in_service=in_service,blown=blown);self._network.add_fuse(fuse);transaction.record_undo(lambda fuse=fuse:self._network.remove_fuse(fuse));return self._success(fuse,"fuse",fuse_id,f"Fuse created: {fuse_id}")
    def update_fuse(self, *, fuse_id: str, name: str | None = None, rated_current_a: float | None = None, rated_voltage_v: float | None = None, interrupting_rating_ka: float | None = None, in_service: bool | None = None, blown: bool | None = None, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction);self._require_id(fuse_id,"fuse_id");fuse=self._get_required("fuse",fuse_id,"Fuse");self._require_type(fuse,Fuse,fuse_id,"Fuse")
        if all(v is None for v in (name,rated_current_a,rated_voltage_v,interrupting_rating_ka,in_service,blown)):raise DomainError(code="NO_FUSE_UPDATE",message="At least one mutable Fuse property must be specified.",details={"fuse_id":fuse_id})
        old={"name":fuse.name,"rated_current_a":fuse.rated_current_a,"rated_voltage_v":fuse.rated_voltage_v,"interrupting_rating_ka":fuse.interrupting_rating_ka,"in_service":fuse.in_service,"blown":fuse.blown}
        for k,v in (("name",name),("rated_current_a",rated_current_a),("rated_voltage_v",rated_voltage_v),("interrupting_rating_ka",interrupting_rating_ka)):
            if v is not None:setattr(fuse,k,v)
        if in_service is not None:fuse.set_in_service(in_service)
        if blown is not None:fuse.blow() if blown else fuse.reset()
        def restore(): fuse.name=old["name"];fuse.rated_current_a=old["rated_current_a"];fuse.rated_voltage_v=old["rated_voltage_v"];fuse.interrupting_rating_ka=old["interrupting_rating_ka"];fuse.set_in_service(old["in_service"]);fuse.blow() if old["blown"] else fuse.reset()
        transaction.record_undo(restore);return self._success(fuse,"fuse",fuse_id,f"Fuse updated: {fuse_id}")
    def delete_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction);self._require_id(fuse_id,"fuse_id");fuse=self._get_required("fuse",fuse_id,"Fuse");self._require_type(fuse,Fuse,fuse_id,"Fuse");self._network.remove_fuse(fuse);transaction.record_undo(lambda fuse=fuse:self._network.add_fuse(fuse));return self._success(fuse,"fuse",fuse_id,f"Fuse deleted: {fuse_id}")
    def blow_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction);self._require_id(fuse_id,"fuse_id");fuse=self._get_required("fuse",fuse_id,"Fuse");self._require_type(fuse,Fuse,fuse_id,"Fuse");old=fuse.blown;fuse.blow();transaction.record_undo(lambda fuse=fuse,old=old:fuse.reset() if not old else fuse.blow());return self._success(fuse,"fuse",fuse_id,f"Fuse blown: {fuse_id}")
    def reset_fuse(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction);self._require_id(fuse_id,"fuse_id");fuse=self._get_required("fuse",fuse_id,"Fuse");self._require_type(fuse,Fuse,fuse_id,"Fuse");old=fuse.blown;fuse.reset();transaction.record_undo(lambda fuse=fuse,old=old:fuse.blow() if old else fuse.reset());return self._success(fuse,"fuse",fuse_id,f"Fuse reset: {fuse_id}")
    def put_fuse_in_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:return self._set_fuse_service(fuse_id=fuse_id,in_service=True,transaction=transaction)
    def take_fuse_out_of_service(self, *, fuse_id: str, transaction: Transaction) -> ApplicationResult[Fuse]:return self._set_fuse_service(fuse_id=fuse_id,in_service=False,transaction=transaction)
    def _set_fuse_service(self, *, fuse_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Fuse]:
        self._require_transaction(transaction);self._require_id(fuse_id,"fuse_id");fuse=self._get_required("fuse",fuse_id,"Fuse");self._require_type(fuse,Fuse,fuse_id,"Fuse");old=fuse.in_service;fuse.set_in_service(in_service);transaction.record_undo(lambda fuse=fuse,old=old:fuse.set_in_service(old));return self._success(fuse,"fuse",fuse_id,f"Fuse {'put in service' if in_service else 'taken out of service'}: {fuse_id}")


__all__ = ["ModelService"]
