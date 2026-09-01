# ============================================================

# File: core/network/registry.py

# GridForge V2 — Network Registry

# Author: Subhendu Mishra

# ============================================================

"""
Typed registry for canonical electrical Network equipment.

Registry owns membership only.

It does not:
- build topology;
- validate electrical connectivity;
- calculate numerical values;
- manage UI/SLD state;
- manage plugins.
"""

from __future__ import annotations

from typing import Any

class NetworkRegistry:
"""Store canonical Network equipment by stable object ID."""

```
def __init__(self) -> None:
    self._buses: dict[str, Any] = {}
    self._grids: dict[str, Any] = {}
    self._generators: dict[str, Any] = {}
    self._synchronous_machines: dict[str, Any] = {}
    self._loads: dict[str, Any] = {}
    self._motors: dict[str, Any] = {}
    self._shunts: dict[str, Any] = {}
    self._capacitors: dict[str, Any] = {}
    self._reactors: dict[str, Any] = {}
    self._solar: dict[str, Any] = {}
    self._batteries: dict[str, Any] = {}

    self._branches: dict[str, Any] = {}
    self._lines: dict[str, Any] = {}
    self._cables: dict[str, Any] = {}
    self._transformers: dict[str, Any] = {}

    self._breakers: dict[str, Any] = {}
    self._switches: dict[str, Any] = {}
    self._disconnectors: dict[str, Any] = {}
    self._fuses: dict[str, Any] = {}

# ========================================================
# COLLECTION ACCESS
# ========================================================

@staticmethod
def _values(collection: dict[str, Any]) -> tuple[Any, ...]:
    """Return a read-only snapshot of a collection."""

    return tuple(collection.values())

@property
def buses(self) -> tuple[Any, ...]:
    return self._values(self._buses)

@property
def grids(self) -> tuple[Any, ...]:
    return self._values(self._grids)

@property
def generators(self) -> tuple[Any, ...]:
    return self._values(self._generators)

@property
def synchronous_machines(self) -> tuple[Any, ...]:
    return self._values(self._synchronous_machines)

@property
def loads(self) -> tuple[Any, ...]:
    return self._values(self._loads)

@property
def motors(self) -> tuple[Any, ...]:
    return self._values(self._motors)

@property
def shunts(self) -> tuple[Any, ...]:
    return self._values(self._shunts)

@property
def capacitors(self) -> tuple[Any, ...]:
    return self._values(self._capacitors)

@property
def reactors(self) -> tuple[Any, ...]:
    return self._values(self._reactors)

@property
def solar(self) -> tuple[Any, ...]:
    return self._values(self._solar)

@property
def batteries(self) -> tuple[Any, ...]:
    return self._values(self._batteries)

@property
def branches(self) -> tuple[Any, ...]:
    return self._values(self._branches)

@property
def lines(self) -> tuple[Any, ...]:
    return self._values(self._lines)

@property
def cables(self) -> tuple[Any, ...]:
    return self._values(self._cables)

@property
def transformers(self) -> tuple[Any, ...]:
    return self._values(self._transformers)

@property
def breakers(self) -> tuple[Any, ...]:
    return self._values(self._breakers)

@property
def switches(self) -> tuple[Any, ...]:
    return self._values(self._switches)

@property
def disconnectors(self) -> tuple[Any, ...]:
    return self._values(self._disconnectors)

@property
def fuses(self) -> tuple[Any, ...]:
    return self._values(self._fuses)

# ========================================================
# REGISTRATION
# ========================================================

@staticmethod
def _id(element: Any) -> str:
    """Return the required stable model ID."""

    value = getattr(element, "id", None)

    if value is None:
        raise ValueError(
            "Network elements must provide an 'id'."
        )

    return str(value)

@classmethod
def _add(
    cls,
    collection: dict[str, Any],
    element: Any,
) -> None:
    """Register an element and reject duplicate IDs."""

    object_id = cls._id(element)

    if object_id in collection:
        raise ValueError(
            f"Duplicate network element ID: {object_id}"
        )

    collection[object_id] = element

@classmethod
def _remove(
    cls,
    collection: dict[str, Any],
    element: Any,
) -> None:
    """Remove a registered element."""

    object_id = cls._id(element)

    if object_id not in collection:
        raise KeyError(
            f"Network element is not registered: {object_id}"
        )

    del collection[object_id]

# ========================================================
# BUS / INJECTION EQUIPMENT
# ========================================================

def add_bus(self, element: Any) -> None:
    self._add(self._buses, element)

def remove_bus(self, element: Any) -> None:
    self._remove(self._buses, element)

def add_grid(self, element: Any) -> None:
    self._add(self._grids, element)

def remove_grid(self, element: Any) -> None:
    self._remove(self._grids, element)

def add_generator(self, element: Any) -> None:
    self._add(self._generators, element)

def remove_generator(self, element: Any) -> None:
    self._remove(self._generators, element)

def add_synchronous_machine(self, element: Any) -> None:
    self._add(self._synchronous_machines, element)

def remove_synchronous_machine(self, element: Any) -> None:
    self._remove(self._synchronous_machines, element)

def add_load(self, element: Any) -> None:
    self._add(self._loads, element)

def remove_load(self, element: Any) -> None:
    self._remove(self._loads, element)

def add_motor(self, element: Any) -> None:
    self._add(self._motors, element)

def remove_motor(self, element: Any) -> None:
    self._remove(self._motors, element)

def add_shunt(self, element: Any) -> None:
    self._add(self._shunts, element)

def remove_shunt(self, element: Any) -> None:
    self._remove(self._shunts, element)

def add_capacitor(self, element: Any) -> None:
    self._add(self._capacitors, element)

def remove_capacitor(self, element: Any) -> None:
    self._remove(self._capacitors, element)

def add_reactor(self, element: Any) -> None:
    self._add(self._reactors, element)

def remove_reactor(self, element: Any) -> None:
    self._remove(self._reactors, element)

def add_solar(self, element: Any) -> None:
    self._add(self._solar, element)

def remove_solar(self, element: Any) -> None:
    self._remove(self._solar, element)

def add_battery(self, element: Any) -> None:
    self._add(self._batteries, element)

def remove_battery(self, element: Any) -> None:
    self._remove(self._batteries, element)

# ========================================================
# BRANCH EQUIPMENT
# ========================================================

def add_branch(self, element: Any) -> None:
    self._add(self._branches, element)

def remove_branch(self, element: Any) -> None:
    self._remove(self._branches, element)

def add_line(self, element: Any) -> None:
    self._add(self._lines, element)

def remove_line(self, element: Any) -> None:
    self._remove(self._lines, element)

def add_cable(self, element: Any) -> None:
    self._add(self._cables, element)

def remove_cable(self, element: Any) -> None:
    self._remove(self._cables, element)

def add_transformer(self, element: Any) -> None:
    self._add(self._transformers, element)

def remove_transformer(self, element: Any) -> None:
    self._remove(self._transformers, element)

# ========================================================
# SWITCHING EQUIPMENT
# ========================================================

def add_breaker(self, element: Any) -> None:
    self._add(self._breakers, element)

def remove_breaker(self, element: Any) -> None:
    self._remove(self._breakers, element)

def add_switch(self, element: Any) -> None:
    self._add(self._switches, element)

def remove_switch(self, element: Any) -> None:
    self._remove(self._switches, element)

def add_disconnector(self, element: Any) -> None:
    self._add(self._disconnectors, element)

def remove_disconnector(self, element: Any) -> None:
    self._remove(self._disconnectors, element)

def add_fuse(self, element: Any) -> None:
    self._add(self._fuses, element)

def remove_fuse(self, element: Any) -> None:
    self._remove(self._fuses, element)

# ========================================================
# LOOKUP
# ========================================================

def get_by_id(
    self,
    element_type: str,
    object_id: str,
) -> Any:
    """Return an element from a canonical typed collection."""

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

    key = element_type.strip().lower()

    if key not in collections:
        raise KeyError(
            f"Unknown network element type: {element_type}"
        )

    try:
        return collections[key][str(object_id)]
    except KeyError as exc:
        raise KeyError(
            f"Network element is not registered: "
            f"{element_type}:{object_id}"
        ) from exc
```

__all__ = ["NetworkRegistry"]
