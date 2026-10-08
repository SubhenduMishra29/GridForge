# ============================================================
# File: core/network/network.py
# GridForge V2 — Authoritative Network Aggregate
# Author: Subhendu Mishra
# ============================================================

"""Authoritative electrical Network aggregate."""

from __future__ import annotations

from typing import Any, Optional

from .connectivity import ConnectivityStore, SimpleWireConnection
from .electrical_boundary import EndpointCompatibility, conduction_state
from .indexing import BusIndex
from .junction import Junction
from .junction_registry import JunctionRegistry
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager
from .topology_endpoint_reference import TopologyEndpointReferenceKind


class Network:
    """Authoritative electrical network aggregate."""

    def __init__(self, *, registry: Optional[NetworkRegistry] = None, junctions: Optional[JunctionRegistry] = None, state: Optional[NetworkState] = None, index: Optional[BusIndex] = None, topology: Optional[TopologyManager] = None, connectivity: Optional[ConnectivityStore] = None) -> None:
        self.registry = registry or NetworkRegistry()
        self._junctions = junctions or JunctionRegistry()
        self._junctions._bind_network(self)
        self.state = state or NetworkState()
        self.index = index or BusIndex()
        self.connectivity = connectivity or ConnectivityStore()
        if topology is None:
            self.topology = TopologyManager(self)
        else:
            owner = getattr(topology, "network", None)
            if owner is not None and owner is not self:
                raise ValueError("TopologyManager belongs to another Network.")
            self.topology = topology

    @property
    def buses(self) -> tuple[Any, ...]: return self.registry.buses
    @property
    def grids(self) -> tuple[Any, ...]: return self.registry.grids
    @property
    def generators(self) -> tuple[Any, ...]: return self.registry.generators
    @property
    def synchronous_machines(self) -> tuple[Any, ...]: return self.registry.synchronous_machines
    @property
    def loads(self) -> tuple[Any, ...]: return self.registry.loads
    @property
    def motors(self) -> tuple[Any, ...]: return self.registry.motors
    @property
    def shunts(self) -> tuple[Any, ...]: return self.registry.shunts
    @property
    def capacitors(self) -> tuple[Any, ...]: return self.registry.capacitors
    @property
    def reactors(self) -> tuple[Any, ...]: return self.registry.reactors
    @property
    def solar(self) -> tuple[Any, ...]: return self.registry.solar
    @property
    def batteries(self) -> tuple[Any, ...]: return self.registry.batteries
    @property
    def current_transformers(self) -> tuple[Any, ...]: return self.registry.current_transformers
    @property
    def capacitive_voltage_transformers(self) -> tuple[Any, ...]: return self.registry.capacitive_voltage_transformers
    @property
    def potential_transformers(self) -> tuple[Any, ...]: return self.registry.potential_transformers
    @property
    def relays(self) -> tuple[Any, ...]: return self.registry.relays
    @property
    def lines(self) -> tuple[Any, ...]: return self.registry.lines
    @property
    def cables(self) -> tuple[Any, ...]: return self.registry.cables
    @property
    def transformers(self) -> tuple[Any, ...]: return self.registry.transformers
    @property
    def branches(self) -> tuple[Any, ...]: return self.registry.branches
    @property
    def breakers(self) -> tuple[Any, ...]: return self.registry.breakers
    @property
    def switches(self) -> tuple[Any, ...]: return self.registry.switches
    @property
    def disconnectors(self) -> tuple[Any, ...]: return self.registry.disconnectors
    @property
    def fuses(self) -> tuple[Any, ...]: return self.registry.fuses
    @property
    def junction_snapshot(self) -> tuple[Junction, ...]: return self._junctions.snapshot

    def get_by_id(self, element_type: str, object_id: str) -> Any:
        return self.registry.get_by_id(element_type, object_id)

    def get_by_identity(self, object_id: str) -> Any:
        """Resolve one canonical electrical object by NetworkRegistry identity."""
        return self.registry.get_by_identity(object_id)

    def get_junction(self, junction_id: str) -> Junction:
        """Resolve one Junction through the Network-owned topology registry."""
        return self._junctions.get(junction_id)

    def contains_junction(self, junction_id: str) -> bool:
        return self._junctions.contains(junction_id)

    def validate(self) -> bool:
        """Validate the complete authoritative Network membership and endpoint graph."""
        registered = {element.id: element for element in self.registry._objects.values()}
        if len(registered) != len(self.registry._objects):
            raise ValueError("Network contains duplicate canonical identities.")
        junctions = self._junctions.snapshot
        junction_ids = {junction.junction_id for junction in junctions}
        if len(junction_ids) != len(junctions):
            raise ValueError("Network contains duplicate canonical Junction identities.")
        for junction in junctions:
            if junction._gridforge_network_token is not self._junctions._network_token:
                raise ValueError(f"Junction ownership token is invalid for '{junction.junction_id}'.")

        from core.model.base import ElectricalObject

        for element in self.registry._objects.values():
            if not isinstance(element, ElectricalObject):
                raise TypeError("Network contains a non-Core electrical object.")
            element.validate()
            if getattr(element, "_gridforge_network_token", None) is not self.registry._network_token:
                raise ValueError(f"Network membership token is invalid for '{element.id}'.")

            for terminal in getattr(element, "terminals", ()):
                if terminal.owner is not element:
                    raise ValueError(
                        f"Terminal '{terminal.role}' is not owned by '{element.id}'."
                    )
                endpoint = terminal.endpoint
                if endpoint is None:
                    continue
                if getattr(endpoint, "_gridforge_network_token", None) is not self.registry._network_token:
                    raise ValueError(
                        f"Terminal '{terminal.role}' on '{element.id}' references an object outside this Network."
                    )
                if registered.get(endpoint.id) is not endpoint:
                    raise ValueError(
                        f"Terminal '{terminal.role}' on '{element.id}' references an unregistered object '{endpoint.id}'."
                    )

        self.connectivity.validate(self)
        from .connectivity import ConnectivityResolver
        resolver = ConnectivityResolver(self)
        for element in self.registry._objects.values():
            for terminal in getattr(element, "terminals", ()):
                reference = self._reference_for_terminal(element, terminal.role)
                buses = resolver.bus_ids_for_terminal(reference)
                if len(buses) > 1:
                    raise ValueError(
                        f"Terminal '{terminal.role}' on '{element.id}' reaches multiple Bus endpoints: {buses!r}."
                    )
                physical = getattr(terminal.endpoint, "id", None)
                if physical is not None and buses and str(physical) != buses[0]:
                    raise ValueError(
                        f"Terminal '{terminal.role}' on '{element.id}' has contradictory physical/Simple Wire Bus identities."
                    )
        return True

    @staticmethod
    def _reference_for_terminal(element: Any, role: str):
        from core.model.endpoint_reference import EndpointReference, EquipmentType
        raw = str(getattr(element, "element_type", "")).strip().lower()
        if raw == "electrical_object":
            raw = type(element).__name__.strip().lower()
        return EndpointReference.terminal(
            equipment_type=EquipmentType(raw),
            equipment_id=element.id,
            terminal_role=role,
        )

    def _invalidate_topology(self, *, bus_membership: bool = False) -> None:
        self.state.invalidate_topology()
        self.topology.invalidate()
        if bus_membership:
            self.index.invalidate()

    def invalidate_topology(self) -> None:
        self._invalidate_topology()

    def _add(self, method: Any, element: Any, *, affects_topology: bool = False, affects_bus_index: bool = False) -> None:
        method(element)
        if affects_topology:
            self._invalidate_topology(bus_membership=affects_bus_index)

    def _remove(self, method: Any, element: Any, *, affects_topology: bool = False, affects_bus_index: bool = False) -> None:
        dependencies = self.connectivity.connections_for_equipment(getattr(element, "id", ""))
        if dependencies:
            raise ValueError(
                f"Cannot remove '{getattr(element, 'id', element)}': dependent Simple Wire relationships exist."
            )
        method(element)
        if affects_topology:
            self._invalidate_topology(bus_membership=affects_bus_index)

    @staticmethod
    def _has_physical_bus_attachment(element: Any) -> bool:
        return any(getattr(terminal, "endpoint", None) is not None for terminal in getattr(element, "terminals", ()))

    def add_bus(self, bus: Any) -> None: self._add(self.registry.add_bus, bus, affects_topology=True, affects_bus_index=True)
    def remove_bus(self, bus: Any) -> None: self._remove(self.registry.remove_bus, bus, affects_topology=True, affects_bus_index=True)
    def add_grid(self, grid: Any) -> None: self._add(self.registry.add_grid, grid, affects_topology=self._has_physical_bus_attachment(grid))
    def remove_grid(self, grid: Any) -> None: self._remove(self.registry.remove_grid, grid, affects_topology=self._has_physical_bus_attachment(grid))
    def add_generator(self, generator: Any) -> None: self._add(self.registry.add_generator, generator, affects_topology=self._has_physical_bus_attachment(generator))
    def remove_generator(self, generator: Any) -> None: self._remove(self.registry.remove_generator, generator, affects_topology=self._has_physical_bus_attachment(generator))
    def add_synchronous_machine(self, machine: Any) -> None: self._add(self.registry.add_synchronous_machine, machine, affects_topology=self._has_physical_bus_attachment(machine))
    def remove_synchronous_machine(self, machine: Any) -> None: self._remove(self.registry.remove_synchronous_machine, machine, affects_topology=self._has_physical_bus_attachment(machine))
    def add_load(self, load: Any) -> None: self._add(self.registry.add_load, load, affects_topology=self._has_physical_bus_attachment(load))
    def remove_load(self, load: Any) -> None: self._remove(self.registry.remove_load, load, affects_topology=self._has_physical_bus_attachment(load))
    def add_motor(self, motor: Any) -> None: self._add(self.registry.add_motor, motor, affects_topology=self._has_physical_bus_attachment(motor))
    def remove_motor(self, motor: Any) -> None: self._remove(self.registry.remove_motor, motor, affects_topology=self._has_physical_bus_attachment(motor))
    def add_shunt(self, shunt: Any) -> None: self._add(self.registry.add_shunt, shunt, affects_topology=self._has_physical_bus_attachment(shunt))
    def remove_shunt(self, shunt: Any) -> None: self._remove(self.registry.remove_shunt, shunt, affects_topology=self._has_physical_bus_attachment(shunt))
    def add_capacitor(self, capacitor: Any) -> None: self._add(self.registry.add_capacitor, capacitor, affects_topology=self._has_physical_bus_attachment(capacitor))
    def remove_capacitor(self, capacitor: Any) -> None: self._remove(self.registry.remove_capacitor, capacitor, affects_topology=self._has_physical_bus_attachment(capacitor))
    def add_reactor(self, reactor: Any) -> None: self._add(self.registry.add_reactor, reactor, affects_topology=self._has_physical_bus_attachment(reactor))
    def remove_reactor(self, reactor: Any) -> None: self._remove(self.registry.remove_reactor, reactor, affects_topology=self._has_physical_bus_attachment(reactor))
    def add_solar(self, solar: Any) -> None: self._add(self.registry.add_solar, solar, affects_topology=self._has_physical_bus_attachment(solar))
    def remove_solar(self, solar: Any) -> None: self._remove(self.registry.remove_solar, solar, affects_topology=self._has_physical_bus_attachment(solar))
    def add_battery(self, battery: Any) -> None: self._add(self.registry.add_battery, battery, affects_topology=self._has_physical_bus_attachment(battery))
    def remove_battery(self, battery: Any) -> None: self._remove(self.registry.remove_battery, battery, affects_topology=self._has_physical_bus_attachment(battery))
    def add_current_transformer(self, transformer: Any) -> None: self._add(self.registry.add_current_transformer, transformer, affects_topology=False)
    def remove_current_transformer(self, transformer: Any) -> None: self._remove(self.registry.remove_current_transformer, transformer, affects_topology=False)
    def add_capacitive_voltage_transformer(self, transformer: Any) -> None: self._add(self.registry.add_capacitive_voltage_transformer, transformer, affects_topology=False)
    def remove_capacitive_voltage_transformer(self, transformer: Any) -> None: self._remove(self.registry.remove_capacitive_voltage_transformer, transformer, affects_topology=False)
    def add_potential_transformer(self, transformer: Any) -> None: self._add(self.registry.add_potential_transformer, transformer, affects_topology=False)
    def remove_potential_transformer(self, transformer: Any) -> None: self._remove(self.registry.remove_potential_transformer, transformer, affects_topology=False)
    def add_relay(self, relay: Any) -> None: self._add(self.registry.add_relay, relay, affects_topology=False)
    def remove_relay(self, relay: Any) -> None: self._remove(self.registry.remove_relay, relay, affects_topology=False)
    def add_line(self, line: Any) -> None: self._add(self.registry.add_line, line, affects_topology=True)
    def remove_line(self, line: Any) -> None: self._remove(self.registry.remove_line, line, affects_topology=True)
    def add_cable(self, cable: Any) -> None: self._add(self.registry.add_cable, cable, affects_topology=True)
    def remove_cable(self, cable: Any) -> None: self._remove(self.registry.remove_cable, cable, affects_topology=True)
    def add_transformer(self, transformer: Any) -> None: self._add(self.registry.add_transformer, transformer, affects_topology=True)
    def remove_transformer(self, transformer: Any) -> None: self._remove(self.registry.remove_transformer, transformer, affects_topology=True)
    def add_breaker(self, breaker: Any) -> None: self._add(self.registry.add_breaker, breaker, affects_topology=True)
    def remove_breaker(self, breaker: Any) -> None: self._remove(self.registry.remove_breaker, breaker, affects_topology=True)
    def add_switch(self, switch: Any) -> None: self._add(self.registry.add_switch, switch, affects_topology=True)
    def remove_switch(self, switch: Any) -> None: self._remove(self.registry.remove_switch, switch, affects_topology=True)
    def add_disconnector(self, disconnector: Any) -> None: self._add(self.registry.add_disconnector, disconnector, affects_topology=True)
    def remove_disconnector(self, disconnector: Any) -> None: self._remove(self.registry.remove_disconnector, disconnector, affects_topology=True)
    def add_fuse(self, fuse: Any) -> None: self._add(self.registry.add_fuse, fuse, affects_topology=True)
    def remove_fuse(self, fuse: Any) -> None: self._remove(self.registry.remove_fuse, fuse, affects_topology=True)

    def add_junction(self, junction: Junction) -> None:
        if not isinstance(junction, Junction):
            raise TypeError("junction must be a Junction.")
        self._junctions.add(junction)

    def remove_junction(self, junction: Junction) -> None:
        self._junctions.remove(junction)

    def add_simple_wire_connection(self, connection: SimpleWireConnection) -> None:
        if not isinstance(connection, SimpleWireConnection):
            raise TypeError("connection must be a SimpleWireConnection.")
        if connection.endpoint_a.kind is not TopologyEndpointReferenceKind.TERMINAL:
            raise ValueError(
                "Simple Wire currently supports terminal topology endpoints only; "
                f"got {connection.endpoint_a.kind.value!r}."
            )
        if connection.endpoint_b.kind is not TopologyEndpointReferenceKind.TERMINAL:
            raise ValueError(
                "Simple Wire currently supports terminal topology endpoints only; "
                f"got {connection.endpoint_b.kind.value!r}."
            )
        endpoint_a = connection.endpoint_a.terminal_reference
        endpoint_b = connection.endpoint_b.terminal_reference
        EndpointCompatibility.validate_reference(endpoint_a, self)
        EndpointCompatibility.validate_reference(endpoint_b, self)
        EndpointCompatibility.validate_pair(endpoint_a, endpoint_b, self)
        self.connectivity.add(connection, self)
        self._invalidate_topology()

    def remove_simple_wire_connection(self, connection_id: str) -> SimpleWireConnection:
        connection = self.connectivity.remove(connection_id)
        self._invalidate_topology()
        return connection

    def get_simple_wire_connection(self, connection_id: str) -> SimpleWireConnection:
        return self.connectivity.get(connection_id)

    def rebuild_topology(self) -> dict[Any, set[Any]]:
        graph = self.topology._build()
        if self.topology.snapshot is None:
            self.state.topology_rebuilt(valid=False)
            raise RuntimeError("TopologyManager did not produce a valid TopologySnapshot.")
        self.state.topology_rebuilt(valid=True)
        return graph

    @property
    def topology_snapshot(self):
        """Return the current immutable runtime-derived topology snapshot."""
        if self.topology_dirty:
            return None
        return self.topology.snapshot

    def conduction_state(self, element: Any) -> bool:
        return conduction_state(element)

    def ensure_bus_index(self) -> None:
        self.index.ensure(self.buses)

    @property
    def topology_revision(self) -> int: return self.state.topology_revision
    @property
    def topology_valid(self) -> bool: return self.state.topology_valid
    @property
    def topology_dirty(self) -> bool: return self.state.topology_dirty
    @property
    def index_valid(self) -> bool: return self.index.valid

    def __repr__(self) -> str:
        return ("Network(" f"buses={len(self.buses)}, " f"branches={len(self.branches)}, " f"junctions={len(self._junctions)}, " f"simple_wires={len(self.connectivity.connections)}, " f"relays={len(self.relays)}, " f"topology_revision={self.topology_revision}, " f"topology_valid={self.topology_valid}, " f"index_valid={self.index_valid}" ")")


__all__ = ["Network"]
