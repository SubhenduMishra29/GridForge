# ============================================================
# File: core/network/registry.py
# GridForge V2 — Authoritative Network Registry
# Author: Subhendu Mishra
# ============================================================

"""Authoritative Network membership and identity registry."""

from __future__ import annotations

from typing import Any

from core.model import (
    Battery,
    Breaker,
    Bus,
    Cable,
    Capacitor,
    CVT,
    CurrentTransformer,
    Disconnector,
    ElectricalObject,
    Fuse,
    Generator,
    Grid,
    Line,
    Load,
    Motor,
    PT,
    Reactor,
    Relay,
    Shunt,
    Solar,
    Switch,
    SynchronousMachine,
    Transformer,
)


_SUPPORTED_TYPES = (
    Bus,
    Grid,
    Generator,
    SynchronousMachine,
    Load,
    Motor,
    Shunt,
    Capacitor,
    Reactor,
    Solar,
    Battery,
    CurrentTransformer,
    PT,
    CVT,
    Relay,
    Line,
    Cable,
    Transformer,
    Breaker,
    Switch,
    Disconnector,
    Fuse,
)

_COLLECTION_TYPES: dict[str, tuple[type[Any], ...]] = {
    "bus": (Bus,),
    "grid": (Grid,),
    "generator": (Generator,),
    "synchronous_machine": (SynchronousMachine,),
    "load": (Load,),
    "motor": (Motor,),
    "shunt": (Shunt,),
    "capacitor": (Capacitor,),
    "reactor": (Reactor,),
    "solar": (Solar,),
    "battery": (Battery,),
    "current_transformer": (CurrentTransformer,),
    "potential_transformer": (PT,),
    "capacitive_voltage_transformer": (CVT,),
    "relay": (Relay,),
    "line": (Line,),
    "cable": (Cable,),
    "transformer": (Transformer,),
    "breaker": (Breaker,),
    "switch": (Switch,),
    "disconnector": (Disconnector,),
    "fuse": (Fuse,),
}

_TYPE_ALIASES = {
    "ct": "current_transformer",
    "current_transformer": "current_transformer",
    "pt": "potential_transformer",
    "potential_transformer": "potential_transformer",
    "cvt": "capacitive_voltage_transformer",
    "capacitive_voltage_transformer": "capacitive_voltage_transformer",
    "relay": "relay",
    "relays": "relay",
}


