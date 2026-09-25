from __future__ import annotations
from collections import deque
from core.model import Branch,Breaker,Cable,Disconnector,Fuse,Line,Switch,Transformer
from core.model.endpoint_reference import EndpointReference
from .connectivity import ConnectivityResolver
from .electrical_boundary import ElectricalBoundaryResolver,ElectricalBoundaryType,EndpointCompatibilityError,conduction_state
from .endpoint import resolve_terminal_bus
from .topology_snapshot import ConductiveEdge,EquipmentBusAttachment,TopologySnapshot
class TopologyManager:
    _TOPOLOGY_TYPES=(Branch,Line,Cable,Transformer,Breaker,Switch,Disconnector,Fuse)
    def __init__(self,network): self.network=network;self._graph={};self._edges={};self._snapshot=None
    @property
    def snapshot(self): return self._snapshot
    def build(self):
        graph={b:set() for b in self.network.buses};self._edges={};boundary=ElectricalBoundaryResolver(self.network)
        self.network.connectivity.validate(self.network);attachments=self._physical_attachments();self._validate_conductive_elements(boundary)
        zero={}
        for b in self.network.buses:self._node(zero,("bus",b.id))
        for a in attachments:self._edge(zero,("terminal",a.equipment_id+"::"+a.terminal_role),("bus",a.bus_id))
        for c in self.network.connectivity.connections:
            for e in (c.endpoint_a,c.endpoint_b): self._node(zero,self._node_for_reference(e))
            na=self._node_for_reference(c.endpoint_a);nb=self._node_for_reference(c.endpoint_b);self._edge(zero,na,nb)
            for e,n in ((c.endpoint_a,na),(c.endpoint_b,nb)):
                b=boundary.resolve(e)
                if e.is_terminal and b.boundary_type is ElectricalBoundaryType.SWITCHING_BOUNDARY and b.conductive and b.opposite_terminal is not None:self._edge(zero,n,self._node_for_reference(b.opposite_terminal))
        adjacency={b.id:set() for b in self.network.buses}
        for component in self._components(zero):
            buses=sorted(n[1] for n in component if n[0]=="bus")
            for i,a in enumerate(buses):
                for b in buses[i+1:]:adjacency[a].add(b);adjacency[b].add(a)
        for b in self.network.buses:
            graph[b]={self.network.get_by_identity(x) for x in sorted(adjacency[b.id])}
        # Conductive equipment is an explicit electrical boundary. It contributes
        # Bus adjacency, but Simple Wire never traverses its numerical branch.
        for e in self._topology_elements():
            if not conduction_state(e):
                continue
            terminals=tuple(getattr(e,"terminals",()))
            if len(terminals)!=2:
                continue
            bus_a=resolve_terminal_bus(terminals[0]); bus_b=resolve_terminal_bus(terminals[1])
            if bus_a is None or bus_b is None:
                raise EndpointCompatibilityError(f"Conductive {type(e).__name__} '{e.id}' has unresolved terminals.")
            if bus_a is not bus_b:
                graph.setdefault(bus_a,set()).add(bus_b)
                graph.setdefault(bus_b,set()).add(bus_a)
                adjacency[bus_a.id].add(bus_b.id)
                adjacency[bus_b.id].add(bus_a.id)
        for e in self._topology_elements():
            if conduction_state(e) and isinstance(e,(Line,Cable,Transformer)):
                a=resolve_terminal_bus(e.from_terminal);b=resolve_terminal_bus(e.to_terminal)
                if a is None or b is None:raise EndpointCompatibilityError(f"Conductive {type(e).__name__} '{e.id}' has unresolved terminals.")
                if a is not b:self._edges.setdefault(self._edge_key(a,b),[]).append(e)
        self._graph=graph;self._snapshot=self._make_snapshot(adjacency,attachments,boundary);return graph
    def _physical_attachments(self):
        out=[];seen=set()
        for e in self._registered_equipment():
            for t in sorted(getattr(e,"terminals",()),key=lambda x:x.role):
                bus=resolve_terminal_bus(t)
                if bus is None:continue
                if bus not in self.network.buses:raise EndpointCompatibilityError(f"Equipment '{e.id}' terminal '{t.role}' resolves to an unregistered Bus.")
                key=(e.id,t.role,bus.id)
                if key not in seen:seen.add(key);out.append(EquipmentBusAttachment(*key))
        return tuple(out)
    def _registered_equipment(self):
        names=("grids","generators","synchronous_machines","loads","motors","shunts","capacitors","reactors","solar","batteries","current_transformers","capacitive_voltage_transformers","potential_transformers","relays","lines","cables","transformers","breakers","switches","disconnectors","fuses")
        out=[];seen=set()
        for name in names:
            for e in getattr(self.network,name,()):
                if id(e) not in seen:seen.add(id(e));out.append(e)
        return tuple(sorted(out,key=lambda e:str(getattr(e,"id",""))))
    def _validate_conductive_elements(self,resolver):
        for e in self._topology_elements():
            if not conduction_state(e):continue
            for t in getattr(e,"terminals",()):
                b=resolver.resolve(self._reference_for_terminal(e,t.role))
                if b.attached_bus_id is None:raise EndpointCompatibilityError(f"Conductive {type(e).__name__} '{e.id}' terminal '{t.role}' has no physical Bus attachment.")
    def _conductive_edges(self,resolver):
        out=[]
        for e in self._topology_elements():
            if not isinstance(e,(Breaker,Switch,Disconnector,Fuse)) or not conduction_state(e):continue
            ts=tuple(e.terminals)
            if len(ts)!=2:raise EndpointCompatibilityError(f"Switching element '{e.id}' must have exactly two terminals.")
            a=resolver.resolve(self._reference_for_terminal(e,ts[0].role));b=resolver.resolve(self._reference_for_terminal(e,ts[1].role))
            if a.attached_bus_id and b.attached_bus_id and a.attached_bus_id!=b.attached_bus_id:out.append(ConductiveEdge(e.id,str(e.element_type).lower(),a.attached_bus_id,b.attached_bus_id,ts[0].role,ts[1].role))
        return tuple(out)
    def _make_snapshot(self,adjacency,attachments,resolver):
        buses=tuple(sorted(adjacency));remaining=set(buses);islands=[]
        while remaining:
            start=min(remaining);part={start};q=[start]
            while q:
                cur=q.pop(0)
                for n in sorted(adjacency[cur]):
                    if n not in part:part.add(n);q.append(n)
            remaining-=part;islands.append(tuple(sorted(part)))
        return TopologySnapshot(str(getattr(self.network,"project_id","UNSCOPED")),int(getattr(self.network,"activation_generation",1)),self.network.state.topology_revision,buses,{k:tuple(sorted(v)) for k,v in adjacency.items()},attachments,self._conductive_edges(resolver),tuple(islands))
    def invalidate(self):self._graph={};self._edges={};self._snapshot=None
    def _ensure_built(self):
        if self.network.state.topology_dirty or self._snapshot is None:self.network.rebuild_topology()
    def _node_for_reference(self,r):return ("bus",r.object_id) if r.is_bus else ("terminal",r.object_id+"::"+(r.terminal_role or ""))
    @staticmethod
    def _node(g,n):g.setdefault(n,set())
    @staticmethod
    def _edge(g,a,b):g.setdefault(a,set()).add(b);g.setdefault(b,set()).add(a)
    @classmethod
    def _reference_for_terminal(cls,e,role):
        from core.model.endpoint_reference import EquipmentType
        try:et=EquipmentType(str(e.element_type).strip().lower())
        except ValueError as exc:raise EndpointCompatibilityError(f"Unsupported equipment type '{e.element_type}'.") from exc
        return EndpointReference.terminal(equipment_type=et,equipment_id=e.id,terminal_role=role)
    def _topology_elements(self):
        out=[];seen=set()
        for name in ("branches","lines","cables","transformers","breakers","switches","disconnectors","fuses"):
            for e in getattr(self.network,name,()):
                if isinstance(e,self._TOPOLOGY_TYPES) and id(e) not in seen:seen.add(id(e));out.append(e)
        return out
    @staticmethod
    def _components(g):
        out=[];vis=set()
        for start in sorted(g):
            if start in vis:continue
            c=set();q=deque([start]);vis.add(start)
            while q:
                cur=q.popleft();c.add(cur)
                for n in sorted(g[cur]):
                    if n not in vis:vis.add(n);q.append(n)
            out.append(c)
        return out
    @staticmethod
    def _edge_key(a,b):return (a,b) if str(a.id)<=str(b.id) else (b,a)
    def neighbours(self,bus):self._require_bus(bus);self._ensure_built();return set(self._graph.get(bus,set()))
    def degree(self,bus):return len(self.neighbours(bus))
    def is_connected(self,a,b):
        self._require_bus(a);self._require_bus(b)
        if a is b:return True
        self._ensure_built();vis={a};q=deque([a])
        while q:
            cur=q.popleft()
            for n in self._graph.get(cur,set()):
                if n is b:return True
                if n not in vis:vis.add(n);q.append(n)
        return False
    def connected_component(self,bus):
        self._require_bus(bus);self._ensure_built();c={bus};q=deque([bus])
        while q:
            cur=q.popleft()
            for n in self._graph.get(cur,set()):
                if n not in c:c.add(n);q.append(n)
        return c
    def find_islands(self):self._ensure_built();return [set(self.network.get_by_identity(x) for x in i) for i in self._snapshot.islands]
    def island_count(self):return len(self.find_islands())
    def branches_between(self,a,b):self._require_bus(a);self._require_bus(b);self._ensure_built();return list(self._edges.get(self._edge_key(a,b),[]))
    def _require_bus(self,bus):
        if bus is None or bus not in self.network.buses:raise ValueError(f"Bus '{getattr(bus,'id',bus)}' is not registered on this Network.")
    def summary(self):self._ensure_built();return {"buses":len(self.network.buses),"edges":sum(len(v) for v in self._graph.values())//2,"islands":self.island_count(),"topology_revision":self.network.state.topology_revision,"topology_valid":self.network.state.topology_valid}
__all__=["TopologyManager"]