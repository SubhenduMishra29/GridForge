# ============================================================
# File: core/application/draft/network.py
# GridForge V2 — Persistent Application Draft Network
# Author: Subhendu Mishra
# ============================================================
"""Application-owned engineering draft; never authoritative Core state."""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from copy import deepcopy

@dataclass(frozen=True, slots=True)
class DraftEndpoint:
    draft_id: str
    terminal_role: str
    endpoint_kind: str = "terminal"
    attachment_id: str | None = None
    def __post_init__(self) -> None:
        if not self.draft_id.strip() or not self.terminal_role.strip(): raise ValueError("DraftEndpoint requires draft_id and terminal_role.")
        if self.endpoint_kind != "bus" and not self.endpoint_kind.strip(): raise ValueError("DraftEndpoint requires endpoint kind.")
    def to_dict(self): return {"draft_id":self.draft_id,"terminal_role":self.terminal_role,"endpoint_kind":self.endpoint_kind,"attachment_id":self.attachment_id}
    @classmethod
    def from_value(cls,value):
        if isinstance(value,cls): return value
        return cls(str(value["draft_id"]),str(value["terminal_role"]),str(value.get("endpoint_kind","terminal")),value.get("attachment_id"))

@dataclass(frozen=True, slots=True)
class DraftEquipment:
    draft_id: str
    equipment_type: str
    display_name: str
    terminal_contract: tuple[str,...]
    engineering_data: Mapping[str,Any]=field(default_factory=dict)
    endpoints: Mapping[str,DraftEndpoint]=field(default_factory=dict)
    placement: tuple[float,float]|None=None
    presentation: Mapping[str,Any]=field(default_factory=dict)
    validation_state: Mapping[str,Any]=field(default_factory=dict)
    command_type: str=""
    id_field: str=""
    parameter_mapping: Mapping[str,str]=field(default_factory=dict)
    endpoint_mapping: Mapping[str,str]=field(default_factory=dict)
    def __post_init__(self):
        if not self.draft_id.strip() or not self.equipment_type.strip(): raise ValueError("DraftEquipment identity is required.")
        if not self.command_type.strip() or not self.id_field.strip(): raise ValueError("DraftEquipment requires its canonical command contract.")
        object.__setattr__(self,"terminal_contract",tuple(self.terminal_contract))
        object.__setattr__(self,"engineering_data",MappingProxyType(dict(self.engineering_data)))
        object.__setattr__(self,"endpoints",MappingProxyType({k:DraftEndpoint.from_value(v) for k,v in self.endpoints.items()}))
        object.__setattr__(self,"presentation",MappingProxyType(dict(self.presentation)))
        object.__setattr__(self,"validation_state",MappingProxyType(dict(self.validation_state)))
        object.__setattr__(self,"parameter_mapping",MappingProxyType(dict(self.parameter_mapping)))
        object.__setattr__(self,"endpoint_mapping",MappingProxyType(dict(self.endpoint_mapping)))
    def to_dict(self):
        return {"draft_id":self.draft_id,"equipment_type":self.equipment_type,"display_name":self.display_name,"terminal_contract":list(self.terminal_contract),
                "engineering_data":deepcopy(dict(self.engineering_data)),"endpoints":{k:v.to_dict() for k,v in self.endpoints.items()},
                "placement":None if self.placement is None else list(self.placement),"presentation":deepcopy(dict(self.presentation)),
                "validation_state":deepcopy(dict(self.validation_state)),"command_type":self.command_type,"id_field":self.id_field,
                "parameter_mapping":dict(self.parameter_mapping),"endpoint_mapping":dict(self.endpoint_mapping)}
    @classmethod
    def from_dict(cls,data):
        p=data.get("placement")
        return cls(str(data["draft_id"]),str(data["equipment_type"]),str(data.get("display_name",data["equipment_type"])),
            tuple(str(x) for x in data.get("terminal_contract",())),dict(data.get("engineering_data",{})),
            {k:DraftEndpoint.from_value(v) for k,v in dict(data.get("endpoints",{})).items()},
            None if p is None else (float(p[0]),float(p[1])),dict(data.get("presentation",{})),dict(data.get("validation_state",{})),
            str(data["command_type"]),str(data["id_field"]),dict(data.get("parameter_mapping",{})),dict(data.get("endpoint_mapping",{})))

@dataclass(frozen=True, slots=True)
class DraftConnection:
    connection_id:str; source_draft_id:str; source_terminal:str; target_draft_id:str; target_terminal:str
    connection_kind:str="simple_wire"; route:Mapping[str,Any]=field(default_factory=dict); validation_state:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not all(str(x).strip() for x in (self.connection_id,self.source_draft_id,self.source_terminal,self.target_draft_id,self.target_terminal)): raise ValueError("DraftConnection identity/endpoints are required.")
        object.__setattr__(self,"route",MappingProxyType(dict(self.route))); object.__setattr__(self,"validation_state",MappingProxyType(dict(self.validation_state)))
    def to_dict(self): return {"connection_id":self.connection_id,"source_draft_id":self.source_draft_id,"source_terminal":self.source_terminal,"target_draft_id":self.target_draft_id,"target_terminal":self.target_terminal,"connection_kind":self.connection_kind,"route":deepcopy(dict(self.route)),"validation_state":deepcopy(dict(self.validation_state))}
    @classmethod
    def from_dict(cls,data): return cls(str(data["connection_id"]),str(data["source_draft_id"]),str(data["source_terminal"]),str(data["target_draft_id"]),str(data["target_terminal"]),str(data.get("connection_kind","simple_wire")),dict(data.get("route",{})),dict(data.get("validation_state",{})))

