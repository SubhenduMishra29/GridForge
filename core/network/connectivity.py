from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from core.model import EndpointReference, EndpointReferenceKind
from .electrical_boundary import EndpointCompatibility
SIMPLE_WIRE_KIND="SIMPLE_WIRE"
class ConnectivityError(ValueError): pass
@dataclass(frozen=True, slots=True)
class SimpleWireConnection:
    connection_id:str
    endpoint_a:EndpointReference
    endpoint_b:EndpointReference
    kind:str=SIMPLE_WIRE_KIND
    def __post_init__(self):
        if not isinstance(self.connection_id,str) or not self.connection_id.strip(): raise ValueError("connection_id must be a non-empty string.")
        object.__setattr__(self,"connection_id",self.connection_id.strip())
        if not isinstance(self.endpoint_a,EndpointReference) or not isinstance(self.endpoint_b,EndpointReference): raise TypeError("Simple Wire endpoints must be EndpointReference values.")
        if self.kind!=SIMPLE_WIRE_KIND: raise ValueError(f"Simple Wire kind must be {SIMPLE_WIRE_KIND!r}.")
        EndpointCompatibility.validate_pair(self.endpoint_a,self.endpoint_b)
    @property
    def endpoint_pair_key(self):
        a,b=self.endpoint_a,self.endpoint_b
        return (a,b) if _key(a)<=_key(b) else (b,a)
    @property
    def equipment_ids(self): return self.endpoint_a.object_id,self.endpoint_b.object_id
    def to_dict(self): return {"connection_id":self.connection_id,"kind":self.kind,"endpoint_a":dict(self.endpoint_a.to_mapping()),"endpoint_b":dict(self.endpoint_b.to_mapping())}
    @classmethod
    def from_dict(cls,data): return cls(str(data["connection_id"]),_endpoint_from_mapping(data.get("endpoint_a")),_endpoint_from_mapping(data.get("endpoint_b")),str(data.get("kind",SIMPLE_WIRE_KIND)))
def _key(r): return (r.kind.value,r.equipment_type.value if r.equipment_type else "",r.object_id,r.terminal_role or "")
def _endpoint_from_mapping(data):
    if not isinstance(data,dict): raise ConnectivityError("Persisted Simple Wire endpoint must be an object.")
    if data.get("kind")==EndpointReferenceKind.BUS.value: return EndpointReference.bus(data["object_id"])
    if data.get("kind")!=EndpointReferenceKind.TERMINAL.value: raise ConnectivityError("Persisted Simple Wire endpoint kind is invalid.")
    from core.model import EquipmentType
    try: et=EquipmentType(str(data["equipment_type"]).strip().lower())
    except ValueError as exc: raise ConnectivityError("Unknown terminal equipment type.") from exc
    return EndpointReference.terminal(equipment_type=et,equipment_id=data["object_id"],terminal_role=data["terminal_role"])
class ConnectivityStore:
    def __init__(self): self._connections={}; self._endpoint_index={}; self._equipment_index={}
    @property
    def connections(self): return tuple(self._connections.values())
    def add(self,connection,network=None):
        if not isinstance(connection,SimpleWireConnection): raise TypeError("connection must be a SimpleWireConnection.")
        EndpointCompatibility.validate_pair(connection.endpoint_a,connection.endpoint_b,network)
        if connection.connection_id in self._connections: raise ConnectivityError(f"Simple Wire connection ID already exists: {connection.connection_id}")
        if any(x.endpoint_pair_key==connection.endpoint_pair_key for x in self._connections.values()): raise ConnectivityError("Duplicate Simple Wire relationship.")
        for endpoint in (connection.endpoint_a,connection.endpoint_b):
            if endpoint.is_terminal and self.connections_for_endpoint(endpoint): raise ConnectivityError(f"Terminal {endpoint} already participates in a Simple Wire relationship.")
        self._connections[connection.connection_id]=connection; self._index(connection); return connection
    def remove(self,connection_id):
        c=self.get(connection_id); del self._connections[c.connection_id]; self._deindex(c); return c
    def get(self,connection_id):
        try:return self._connections[connection_id]
        except KeyError as exc:raise KeyError(f"Simple Wire connection is not registered: {connection_id}") from exc
    def contains(self,connection_id): return connection_id in self._connections
    def connections_for_endpoint(self,endpoint): return tuple(self._connections[x] for x in sorted(self._endpoint_index.get(endpoint,set())))
    def connections_for_equipment(self,equipment_id): return tuple(self._connections[x] for x in sorted(self._equipment_index.get(equipment_id,set())))
    def validate(self,network):
        rebuilt=ConnectivityStore()
        for c in sorted(self._connections.values(),key=lambda x:x.connection_id): rebuilt.add(c,network)
        if tuple(rebuilt._connections)!=tuple(sorted(self._connections)): raise ConnectivityError("Connectivity indexes are inconsistent.")
    def _index(self,c):
        for e in (c.endpoint_a,c.endpoint_b):
            self._endpoint_index.setdefault(e,set()).add(c.connection_id); self._equipment_index.setdefault(e.object_id,set()).add(c.connection_id)
    def _deindex(self,c):
        for e in (c.endpoint_a,c.endpoint_b):
            ids=self._endpoint_index.get(e)
            if ids is not None:
                ids.discard(c.connection_id)
                if not ids:self._endpoint_index.pop(e,None)
            ids=self._equipment_index.get(e.object_id)
            if ids is not None:
                ids.discard(c.connection_id)
                if not ids:self._equipment_index.pop(e.object_id,None)
@dataclass(frozen=True, slots=True)
class ResolvedConnectivity:
    terminal_adjacency:tuple[tuple[EndpointReference,tuple[EndpointReference,...]],...]
    def neighbours(self,endpoint):
        for source,targets in self.terminal_adjacency:
            if source==endpoint:return targets
        return ()
class ConnectivityResolver:
    def __init__(self,network): self._network=network
    def resolve(self):
        adjacency={}
        for c in sorted(self._network.connectivity.connections,key=lambda x:x.connection_id):
            adjacency.setdefault(c.endpoint_a,set()).add(c.endpoint_b); adjacency.setdefault(c.endpoint_b,set()).add(c.endpoint_a)
        return ResolvedConnectivity(tuple((s,tuple(sorted(ts,key=_key))) for s,ts in sorted(adjacency.items(),key=lambda x:_key(x[0]))))
    def terminal_component(self,endpoint):
        resolved=self.resolve(); seen={endpoint}; queue=[endpoint]
        while queue:
            cur=queue.pop(0)
            for n in resolved.neighbours(cur):
                if n not in seen:seen.add(n);queue.append(n)
        return tuple(sorted(seen,key=_key))
SimpleWireCompatibility=EndpointCompatibility
__all__=["ConnectivityError","ConnectivityResolver","ConnectivityStore","ResolvedConnectivity","SIMPLE_WIRE_KIND","SimpleWireCompatibility","SimpleWireConnection"]