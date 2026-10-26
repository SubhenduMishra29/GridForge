# ============================================================
# File: core/application/creation_schema.py
# GridForge V2 — Framework-neutral creation parameter schema
# Author: Subhendu Mishra
# ============================================================
"""Framework-neutral immutable schema primitives for equipment creation.

This module has no UI, Qt, plugin lifecycle, or Core-model dependencies.
The Application and UI adapters may share these declarative parameter
contracts; authority over committed electrical state remains in Core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

@dataclass(frozen=True, slots=True)
class EngineeringParameterDefinition:
    """Canonical engineering parameter contract for equipment creation."""
    parameter_id: str
    display_name: str
    datatype: str = "str"
    unit: str | None = None
    required_before_create: bool = False
    default_value: Any = None
    editable: bool = True
    derived: bool = False
    choices: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    validation: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.parameter_id, str) or not self.parameter_id.strip():
            raise ValueError("parameter_id must be non-empty")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError("display_name must be non-empty")
        if not isinstance(self.datatype, str) or not self.datatype.strip():
            raise ValueError("datatype must be non-empty")
        if self.derived and self.editable:
            raise ValueError("derived parameters cannot be editable")
        object.__setattr__(self, "parameter_id", self.parameter_id.strip())
        object.__setattr__(self, "display_name", self.display_name.strip())
        object.__setattr__(self, "datatype", self.datatype.strip())
        object.__setattr__(self, "choices", tuple(self.choices))
        object.__setattr__(self, "validation", MappingProxyType(dict(self.validation)))


__all__ = ["EngineeringParameterDefinition"]