class NetworkRegistry:
    """Own the single authoritative membership/identity set for a Network.

    Typed collections are projections of the canonical identity map; they are
    not independent authorities.
    """

    def __init__(self) -> None:
        self._objects: dict[str, ElectricalObject] = {}
        self._network_token = object()

    @staticmethod
    def _values(collection: tuple[Any, ...]) -> tuple[Any, ...]:
        return collection

    def _typed(self, key: str) -> tuple[Any, ...]:
        types = _COLLECTION_TYPES[key]
        return tuple(
            obj for obj in self._objects.values()
            if isinstance(obj, types)
        )

    @property
    def buses(self) -> tuple[Any, ...]: return self._typed("bus")
    @property
    def grids(self) -> tuple[Any, ...]: return self._typed("grid")
    @property
    def generators(self) -> tuple[Any, ...]: return self._typed("generator")
    @property
    def synchronous_machines(self) -> tuple[Any, ...]: return self._typed("synchronous_machine")
    @property
    def loads(self) -> tuple[Any, ...]: return self._typed("load")
    @property
    def motors(self) -> tuple[Any, ...]: return self._typed("motor")
    @property
    def shunts(self) -> tuple[Any, ...]: return self._typed("shunt")
    @property
    def capacitors(self) -> tuple[Any, ...]: return self._typed("capacitor")
    @property
    def reactors(self) -> tuple[Any, ...]: return self._typed("reactor")
    @property
    def solar(self) -> tuple[Any, ...]: return self._typed("solar")
    @property
    def batteries(self) -> tuple[Any, ...]: return self._typed("battery")
    @property
    def current_transformers(self) -> tuple[Any, ...]: return self._typed("current_transformer")
    @property
    def potential_transformers(self) -> tuple[Any, ...]: return self._typed("potential_transformer")
    @property
    def capacitive_voltage_transformers(self) -> tuple[Any, ...]: return self._typed("capacitive_voltage_transformer")
    @property
    def relays(self) -> tuple[Any, ...]: return self._typed("relay")
    @property
    def lines(self) -> tuple[Any, ...]: return self._typed("line")
    @property
    def cables(self) -> tuple[Any, ...]: return self._typed("cable")
    @property
    def transformers(self) -> tuple[Any, ...]: return self._typed("transformer")
    @property
    def branches(self) -> tuple[Any, ...]: return (*self.lines, *self.cables, *self.transformers)
    @property
    def breakers(self) -> tuple[Any, ...]: return self._typed("breaker")
    @property
    def switches(self) -> tuple[Any, ...]: return self._typed("switch")
    @property
    def disconnectors(self) -> tuple[Any, ...]: return self._typed("disconnector")
    @property
    def fuses(self) -> tuple[Any, ...]: return self._typed("fuse")

    @staticmethod
    def _id(element: Any) -> str:
        value = getattr(element, "id", None)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Network elements must provide a non-empty string 'id'.")
        return value.strip()

    @staticmethod
    def _validate_supported(element: Any) -> ElectricalObject:
        if not isinstance(element, ElectricalObject):
            raise TypeError(
                "Only supported Core ElectricalObject instances may enter the Network."
            )
        if not isinstance(element, _SUPPORTED_TYPES):
            raise TypeError(
                f"Unsupported Core Network object type: {type(element).__name__}."
            )
        object_id = NetworkRegistry._id(element)
        if object_id != element.id:
            raise ValueError("Canonical object identity must be the immutable Core object id.")
        element.validate()
        for terminal in getattr(element, "terminals", ()):
            if terminal.owner is not element:
                raise ValueError(
                    f"Terminal '{terminal.role}' is not owned by its canonical Equipment object."
                )
            terminal.validate()
        return element

    def _bind(self, element: ElectricalObject) -> None:
        object.__setattr__(element, "_gridforge_network_token", self._network_token)
        for terminal in getattr(element, "terminals", ()):
            terminal._bind_network(self._network_token)

    def _unbind(self, element: ElectricalObject) -> None:
        for terminal in getattr(element, "terminals", ()):
            terminal._bind_network(None)
        if getattr(element, "_gridforge_network_token", None) is self._network_token:
            object.__setattr__(element, "_gridforge_network_token", None)

    def add(self, element: Any) -> None:
        """Register one supported Core object under its canonical identity."""
        element = self._validate_supported(element)
        object_id = self._id(element)
        existing = self._objects.get(object_id)
        if existing is not None:
            raise ValueError(f"Duplicate canonical network element ID: {object_id}")
        for terminal in getattr(element, "terminals", ()):
            endpoint = terminal.endpoint
            if endpoint is None:
                continue
            endpoint_token = getattr(endpoint, "_gridforge_network_token", None)
            if endpoint_token is not None and endpoint_token is not self._network_token:
                raise ValueError(
                    f"Terminal '{terminal.role}' on '{object_id}' references an object from another Network."
                )
            if endpoint_token is None and isinstance(endpoint, ElectricalObject):
                registered = self._objects.get(endpoint.id)
                if registered is not endpoint:
                    raise ValueError(
                        f"Terminal '{terminal.role}' on '{object_id}' references an object "
                        "that is not registered in this Network."
                    )
        self._objects[object_id] = element
        self._bind(element)

    def remove(self, element: Any) -> None:
        """Remove one canonical object, rejecting dangling external references."""
        if not isinstance(element, ElectricalObject):
            raise TypeError("Only Core ElectricalObject instances may be removed.")
        object_id = self._id(element)
        registered = self._objects.get(object_id)
        if registered is not element:
            raise KeyError(f"Network element is not registered: {object_id}")
        for owner in tuple(self._objects.values()):
            if owner is element:
                continue
            for terminal in getattr(owner, "terminals", ()):
                if terminal.endpoint is element:
                    raise ValueError(
                        f"Cannot remove '{object_id}': Terminal '{terminal.role}' on "
                        f"'{owner.id}' still references it."
                    )
        del self._objects[object_id]
        self._unbind(element)

    def _add_typed(self, key: str, element: Any) -> None:
        if not isinstance(element, _COLLECTION_TYPES[key]):
            expected = ", ".join(t.__name__ for t in _COLLECTION_TYPES[key])
            raise TypeError(f"Expected {expected}; received {type(element).__name__}.")
        self.add(element)

    def _remove_typed(self, key: str, element: Any) -> None:
        if not isinstance(element, _COLLECTION_TYPES[key]):
            expected = ", ".join(t.__name__ for t in _COLLECTION_TYPES[key])
            raise TypeError(f"Expected {expected}; received {type(element).__name__}.")
        self.remove(element)

    def add_bus(self, element: Any) -> None: self._add_typed("bus", element)
    def remove_bus(self, element: Any) -> None: self._remove_typed("bus", element)
    def add_grid(self, element: Any) -> None: self._add_typed("grid", element)
    def remove_grid(self, element: Any) -> None: self._remove_typed("grid", element)
    def add_generator(self, element: Any) -> None: self._add_typed("generator", element)
    def remove_generator(self, element: Any) -> None: self._remove_typed("generator", element)
    def add_synchronous_machine(self, element: Any) -> None: self._add_typed("synchronous_machine", element)
    def remove_synchronous_machine(self, element: Any) -> None: self._remove_typed("synchronous_machine", element)
    def add_load(self, element: Any) -> None: self._add_typed("load", element)
    def remove_load(self, element: Any) -> None: self._remove_typed("load", element)
    def add_motor(self, element: Any) -> None: self._add_typed("motor", element)
    def remove_motor(self, element: Any) -> None: self._remove_typed("motor", element)
    def add_shunt(self, element: Any) -> None: self._add_typed("shunt", element)
    def remove_shunt(self, element: Any) -> None: self._remove_typed("shunt", element)
    def add_capacitor(self, element: Any) -> None: self._add_typed("capacitor", element)
    def remove_capacitor(self, element: Any) -> None: self._remove_typed("capacitor", element)
    def add_reactor(self, element: Any) -> None: self._add_typed("reactor", element)
    def remove_reactor(self, element: Any) -> None: self._remove_typed("reactor", element)
    def add_solar(self, element: Any) -> None: self._add_typed("solar", element)
    def remove_solar(self, element: Any) -> None: self._remove_typed("solar", element)
    def add_battery(self, element: Any) -> None: self._add_typed("battery", element)
    def remove_battery(self, element: Any) -> None: self._remove_typed("battery", element)
    def add_current_transformer(self, element: Any) -> None: self._add_typed("current_transformer", element)
    def remove_current_transformer(self, element: Any) -> None: self._remove_typed("current_transformer", element)
    def add_potential_transformer(self, element: Any) -> None: self._add_typed("potential_transformer", element)
    def remove_potential_transformer(self, element: Any) -> None: self._remove_typed("potential_transformer", element)
    def add_capacitive_voltage_transformer(self, element: Any) -> None: self._add_typed("capacitive_voltage_transformer", element)
    def remove_capacitive_voltage_transformer(self, element: Any) -> None: self._remove_typed("capacitive_voltage_transformer", element)
    def add_relay(self, element: Any) -> None: self._add_typed("relay", element)
    def remove_relay(self, element: Any) -> None: self._remove_typed("relay", element)
    def add_line(self, element: Any) -> None: self._add_typed("line", element)
    def remove_line(self, element: Any) -> None: self._remove_typed("line", element)
    def add_cable(self, element: Any) -> None: self._add_typed("cable", element)
    def remove_cable(self, element: Any) -> None: self._remove_typed("cable", element)
    def add_transformer(self, element: Any) -> None: self._add_typed("transformer", element)
    def remove_transformer(self, element: Any) -> None: self._remove_typed("transformer", element)
    def add_breaker(self, element: Any) -> None: self._add_typed("breaker", element)
    def remove_breaker(self, element: Any) -> None: self._remove_typed("breaker", element)
    def add_switch(self, element: Any) -> None: self._add_typed("switch", element)
    def remove_switch(self, element: Any) -> None: self._remove_typed("switch", element)
    def add_disconnector(self, element: Any) -> None: self._add_typed("disconnector", element)
    def remove_disconnector(self, element: Any) -> None: self._remove_typed("disconnector", element)
    def add_fuse(self, element: Any) -> None: self._add_typed("fuse", element)
    def remove_fuse(self, element: Any) -> None: self._remove_typed("fuse", element)

    def get_by_identity(self, object_id: str) -> ElectricalObject:
        """Return the unique registered Core object for a canonical identity."""
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError("Canonical object identity must be a non-empty string.")
        try:
            return self._objects[object_id.strip()]
        except KeyError as exc:
            raise KeyError(f"Network element is not registered: {object_id}") from exc

    def get_by_id(self, element_type: str, object_id: str) -> Any:
        """Compatibility typed lookup over the canonical identity registry."""
        if not isinstance(element_type, str) or not element_type.strip():
            raise TypeError("element_type must be a non-empty string.")
        if not isinstance(object_id, str) or not object_id.strip():
            raise TypeError("object_id must be a non-empty string.")
        key = element_type.strip().lower()
        key = _TYPE_ALIASES.get(key, key)
        if key == "branch":
            candidates = self.branches
        elif key in _COLLECTION_TYPES:
            candidates = self._typed(key)
        else:
            raise KeyError(f"Unknown network element type: {element_type}")
        for element in candidates:
            if element.id == object_id.strip():
                return element
        raise KeyError(f"Network element is not registered: {element_type}:{object_id}")


__all__ = ["NetworkRegistry"]