class DraftNetwork:
    SCHEMA=1
    def __init__(self,project_id:str,activation_generation:int):
        if not str(project_id).strip() or int(activation_generation)<1: raise ValueError("DraftNetwork requires valid project scope.")
        self.project_id=str(project_id); self.activation_generation=int(activation_generation); self._equipment={}; self._connections={}; self.validation_state={}
    @property
    def equipment(self): return tuple(self._equipment.values())
    @property
    def connections(self): return tuple(self._connections.values())
    def require_equipment(self,draft_id): return self._equipment[draft_id]
    def add_equipment(self,equipment): 
        if equipment.draft_id in self._equipment: raise ValueError(f"Draft equipment already exists: {equipment.draft_id}")
        self._equipment[equipment.draft_id]=equipment; self.validation_state={}
    def update_equipment(self,draft_id,**changes):
        current=self.require_equipment(draft_id); allowed={"display_name","engineering_data","endpoints","placement","presentation","validation_state"}
        unknown=set(changes)-allowed
        if unknown: raise ValueError(f"Unsupported DraftEquipment fields: {sorted(unknown)!r}")
        values={f:getattr(current,f) for f in ("draft_id","equipment_type","display_name","terminal_contract","engineering_data","endpoints","placement","presentation","validation_state","command_type","id_field","parameter_mapping","endpoint_mapping")}
        values.update(changes); updated=DraftEquipment(**values); self._equipment[draft_id]=updated; self.validation_state={}; return updated
    def remove_equipment(self,draft_id):
        equipment=self._equipment.pop(draft_id)
        for cid,c in tuple(self._connections.items()):
            if c.source_draft_id==draft_id or c.target_draft_id==draft_id: self._connections.pop(cid)
        self.validation_state={}; return equipment
    def add_connection(self,connection):
        if connection.connection_id in self._connections: raise ValueError(f"Draft connection already exists: {connection.connection_id}")
        source,target=self.require_equipment(connection.source_draft_id),self.require_equipment(connection.target_draft_id)
        if connection.source_terminal not in source.terminal_contract or connection.target_terminal not in target.terminal_contract: raise ValueError("Draft connection uses a non-canonical terminal role.")
        if source.draft_id==target.draft_id and connection.source_terminal==connection.target_terminal: raise ValueError("Draft connection endpoints must be distinct.")
        self._connections[connection.connection_id]=connection; self.validation_state={}
    def remove_connection(self,connection_id): return self._connections.pop(connection_id)
    def validate(self):
        errors=[]
        from ..creation import CreationCommitIntent, CreationCommandPreparer
        for item in self._equipment.values():
            if item.placement is None: errors.append(f"{item.draft_id}: placement is required.")
            for role in item.endpoints:
                if role not in item.terminal_contract: errors.append(f"{item.draft_id}: endpoint role {role!r} is not canonical.")
            try:
                CreationCommandPreparer.prepare(CreationCommitIntent(command_type=item.command_type,id_field=item.id_field,object_id=item.draft_id,parameter_mapping=dict(item.parameter_mapping),endpoint_mapping=dict(item.endpoint_mapping),values=dict(item.engineering_data),endpoints=dict(item.endpoints),position=item.placement))
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"{item.draft_id}: engineering/create-command validation failed: {exc}")
        for item in self._connections.values():
            try: source,target=self.require_equipment(item.source_draft_id),self.require_equipment(item.target_draft_id)
            except KeyError: errors.append(f"{item.connection_id}: unresolved draft endpoint."); continue
            if item.source_terminal not in source.terminal_contract: errors.append(f"{item.connection_id}: invalid source terminal {item.source_terminal!r}.")
            if item.target_terminal not in target.terminal_contract: errors.append(f"{item.connection_id}: invalid target terminal {item.target_terminal!r}.")
        self.validation_state={"errors":tuple(errors),"valid":not errors}; return tuple(errors)
    def clear_after_commit(self): self._equipment.clear(); self._connections.clear(); self.validation_state={}
    def restore_snapshot(self,snapshot):
        restored=DraftNetwork.from_dict(snapshot,project_id=self.project_id,activation_generation=self.activation_generation)
        self._equipment=restored._equipment; self._connections=restored._connections; self.validation_state=restored.validation_state
    def to_dict(self): return {"schema":self.SCHEMA,"project_id":self.project_id,"activation_generation":self.activation_generation,"equipment":[x.to_dict() for x in self.equipment],"connections":[x.to_dict() for x in self.connections],"validation_state":deepcopy(self.validation_state)}
    @classmethod
    def from_dict(cls,data,*,project_id,activation_generation):
        if data.get("project_id",project_id)!=project_id: raise ValueError("DraftNetwork project_id does not match project metadata.")
        if data.get("activation_generation") is not None and int(data["activation_generation"])>activation_generation: raise ValueError("DraftNetwork generation is newer than active project generation.")
        draft=cls(project_id,activation_generation)
        for item in data.get("equipment",()): draft.add_equipment(DraftEquipment.from_dict(item))
        for item in data.get("connections",()): draft.add_connection(DraftConnection.from_dict(item))
        draft.validation_state=dict(data.get("validation_state",{})); return draft
    @classmethod
    def empty(cls,project_id,activation_generation): return cls(project_id,activation_generation)
