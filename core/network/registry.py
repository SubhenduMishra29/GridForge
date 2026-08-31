# ============================================================

# File: core/network/registry.py

# GridForge V2 — Network Registry

# Author: Subhendu Mishra

# ============================================================

"""
Canonical registry for electrical equipment belonging to a Network.

Registry owns:
- typed equipment collections;
- registration/removal;
- deterministic ID lookup.

Registry does NOT own:
- topology;
- topology validity/revision;
- numerical matrices;
- equipment physics;
- UI/SLD state;
- plugin lifecycle.

Network is the public mutation façade.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

class NetworkRegistry:
"""Typed canonical membership registry for a Network."""

```
def __init__(self) -> None:
    self._buses: Dict[str, Any] = {}
    self._grids: Dict[str, Any] = {}
    self._generators: Dict[str, Any] = {}
    self._synchronous_machines: Dict[str, Any] = {}
    self._loads: Dict[str, Any] = {}
    self._motors: Dict[str, Any] = {}
    self._shunts: Dict[str, Any] = {}
    self._capacitors: Dict[str, Any] = {}
    self._reactors: Dict[str, Any] = {}
    self._solar: Dict[str, Any] = {}
    self._batteries: Dict[str, Any] = {}

    self._branches: Dict[str, Any] = {}
    self._lines: Dict[str, Any] = {}
    self._cables: Dict[str, Any] = {}
    self._transformers: Dict[str, Any] = {}

    self._breakers: Dict[str, Any] = {}
    self._switches: Dict[str, Any] = {}
    self._disconnectors: Dict[str, Any] = {}
    self._fuses: Dict[str, Any] = {}

# ========================================================
# COLLECTIONS
# ========================================================

@property
def buses(self) -> Tuple[Any, ...]:
    return tuple(self._buses.values())

@property
def grids(self) -> Tuple[Any, ...]:
    return tuple(self._grids.values())

@property
def generators(self) -> Tuple[Any, ...]:
    return tuple(self._generators.values())

@property
def synchronous_machines(self) -> Tuple[Any, ...]:
    return tuple(self._synchronous_machines.values())

@property
def loads(self) -> Tuple[Any, ...]:
    return tuple(self._loads.values())

@property
def motors(self) -> Tuple[Any, ...]:
    return tuple(self._motors.values())

@property
def shunts(self) -> Tuple[Any, ...]:
    return tuple(self._shunts.values())

@property
def capacitors(self) -> Tuple[Any, ...]:
    return tuple(self._capacitors.values())

@property
def reactors(self) -> Tuple[Any, ...]:
    return tuple(self._reactors.values())

@property
def solar(self) -> Tuple[Any, ...]:
    return tuple(self._solar.values())

@property
def batteries(self) -> Tuple[Any, ...]:
    return tuple(self._batteries.values())

@property
def branches(self) -> Tuple[Any, ...]:
    return tuple(self._branches.values())

@property
def lines(self) -> Tuple[Any, ...]:
    return tuple(self._lines.values())

@property
def cables(self) -> Tuple[Any, ...]:
    return tuple(self._cables.values())

@property
def transformers(self) -> Tuple[Any, ...]:
    return tuple(self._transformers.values())

@property
def breakers(self) -> Tuple[Any, ...]:
    return tuple(self._breakers.values())

@property
def switches(self) -> Tuple[Any, ...]:
    return tuple(self._switches.values())

@property
def disconnectors(self) -> Tuple[Any, ...]:
    return tuple(self._disconnectors.values())

@property
def fuses(self) -> Tuple[Any, ...]:
    return tuple(self._fuses.values())

# ========================================================
# INTERNAL REGISTRATION
# ========================================================

@staticmethod
def _object_id(element: Any) -> str:
    """Return the stable identifier required for registration."""

    object_id = getattr(element, "id", None)

    if object_id is None:
        raise ValueError(
            "Network elements must provide a stable 'id'."
        )

    return str(object_id)

@staticmethod
def _add(
    collection: Dict[str, Any],
    element: Any,
) -> None:
    """Register one element and reject duplicate IDs."""

    object_id = NetworkRegistry._object_id(element)

    if object_id in collection:
        raise ValueError(
            f"Duplicate network element ID: {object_id}"
        )

    collection[object_id] = element

@staticmethod
def _remove(
    collection: Dict[str, Any],
    element: Any,
) -> None:
    """Remove one element by its stable ID."""

    object_id = NetworkRegistry._object_id(element)

    if object_id not in collection:
        raise KeyError(
            f"Network element is not registered: {object_id}"
        )

    del collection[object_id]

# ========================================================
# BUS / SOURCE / INJECTION EQUIPMENT
# ========================================================

def add_bus(self, bus: Any) -> None:
    self._add(self._buses, bus)

def remove_bus(self, bus: Any) -> None:
    self._remove(self._buses, bus)

def add_grid(self, grid: Any) -> None:
    self._add(self._grids, grid)

def remove_grid(self, grid: Any) -> None:
    self._remove(self._grids, grid)

def add_generator(self, generator: Any) -> None:
    self._add(self._generators, generator)

def remove_generator(self, generator: Any) -> None:
    self._remove(self._generators, generator)

def add_synchronous_machine(self, machine: Any) -> None:
    self._add(
        self._synchronous_machines,
        machine,
    )

def remove_synchronous_machine(self, machine: Any) -> None:
    self._remove(
        self._synchronous_machines,
        machine,
    )

def add_load(self, load: Any) -> None:
    self._add(self._loads, load)

def remove_load(self, load: Any) -> None:
    self._remove(self._loads, load)

def add_motor(self, motor: Any) -> None:
    self._add(self._motors, motor)

def remove_motor(self, motor: Any) -> None:
    self._remove(self._motors, motor)

def add_shunt(self, shunt: Any) -> None:
    self._add(self._shunts, shunt)

def remove_shunt(self, shunt: Any) -> None:
    self._remove(self._shunts, shunt)

def add_capacitor(self, capacitor: Any) -> None:
    self._add(self._capacitors, capacitor)

def remove_capacitor(self, capacitor: Any) -> None:
    self._remove(self._capacitors, capacitor)

def add_reactor(self, reactor: Any) -> None:
    self._add(self._reactors, reactor)

def remove_reactor(self, reactor: Any) -> None:
    self._remove(self._reactors, reactor)

def add_solar(self, solar: Any) -> None:
    self._add(self._solar, solar)

def remove_solar(self, solar: Any) -> None:
    self._remove(self._solar, solar)

def add_battery(self, battery: Any) -> None:
    self._add(self._batteries, battery)

def remove_battery(self, battery: Any) -> None:
    self._remove(self._batteries, battery)

# ========================================================
# TOPOLOGY BRANCHES
# ========================================================

def add_branch(self, branch: Any) -> None:
    self._add(self._branches, branch)

def remove_branch(self, branch: Any) -> None:
    self._remove(self._branches, branch)

def add_line(self, line: Any) -> None:
    self._add(self._lines, line)

def remove_line(self, line: Any) -> None:
    self._remove(self._lines, line)

def add_cable(self, cable: Any) -> None:
    self._add(self._cables, cable)

def remove_cable(self, cable: Any) -> None:
    self._remove(self._cables, cable)

def add_transformer(self, transformer: Any) -> None:
    self._add(
        self._transformers,
        transformer,
    )

def remove_transformer(self, transformer: Any) -> None:
    self._remove(
        self._transformers,
        transformer,
    )

# ========================================================
# SWITCHING EQUIPMENT
# ========================================================

def add_breaker(self, breaker: Any) -> None:
    self._add(self._breakers, breaker)

def remove_breaker(self, breaker: Any) -> None:
    self._remove(self._breakers, breaker)

def add_switch(self, switch: Any) -> None:
    self._add(self._switches, switch)

def remove_switch(self, switch: Any) -> None:
    self._remove(self._switches, switch)

def add_disconnector(
    self,
    disconnector: Any,
) -> None:
    self._add(
        self._disconnectors,
        disconnector,
    )

def remove_disconnector(
    self,
    disconnector: Any,
) -> None:
    self._remove(
        self._disconnectors,
        disconnector,
    )

def add_fuse(self, fuse: Any) -> None:
    self._add(self._fuses, fuse)

def remove_fuse(self, fuse: Any) -> None:
    self._remove(self._fuses, fuse)

# ========================================================
# LOOKUP
# ========================================================

def get_by_id(
    self,
    element_type: str,
    object_id: str,
) -> Any:
    """
    Return an element by canonical type name and ID.

    Raises:
        KeyError: if the type or ID is not registered.
    """

    collections = {
        "bus": self._buses,
        "grid": self._grids,
        "generator": self._generators,
        "synchronous_machine": self._synchronous_machines,
        "load": self._loads,
        "motor": self._motors,
        "shunt": self._shunts,
        "capacitor": self._capacitors,
        "reactor": self._reactors,
        "solar": self._solar,
        "battery": self._batteries,
        "branch": self._branches,
        "line": self._lines,
        "cable": self._cables,
        "transformer": self._transformers,
        "breaker": self._breakers,
        "switch": self._switches,
        "disconnector": self._disconnectors,
        "fuse": self._fuses,
    }

    try:
        collection = collections[element_type.lower()]
    except KeyError as exc:
        raise KeyError(
            f"Unknown network element type: {element_type}"
        ) from exc

    try:
        return collection[str(object_id)]
    except KeyError as exc:
        raise KeyError(
            f"Network element is not registered: "
            f"{element_type}:{object_id}"
        ) from exc
```

__all__ = ["NetworkRegistry"]
