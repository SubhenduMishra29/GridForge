from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from math import isfinite
from typing import Any, Mapping


def canonical_configuration_value(value: Any) -> Any:
    """Detached deterministic snapshot; reject unsupported types explicitly."""
    if isinstance(value, Enum):
        return ("enum", value.__class__.__module__, value.__class__.__qualname__, value.name)
    if value is None or isinstance(value, (str, bool, int)):
        return (type(value).__name__, value)
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("Configuration contains a non-finite float.")
        return ("float", value.hex())
    if isinstance(value, complex):
        if not (isfinite(value.real) and isfinite(value.imag)):
            raise ValueError("Configuration contains a non-finite complex value.")
        return ("complex", value.real.hex(), value.imag.hex())
    if isinstance(value, Mapping):
        entries = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Configuration mapping keys must be strings.")
            entries.append((key, canonical_configuration_value(item)))
        return ("mapping", tuple(sorted(entries, key=lambda pair: pair[0])))
    if isinstance(value, (tuple, list)):
        return (type(value).__name__, tuple(canonical_configuration_value(item) for item in value))
    if isinstance(value, (set, frozenset)):
        items = [canonical_configuration_value(item) for item in value]
        return (type(value).__name__, tuple(sorted(items, key=lambda item: repr(item))))
    if is_dataclass(value) and not isinstance(value, type):
        return ("dataclass", value.__class__.__module__, value.__class__.__qualname__, tuple(
            (item.name, canonical_configuration_value(getattr(value, item.name))) for item in fields(value)
        ))
    raise TypeError("Unsupported configuration value type: " + value.__class__.__module__ + "." + value.__class__.__qualname__)


__all__ = ["canonical_configuration_value"]
