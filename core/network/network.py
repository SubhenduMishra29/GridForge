"""Authoritative electrical Network aggregate."""

from __future__ import annotations

from typing import Any, Optional

from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager


class Network:
    """Authoritative electrical network aggregate."""

    def __init__(self, *, registry: Optional[NetworkRegistry] = None, state: Optional[NetworkState] = None, index: Optional[BusIndex] = None, topology: Optional[TopologyManager] = None) -> None:
        self.registry = registry or NetworkRegistry()
        self.state = state or NetworkState()
        self.index = index or BusIndex()
        self.topology = topology or TopologyManager(self)
        if getattr(self.topology, "network", self) is not self: raise ValueError("TopologyManager belongs to another Network.")

    @property
    def buses(self): return self.registry.buses
    @property
    def grids(self): return self.registry.grids
    @property
    def generators(self): return self.registry.generators
    @property
    def synchronous_machines(self): return self.registry.synchronous_machines
    @property
    def loads(self): return self.registry.loads
    @property
    def motors(self): return self.registry.motors
    @property
    def shunts(self): return self.registry.shunts
    @property
    def capacitors(self): return self.registry.capacitors
    @property
    def reactors(self): return self.registry.reactors
    @property
    def solar(self): return self.registry.solar
    @property
    def batteries(self): return self.registry.batteries
    @property
    def current_transformers(self): return self.registry.current_transformers
    @property
    def potential_transformers(self): return self.registry.potential_transformers
    @property
    def capacitive_voltage_transformers(self): return self.registry.capacitive_voltage_transformers
    @property
    def lines(self): return self.registry.lines
    @property
    def cables(self): return self.registry.cables
    @property
    def transformers(self): return self.registry.transformers
    @property
    def branches(self): return self.registry.branches
    @property
    def breakers(self): return self.registry.breakers
    @property
    def switches(self): return self.registry.switches
    @property
    def disconnectors(self): return self.registry.disconnectors
    @property
    def fuses(self): return self.registry.fuses

    def get_by_id(self, element_type: str, object_id: str) -> Any: return self.registry.get_by_id(element_type, object_id)

    def _invalidate_topology(self, *, bus_membership: bool = False) -> None:
        self.state.invalidate_topology(); self.topology.invalidate()
        if bus_membership: self.index.invalidate()

    def invalidate_topology(self) -> None: self._invalidate_topology()

    def _add(self, method: Any, element: Any, *, affects_topology: bool = False, affects_bus_index: bool = False) -> None:
        method(element)
        if affects_topology: self._invalidate_topology(bus_membership=affects_bus_index)

    def _remove(self, method: Any, element: Any, *, affects_topology: bool = False, affects_bus_index: bool = False) -> None:
        method(element)
        if affects_topology: self._invalidate_topology(bus_membership=affects_bus_index)

    def add_bus(self, bus): self._add(self.registry.add_bus, bus, affects_topology=True, affects_bus_index=True)
    def remove_bus(self, bus): self._remove(self.registry.remove_bus, bus, affects_topology=True, affects_bus_index=True)
    def add_grid(self, grid): self._add(self.registry.add_grid, grid)
    def remove_grid(self, grid): self._remove(self.registry.remove_grid, grid)
    def add_generator(self, generator): self._add(self.registry.add_generator, generator)
    def remove_generator(self, generator): self._remove(self.registry.remove_generator, generator)
    def add_synchronous_machine(self, machine): self._add(self.registry.add_synchronous_machine, machine)
    def remove_synchronous_machine(self, machine): self._remove(self.registry.remove_synchronous_machine, machine)
    def add_load(self, load): self._add(self.registry.add_load, load)
    def remove_load(self, load): self._remove(self.registry.remove_load, load)
    def add_motor(self, motor): self._add(self.registry.add_motor, motor)
    def remove_motor(self, motor): self._remove(self.registry.remove_motor, motor)
    def add_shunt(self, shunt): self._add(self.registry.add_shunt, shunt)
    def remove_shunt(self, shunt): self._remove(self.registry.remove_shunt, shunt)
    def add_capacitor(self, capacitor): self._add(self.registry.add_capacitor, capacitor)
    def remove_capacitor(self, capacitor): self._remove(self.registry.remove_capacitor, capacitor)
    def add_reactor(self, reactor): self._add(self.registry.add_reactor, reactor)
    def remove_reactor(self, reactor): self._remove(self.registry.remove_reactor, reactor)
    def add_solar(self, solar): self._add(self.registry.add_solar, solar)
    def remove_solar(self, solar): self._remove(self.registry.remove_solar, solar)
    def add_battery(self, battery): self._add(self.registry.add_battery, battery)
    def remove_battery(self, battery): self._remove(self.registry.remove_battery, battery)
    def add_current_transformer(self, transformer): self._add(self.registry.add_current_transformer, transformer)
    def remove_current_transformer(self, transformer): self._remove(self.registry.remove_current_transformer, transformer)
    def add_potential_transformer(self, transformer): self._add(self.registry.add_potential_transformer, transformer)
    def remove_potential_transformer(self, transformer): self._remove(self.registry.remove_potential_transformer, transformer)
    def add_capacitive_voltage_transformer(self, transformer): self._add(self.registry.add_capacitive_voltage_transformer, transformer)
    def remove_capacitive_voltage_transformer(self, transformer): self._remove(self.registry.remove_capacitive_voltage_transformer, transformer)
    def add_line(self, line): self._add(self.registry.add_line, line, affects_topology=True)
    def remove_line(self, line): self._remove(self.registry.remove_line, line, affects_topology=True)
    def add_cable(self, cable): self._add(self.registry.add_cable, cable, affects_topology=True)
    def remove_cable(self, cable): self._remove(self.registry.remove_cable, cable, affects_topology=True)
    def add_transformer(self, transformer): self._add(self.registry.add_transformer, transformer, affects_topology=True)
    def remove_transformer(self, transformer): self._remove(self.registry.remove_transformer, transformer, affects_topology=True)
    def add_breaker(self, breaker): self._add(self.registry.add_breaker, breaker, affects_topology=True)
    def remove_breaker(self, breaker): self._remove(self.registry.remove_breaker, breaker, affects_topology=True)
    def add_switch(self, switch): self._add(self.registry.add_switch, switch, affects_topology=True)
    def remove_switch(self, switch): self._remove(self.registry.remove_switch, switch, affects_topology=True)
    def add_disconnector(self, disconnector): self._add(self.registry.add_disconnector, disconnector, affects_topology=True)
    def remove_disconnector(self, disconnector): self._remove(self.registry.remove_disconnector, disconnector, affects_topology=True)
    def add_fuse(self, fuse): self._add(self.registry.add_fuse, fuse, affects_topology=True)
    def remove_fuse(self, fuse): self._remove(self.registry.remove_fuse, fuse, affects_topology=True)

    def rebuild_topology(self):
        graph = self.topology.build(); self.state.topology_rebuilt(); return graph
    def ensure_bus_index(self): self.index.ensure(self.buses)
    @property
    def topology_revision(self): return self.state.topology_revision
    @property
    def topology_valid(self): return self.state.topology_valid
    @property
    def topology_dirty(self): return self.state.topology_dirty
    @property
    def index_valid(self): return self.index.valid
    def __repr__(self) -> str: return f"Network(buses={len(self.buses)}, branches={len(self.branches)}, topology_revision={self.topology_revision}, topology_valid={self.topology_valid}, index_valid={self.index_valid})"


__all__ = ["Network"]
