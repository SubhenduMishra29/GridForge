# ============================================================
# File: core/persistence/type_registry.py
# GridForge V2 — Persistence Type Registry
# Author: Subhendu Mishra
# ============================================================

"""Explicit, fail-fast mapping between persisted model types and Core classes."""

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
    Fuse,
    Generator,
    Grid,
    Line,
    Load,
    Motor,
    PT,
    Reactor,
    Shunt,
    Solar,
    Switch,
    SynchronousMachine,
    Transformer,
)


class UnknownModelTypeError(ValueError):
    """Raised when a persisted concrete model type is not supported."""


_MODEL_TYPES: dict[str, type[Any]] = {
    cls.__name__: cls
    for cls in (
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
        Line,
        Cable,
        Transformer,
        Breaker,
        Switch,
        Disconnector,
        Fuse,
    )
}
_MODEL_TYPES.update(
    {
        "CT": CurrentTransformer,
        "PotentialTransformer": PT,
        "SyncMachine": SynchronousMachine,
    }
)


class ModelTypeRegistry:
    """Resolve the concrete Core model class and Network insertion operation."""

    def __init__(self) -> None:
        self._types = dict(_MODEL_TYPES)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._types))

    def register(self, name: str, model_type: type[Any]) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Model type name must be non-empty.")
        if not isinstance(model_type, type):
            raise TypeError("model_type must be a type.")
        self._types[name.strip()] = model_type

    def resolve(self, name: str) -> type[Any]:
        if not isinstance(name, str):
            raise TypeError("Persisted model type must be a string.")
        try:
            return self._types[name]
        except KeyError as exc:
            raise UnknownModelTypeError(
                f"Unsupported persisted GridForge model type: {name}"
            ) from exc


_NETWORK_ADDERS: dict[type[Any], str] = {
    Bus: "add_bus",
    Grid: "add_grid",
    Generator: "add_generator",
    SynchronousMachine: "add_synchronous_machine",
    Load: "add_load",
    Motor: "add_motor",
    Shunt: "add_shunt",
    Capacitor: "add_capacitor",
    Reactor: "add_reactor",
    Solar: "add_solar",
    Battery: "add_battery",
    CurrentTransformer: "add_current_transformer",
    PT: "add_potential_transformer",
    CVT: "add_capacitive_voltage_transformer",
    Line: "add_line",
    Cable: "add_cable",
    Transformer: "add_transformer",
    Breaker: "add_breaker",
    Switch: "add_switch",
    Disconnector: "add_disconnector",
    Fuse: "add_fuse",
}


def network_adder_name(model_type: type[Any]) -> str:
    """Return the explicit Network registration operation for a model class."""
    try:
        return _NETWORK_ADDERS[model_type]
    except KeyError as exc:
        raise UnknownModelTypeError(
            f"No Network registration contract exists for {model_type.__name__}."
        ) from exc


__all__ = ["ModelTypeRegistry", "UnknownModelTypeError", "network_adder_name"]
