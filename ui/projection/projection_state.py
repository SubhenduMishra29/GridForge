# ============================================================
# File: ui/projection/projection_state.py
# GridForge V2 — Projection State Contract
# Author: Subhendu Mishra
# ============================================================
"""Framework-neutral presentation state for UI projections.

This state is a view-facing snapshot. It is deliberately not an electrical
model and must not become a second source of engineering truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
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
class EngineeringParameterState:
    """Immutable generic presentation snapshot of one engineering parameter."""

    parameter_id: str
    value: Any
    unit: str | None = None
    datatype: str = "unknown"
    choices: tuple[str, ...] = ()
    editable: bool = False
    derived: bool = False
    validation: Mapping[str, Any] = field(default_factory=dict)
    coupling_group: str | None = None
    topology_impact: bool = False
    study_impact: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.parameter_id, str) or not self.parameter_id:
            raise ValueError("EngineeringParameterState.parameter_id must be non-empty")
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "choices", tuple(self.choices))
        object.__setattr__(self, "validation", _freeze(self.validation))


@dataclass(frozen=True, slots=True)
class ProjectionState:
    """Stable, render-ready state derived from authoritative model data."""

    object_id: str
    display_type: str
    labels: tuple[str, ...] = ()
    geometry: Any = None
    status: str | None = None
    connectivity_refs: tuple[str, ...] = ()
    visual_flags: frozenset[str] = field(default_factory=frozenset)
    engineering_parameters: tuple[EngineeringParameterState, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ValueError("ProjectionState object_id must be a non-empty string")
        if not isinstance(self.display_type, str) or not self.display_type:
            raise ValueError("ProjectionState display_type must be a non-empty string")

    @classmethod
    def empty(cls, object_id: str, display_type: str) -> "ProjectionState":
        """Create a deterministic empty presentation state."""
        return cls(object_id=object_id, display_type=display_type)


__all__ = ["EngineeringParameterState", "ProjectionState"]
