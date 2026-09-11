# ============================================================
# File: core/persistence/model_dto.py
# GridForge V2 — Model Persistence DTOs
# Author: Subhendu Mishra
# ============================================================

"""Stable JSON-oriented DTOs for concrete Core model objects."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.model.base import ElectricalObject
from core.model.terminal import Terminal


class ModelSerializationError(ValueError):
    """Raised when a Core model cannot be represented safely."""


@dataclass(frozen=True, slots=True)
class TerminalDTO:
    attribute: str
    role: str
    endpoint_type: str | None = None
    endpoint_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "attribute": self.attribute,
            "role": self.role,
        }
        if self.endpoint_type is not None:
            data["endpoint"] = {
                "type": self.endpoint_type,
                "id": self.endpoint_id,
            }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TerminalDTO":
        endpoint = data.get("endpoint") or {}
        return cls(
            attribute=str(data["attribute"]),
            role=str(data["role"]),
            endpoint_type=endpoint.get("type"),
            endpoint_id=endpoint.get("id"),
        )


@dataclass(frozen=True, slots=True)
class ModelDTO:
    type: str
    id: str
    state: dict[str, Any]
    terminals: tuple[TerminalDTO, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "state": self.state,
            "terminals": [terminal.to_dict() for terminal in self.terminals],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelDTO":
        return cls(
            type=str(data["type"]),
            id=str(data["id"]),
            state=dict(data.get("state") or {}),
            terminals=tuple(TerminalDTO.from_dict(item) for item in data.get("terminals", ())),
        )


def _slot_names(model: Any) -> set[str]:
    names: set[str] = set()
    for cls in type(model).__mro__:
        slots = cls.__dict__.get("__slots__", ())
        if isinstance(slots, str):
            slots = (slots,)
        names.update(slots)
    return {name for name in names if name not in {"__dict__", "__weakref__"}}


def _attribute_items(model: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if hasattr(model, "__dict__"):
        values.update(vars(model))
    for name in _slot_names(model):
        try:
            values[name] = getattr(model, name)
        except AttributeError:
            continue
    return values


def _encode(value: Any, *, terminal_attributes: dict[str, Terminal], path: str) -> Any:
    if isinstance(value, Terminal):
        raise ModelSerializationError(f"Unexpected terminal at {path}; terminals are handled separately.")
    if isinstance(value, ElectricalObject):
        return {"$ref": {"type": type(value).__name__, "id": value.id}}
    if isinstance(value, Enum):
        return {"$enum": f"{type(value).__module__}:{type(value).__qualname__}", "name": value.name}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return {"$float": "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")}
    if isinstance(value, tuple):
        return {"$tuple": [_encode(item, terminal_attributes=terminal_attributes, path=f"{path}[]") for item in value]}
    if isinstance(value, list):
        return [_encode(item, terminal_attributes=terminal_attributes, path=f"{path}[]") for item in value]
    if isinstance(value, dict):
        return {
            str(key): _encode(item, terminal_attributes=terminal_attributes, path=f"{path}.{key}")
            for key, item in value.items()
        }
    raise ModelSerializationError(
        f"Unsupported state value at {path}: {type(value).__module__}.{type(value).__qualname__}"
    )


def model_to_dto(model: Any) -> ModelDTO:
    """Convert one concrete Core model object into a stable DTO."""
    if not isinstance(model, ElectricalObject):
        raise TypeError("Only ElectricalObject instances can be persisted.")

    attributes = _attribute_items(model)
    terminal_attributes = {
        name: value
        for name, value in attributes.items()
        if isinstance(value, Terminal)
    }

    state: dict[str, Any] = {}
    for name, value in attributes.items():
        if name in terminal_attributes:
            continue
        state[name] = _encode(value, terminal_attributes=terminal_attributes, path=name)

    terminals: list[TerminalDTO] = []
    for attribute, terminal in sorted(terminal_attributes.items()):
        endpoint = terminal.endpoint
        endpoint_type = type(endpoint).__name__ if isinstance(endpoint, ElectricalObject) else None
        endpoint_id = endpoint.id if isinstance(endpoint, ElectricalObject) else None
        terminals.append(
            TerminalDTO(
                attribute=attribute,
                role=terminal.role,
                endpoint_type=endpoint_type,
                endpoint_id=endpoint_id,
            )
        )

    return ModelDTO(
        type=type(model).__name__,
        id=model.id,
        state=state,
        terminals=tuple(terminals),
    )


def _decode(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if isinstance(value, dict):
        if "$tuple" in value:
            return tuple(_decode(item) for item in value["$tuple"])
        if "$float" in value:
            return float(value["$float"])
        if "$ref" in value:
            return value
        if "$enum" in value:
            module_name, qualname = value["$enum"].split(":", 1)
            module = __import__(module_name, fromlist=[qualname.split(".")[0]])
            target: Any = module
            for part in qualname.split("."):
                target = getattr(target, part)
            return target[value["name"]]
        return {key: _decode(item) for key, item in value.items()}
    return value


def restore_state(model: Any, state: dict[str, Any]) -> list[tuple[str, dict[str, str]]]:
    """Restore scalar/object-reference state onto an uninitialized model.

    Object references are retained as lightweight ``$ref`` dictionaries and
    resolved by ``network_serializer`` after every object has been registered.
    """
    references: list[tuple[str, dict[str, str]]] = []
    for name, encoded in state.items():
        decoded = _decode(encoded)
        if isinstance(decoded, dict) and "$ref" in decoded:
            references.append((name, dict(decoded["$ref"])))
            continue
        setattr(model, name, decoded)
    return references


__all__ = [
    "ModelDTO",
    "ModelSerializationError",
    "TerminalDTO",
    "model_to_dto",
    "restore_state",
]
