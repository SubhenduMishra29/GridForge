# ============================================================

# File: core/network/network.py

# GridForge V2 — Network Aggregate

# Author: Subhendu Mishra

# ============================================================

"""
Authoritative electrical Network aggregate.

Network owns:
- canonical equipment membership through NetworkRegistry;
- derived topology through TopologyManager;
- topology lifecycle through NetworkState;
- canonical bus indexing through BusIndex.

Network does NOT:
- implement equipment physics;
- resolve or mutate model terminals;
- implement topology algorithms;
- construct Y-bus or other numerical matrices;
- perform numerical solving;
- own UI/SLD state.

Application commands/services should use Network as the
controlled mutation façade.
"""

from __future__ import annotations

from typing import Any, Optional

from .indexing import BusIndex
from .registry import NetworkRegistry
from .state import NetworkState
from .topology import TopologyManager

class Network:
"""Authoritative electrical network aggregate."""

```
def __init__(
    self,
    *,
    registry: Optional[NetworkRegistry] = None,
    topology: Optional[TopologyManager] = None,
    state: Optional[NetworkState] = None,
    index: Optional[BusIndex] = None,
) -> None:
    self.registry = registry or NetworkRegistry()
    self.state = state or NetworkState()
    self.index = index or BusIndex()

    if topology is None:
        self.topology = TopologyManager(self)
    else:
        if getattr(topology, "network", self) is not self:
            raise ValueError(
                "TopologyManager belongs to a different Network."
            )
        self.topology = topology

# ========================================================
# CANONICAL COLLECTIONS
# ========================================================

@property
def buses(self) -> tuple[Any, ...]:
    return self.registry.buses

@property
def grids(self) -> tuple[Any, ...]:
    return self.registry.grids

@property
def generators(self) -> tuple[Any, ...]:
    return self.registry.generators

@property
def synchronous_machines(self) -> tuple[Any, ...]:
    return self.registry.synchronous_machines

@property
def loads(self) -> tuple[Any, ...]:
    return self.registry.loads

@property
def motors(self) -> tuple[Any, ...]:
    return self.registry.motors

@property
def shunts(self) -> tuple[Any, ...]:
    return self.registry.shunts

@property
def capacitors(self) -> tuple[Any, ...]:
    return self.registry.capacitors

@property
def reactors(self) -> tuple[Any, ...]:
    return self.registry.reactors

@property
def solar(self) -> tuple[Any, ...]:
    return self.registry.solar

@property
def batteries(self) -> tuple[Any, ...]:
    return self.registry.batteries

@property
def branches(self) -> tuple[Any, ...]:
    return self.registry.branches

@property
def lines(self) -> tuple[Any, ...]:
    return self.registry.lines

@property
def cables(self) -> tuple[Any, ...]:
    return self.registry.cables

@property
def transformers(self) -> tuple[Any, ...]:
    return self.registry.transformers

@property
def breakers(self) -> tuple[Any, ...]:
    return self.registry.breakers

@property
def switches(self) -> tuple[Any, ...]:
    return self.registry.switches

@property
def disconnectors(self) -> tuple[Any, ...]:
    return self.registry.disconnectors

@property
def fuses(self) -> tuple[Any, ...]:
    return self.registry.fuses

# ========================================================
# LOOKUP
# ========================================================

def get_by_id(
    self,
    element_type: str,
    object_id: str,
) -> Any:
    """Return the canonical registered model instance."""

    return self.registry.get_by_id(
        element_type,
        object_id,
    )

# ========================================================
# DERIVED-STATE INVALIDATION
# ========================================================

def _invalidate_topology(
    self,
    *,
    invalidate_index: bool = False,
) -> None:
    """Invalidate topology and optionally the BusIndex."""

    self.state.invalidate_topology()
    self.topology.invalidate()

    if invalidate_index:
        self.index.invalidate()

def _add(
    self,
    register,
    element: Any,
    *,
    topology: bool = False,
    bus: bool = False,
) -> None:
    """Register equipment and invalidate derived state."""

    register(element)

    if topology or bus:
        self._invalidate_topology(
            invalidate_index=bus,
        )

def _remove(
    self,
    unregister,
    element: Any,
    *,
    topology: bool = False,
    bus: bool = False,
) -> None:
    """Remove equipment and invalidate derived state."""

    unregister(element)

    if topology or bus:
        self._invalidate_topology(
            invalidate_index=bus,
        )

# ========================================================
# BUS
# ========================================================

def add_bus(self, bus: Any) -> None:
    self._add(
        self.registry.add_bus,
        bus,
        topology=True,
        bus=True,
    )

def remove_bus(self, bus: Any) -> None:
    self._remove(
        self.registry.remove_bus,
        bus,
        topology=True,
        bus=True,
    )

# ========================================================
# BUS-CONNECTED ELECTRICAL EQUIPMENT
# ========================================================

def add_grid(self, grid: Any) -> None:
    self._add(self.registry.add_grid, grid)

def remove_grid(self, grid: Any) -> None:
    self._remove(self.registry.remove_grid, grid)

def add_generator(self, generator: Any) -> None:
    self._add(self.registry.add_generator, generator)

def remove_generator(self, generator: Any) -> None:
    self._remove(self.registry.remove_generator, generator)

def add_synchronous_machine(self, machine: Any) -> None:
    self._add(
        self.registry.add_synchronous_machine,
        machine,
    )

def remove_synchronous_machine(self, machine: Any) -> None:
    self._remove(
        self.registry.remove_synchronous_machine,
        machine,
    )

def add_load(self, load: Any) -> None:
    self._add(self.registry.add_load, load)

def remove_load(self, load: Any) -> None:
    self._remove(self.registry.remove_load, load)

def add_motor(self, motor: Any) -> None:
    self._add(self.registry.add_motor, motor)

def remove_motor(self, motor: Any) -> None:
    self._remove(self.registry.remove_motor, motor)

def add_shunt(self, shunt: Any) -> None:
    self._add(self.registry.add_shunt, shunt)

def remove_shunt(self, shunt: Any) -> None:
    self._remove(self.registry.remove_shunt, shunt)

def add_capacitor(self, capacitor: Any) -> None:
    self._add(self.registry.add_capacitor, capacitor)

def remove_capacitor(self, capacitor: Any) -> None:
    self._remove(self.registry.remove_capacitor, capacitor)

def add_reactor(self, reactor: Any) -> None:
    self._add(self.registry.add_reactor, reactor)

def remove_reactor(self, reactor: Any) -> None:
    self._remove(self.registry.remove_reactor, reactor)

def add_solar(self, solar: Any) -> None:
    self._add(self.registry.add_solar, solar)

def remove_solar(self, solar: Any) -> None:
    self._remove(self.registry.remove_solar, solar)

def add_battery(self, battery: Any) -> None:
    self._add(self.registry.add_battery, battery)

def remove_battery(self, battery: Any) -> None:
    self._remove(self.registry.remove_battery, battery)

# ========================================================
# TOPOLOGY BRANCHES
# ========================================================

def add_branch(self, branch: Any) -> None:
    self._add(
        self.registry.add_branch,
        branch,
        topology=True,
    )

def remove_branch(self, branch: Any) -> None:
    self._remove(
        self.registry.remove_branch,
        branch,
        topology=True,
    )

def add_line(self, line: Any) -> None:
    self._add(
        self.registry.add_line,
        line,
        topology=True,
    )

def remove_line(self, line: Any) -> None:
    self._remove(
        self.registry.remove_line,
        line,
        topology=True,
    )

def add_cable(self, cable: Any) -> None:
    self._add(
        self.registry.add_cable,
        cable,
        topology=True,
    )

def remove_cable(self, cable: Any) -> None:
    self._remove(
        self.registry.remove_cable,
        cable,
        topology=True,
    )

def add_transformer(self, transformer: Any) -> None:
    self._add(
        self.registry.add_transformer,
        transformer,
        topology=True,
    )

def remove_transformer(self, transformer: Any) -> None:
    self._remove(
        self.registry.remove_transformer,
        transformer,
        topology=True,
    )

# ========================================================
# SWITCHING EQUIPMENT
# ========================================================

def add_breaker(self, breaker: Any) -> None:
    self._add(
        self.registry.add_breaker,
        breaker,
        topology=True,
    )

def remove_breaker(self, breaker: Any) -> None:
    self._remove(
        self.registry.remove_breaker,
        breaker,
        topology=True,
    )

def add_switch(self, switch: Any) -> None:
    self._add(
        self.registry.add_switch,
        switch,
        topology=True,
    )

def remove_switch(self, switch: Any) -> None:
    self._remove(
        self.registry.remove_switch,
        switch,
        topology=True,
    )

def add_disconnector(
    self,
    disconnector: Any,
) -> None:
    self._add(
        self.registry.add_disconnector,
        disconnector,
        topology=True,
    )

def remove_disconnector(
    self,
    disconnector: Any,
) -> None:
    self._remove(
        self.registry.remove_disconnector,
        disconnector,
        topology=True,
    )

def add_fuse(self, fuse: Any) -> None:
    self._add(
        self.registry.add_fuse,
        fuse,
        topology=True,
    )

def remove_fuse(self, fuse: Any) -> None:
    self._remove(
        self.registry.remove_fuse,
        fuse,
        topology=True,
    )

# ========================================================
# TOPOLOGY PREPARATION
# ========================================================

def rebuild_topology(self) -> dict[Any, set[Any]]:
    """Rebuild derived topology and synchronize NetworkState."""

    graph = self.topology.build()
    self.state.topology_rebuilt()

    return graph

# ========================================================
# NUMERICAL INDEX PREPARATION
# ========================================================

def rebuild_index(self) -> None:
    """Rebuild the canonical numerical BusIndex."""

    self.index.rebuild(self.buses)

# ========================================================
# EXPLICIT PREPARATION
# ========================================================

def prepare(self) -> None:
    """
    Prepare structural Network representations.

    This prepares topology and BusIndex only.
    Numerical matrices remain the responsibility of Numerical.
    """

    self.rebuild_topology()
    self.rebuild_index()

# ========================================================
# STATE ACCESS
# ========================================================

@property
def topology_revision(self) -> int:
    return self.state.topology_revision

@property
def topology_valid(self) -> bool:
    return self.state.topology_valid

@property
def index_valid(self) -> bool:
    return self.index.valid

# ========================================================
# REPRESENTATION
# ========================================================

def __repr__(self) -> str:
    return (
        "Network("
        f"buses={len(self.buses)}, "
        f"lines={len(self.lines)}, "
        f"transformers={len(self.transformers)}, "
        f"topology_revision={self.topology_revision}, "
        f"topology_valid={self.topology_valid}, "
        f"index_valid={self.index_valid}"
        ")"
    )
```

__all__ = ["Network"]
