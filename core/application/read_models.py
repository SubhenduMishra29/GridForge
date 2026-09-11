# ============================================================
# File: core/application/read_models.py
# GridForge V2 — Application Read Models
# Author: Subhendu Mishra
# ============================================================
"""Immutable read-side DTOs exposed across the Application boundary."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    """Recursively freeze supported container values for read-side snapshots."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ElementReadModel:
    """Stable, UI-neutral immutable snapshot of one network element."""

    object_id: str
    element_type: str
    labels: Mapping[str, str]
    connectivity_refs: tuple[str, ...]
    attributes: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ValueError("ElementReadModel.object_id must be non-empty")
        if not isinstance(self.element_type, str) or not self.element_type:
            raise ValueError("ElementReadModel.element_type must be non-empty")
        if not isinstance(self.labels, Mapping):
            raise TypeError("ElementReadModel.labels must be a mapping")
        if not isinstance(self.connectivity_refs, tuple):
            raise TypeError("ElementReadModel.connectivity_refs must be a tuple")
        if not isinstance(self.attributes, Mapping):
            raise TypeError("ElementReadModel.attributes must be a mapping")
        object.__setattr__(self, "labels", _freeze(self.labels))
        object.__setattr__(self, "attributes", _freeze(self.attributes))


@dataclass(frozen=True, slots=True)
class NetworkReadModel:
    """Immutable collection snapshot used by presentation projections."""

    elements: tuple[ElementReadModel, ...]


@dataclass(frozen=True, slots=True)
class RelayInputBindingReadModel:
    """Immutable identifier-only relay input binding."""

    input_name: str
    channel_id: str | None


@dataclass(frozen=True, slots=True)
class RelayReadModel:
    """Immutable presentation snapshot of one authoritative physical Relay."""

    object_id: str
    name: str
    relay_type: str
    function_type: str
    plugin_id: str | None
    settings: Mapping[str, Any]
    in_service: bool
    enabled: bool
    blocked: bool
    picked_up: bool
    tripped: bool
    input_channel_bindings: tuple[RelayInputBindingReadModel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "settings", _freeze(self.settings))
        object.__setattr__(self, "input_channel_bindings", tuple(self.input_channel_bindings))


@dataclass(frozen=True, slots=True)
class ProtectionReadModel:
    """Immutable collection snapshot of protection-domain read data."""

    relays: tuple[RelayReadModel, ...]


__all__ = [
    "ElementReadModel",
    "NetworkReadModel",
    "ProtectionReadModel",
    "RelayInputBindingReadModel",
    "RelayReadModel",
]
