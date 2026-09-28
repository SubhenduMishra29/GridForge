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
from enum import Enum
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


class PropertyFieldKind(str, Enum):
    """Explicit classification for every field exposed to the property projection."""

    ENGINEERING_EDITABLE = "ENGINEERING_EDITABLE"
    ENGINEERING_READ_ONLY = "ENGINEERING_READ_ONLY"
    PRESENTATION_EDITABLE = "PRESENTATION_EDITABLE"
    TOPOLOGY_TERMINAL_EDITABLE = "TOPOLOGY_TERMINAL_EDITABLE"
    DERIVED = "DERIVED"


@dataclass(frozen=True, slots=True)
class PropertyFieldState:
    """Immutable property-panel field contract; never a mutation authority."""

    field_id: str
    value: Any
    category: PropertyFieldKind
    datatype: str = "unknown"
    unit: str | None = None
    choices: tuple[str, ...] = ()
    editable: bool = False
    derived: bool = False
    validation: Mapping[str, Any] = field(default_factory=dict)
    topology_impact: bool = False
    study_impact: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.field_id, str) or not self.field_id.strip():
            raise ValueError("PropertyFieldState.field_id must be non-empty")
        if not isinstance(self.category, PropertyFieldKind):
            raise TypeError("PropertyFieldState.category must be a PropertyFieldKind")
        object.__setattr__(self, "field_id", self.field_id.strip())
        object.__setattr__(self, "value", _freeze(self.value))
        object.__setattr__(self, "choices", tuple(str(choice) for choice in self.choices))
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
    property_fields: tuple[PropertyFieldState, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.object_id, str) or not self.object_id:
            raise ValueError("ProjectionState object_id must be a non-empty string")
        if not isinstance(self.display_type, str) or not self.display_type:
            raise ValueError("ProjectionState display_type must be a non-empty string")
        fields = list(self.property_fields)
        if not fields:
            if self.labels:
                fields.append(PropertyFieldState(
                    field_id="name", value=self.labels[0],
                    category=PropertyFieldKind.ENGINEERING_READ_ONLY,
                    datatype="str", editable=False,
                ))
            if self.status is not None:
                fields.append(PropertyFieldState(
                    field_id="status", value=self.status,
                    category=PropertyFieldKind.DERIVED,
                    datatype="str", derived=True,
                ))
            if self.connectivity_refs:
                fields.append(PropertyFieldState(
                    field_id="terminal_connectivity", value=self.connectivity_refs,
                    category=PropertyFieldKind.ENGINEERING_READ_ONLY,
                    datatype="tuple", editable=False,
                    topology_impact=True,
                ))
            for parameter in self.engineering_parameters:
                if parameter.derived:
                    category = PropertyFieldKind.DERIVED
                elif parameter.editable and str(parameter.validation.get("category", "")).upper() == PropertyFieldKind.TOPOLOGY_TERMINAL_EDITABLE.value:
                    category = PropertyFieldKind.TOPOLOGY_TERMINAL_EDITABLE
                elif parameter.editable:
                    category = PropertyFieldKind.ENGINEERING_EDITABLE
                else:
                    category = PropertyFieldKind.ENGINEERING_READ_ONLY
                fields.append(PropertyFieldState(
                    field_id=parameter.parameter_id,
                    value=parameter.value,
                    category=category,
                    datatype=parameter.datatype,
                    unit=parameter.unit,
                    choices=parameter.choices,
                    editable=parameter.editable,
                    derived=parameter.derived,
                    validation=parameter.validation,
                    topology_impact=parameter.topology_impact,
                    study_impact=parameter.study_impact,
                ))
        object.__setattr__(self, "property_fields", tuple(fields))

    @classmethod
    def empty(cls, object_id: str, display_type: str) -> "ProjectionState":
        """Create a deterministic empty presentation state."""
        return cls(object_id=object_id, display_type=display_type)


__all__ = ["EngineeringParameterState", "PropertyFieldKind", "PropertyFieldState", "ProjectionState"]
