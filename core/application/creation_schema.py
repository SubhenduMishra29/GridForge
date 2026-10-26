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


@dataclass(frozen=True, slots=True)
class CreationTerminalRequirement:
    """Declarative acquisition requirement for one canonical Core terminal."""

    terminal_name: str
    required: bool = False
    cardinality: str = "single"
    allowed_connection_types: tuple[str, ...] = ()
    acquisition_state: str = "required"
    initial_endpoint_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_name, str) or not self.terminal_name.strip():
            raise ValueError("terminal_name must be non-empty.")
        if self.cardinality not in {"single", "pair", "multiple"}:
            raise ValueError("cardinality must be single, pair, or multiple.")
        if self.acquisition_state not in {"required", "optional", "acquired", "pending"}:
            raise ValueError("acquisition_state must be required, optional, acquired, or pending.")
        object.__setattr__(self, "terminal_name", self.terminal_name.strip())
        object.__setattr__(self, "allowed_connection_types", tuple(self.allowed_connection_types))


@dataclass(frozen=True, slots=True)
class CreationTopologyRequirement:
    """Declarative endpoint/topology acquisition requirement."""

    name: str
    required: bool = False
    cardinality: str = "single"
    allowed_connection_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("topology requirement name must be non-empty.")
        if self.cardinality not in {"single", "pair", "multiple"}:
            raise ValueError("cardinality must be single, pair, or multiple.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "allowed_connection_types", tuple(self.allowed_connection_types))


@dataclass(frozen=True, slots=True)
class ConditionalParameterRequirement:
    """Declarative conditional completeness rule."""

    label: str
    require_any: tuple[str, ...] = ()
    require_all: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.require_any and not self.require_all:
            raise ValueError("A conditional requirement must name parameters.")
        object.__setattr__(self, "require_any", tuple(self.require_any))
        object.__setattr__(self, "require_all", tuple(self.require_all))


@dataclass(frozen=True, slots=True)
class CreationDefinition:
    """Immutable canonical creation contract for one equipment type."""

    equipment_type: str
    tool_id: str
    parameter_definitions: tuple[EngineeringParameterDefinition, ...]
    command_type: str
    id_field: str
    parameter_mapping: Mapping[str, str] = field(default_factory=dict)
    endpoint_mapping: Mapping[str, str] = field(default_factory=dict)
    topology_requirements: tuple[CreationTopologyRequirement, ...] = ()
    terminal_requirements: tuple[CreationTerminalRequirement, ...] = ()
    conditional_requirements: tuple[ConditionalParameterRequirement, ...] = ()
    placement_required: bool = True
    preview_supported: bool = True
    configuration_required: bool = False

    def __post_init__(self) -> None:
        if not self.equipment_type.strip() or not self.tool_id.strip():
            raise ValueError("CreationDefinition identities must be non-empty.")
        if not isinstance(self.command_type, str) or not self.command_type.strip():
            raise TypeError("command_type must be a non-empty Application command type.")
        if not self.id_field.strip():
            raise ValueError("id_field must be non-empty.")
        parameters = tuple(self.parameter_definitions)
        ids = [item.parameter_id for item in parameters]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate creation parameter in {self.equipment_type!r}.")
        mapping = dict(self.parameter_mapping)
        for parameter_id in ids:
            mapping.setdefault(parameter_id, parameter_id)
        unknown = set(mapping) - set(ids)
        if unknown:
            raise ValueError(f"Command mapping references unknown parameters: {sorted(unknown)!r}")
        object.__setattr__(self, "equipment_type", self.equipment_type.strip())
        object.__setattr__(self, "tool_id", self.tool_id.strip())
        object.__setattr__(self, "id_field", self.id_field.strip())
        object.__setattr__(self, "command_type", self.command_type.strip())
        object.__setattr__(self, "parameter_definitions", parameters)
        object.__setattr__(self, "parameter_mapping", MappingProxyType(mapping))
        object.__setattr__(self, "endpoint_mapping", MappingProxyType(dict(self.endpoint_mapping)))
        object.__setattr__(self, "topology_requirements", tuple(self.topology_requirements))
        object.__setattr__(self, "terminal_requirements", tuple(self.terminal_requirements))
        object.__setattr__(self, "conditional_requirements", tuple(self.conditional_requirements))

    @property
    def required_parameters(self) -> tuple[EngineeringParameterDefinition, ...]:
        return tuple(p for p in self.parameter_definitions if p.required_before_create)

    @property
    def optional_parameters(self) -> tuple[EngineeringParameterDefinition, ...]:
        return tuple(p for p in self.parameter_definitions if not p.required_before_create)

    @property
    def default_values(self) -> Mapping[str, Any]:
        return {p.parameter_id: p.default_value for p in self.parameter_definitions if p.default_value is not None}

    def parameter(self, parameter_id: str) -> EngineeringParameterDefinition:
        for parameter in self.parameter_definitions:
            if parameter.parameter_id == parameter_id:
                return parameter
        raise KeyError(parameter_id)

    def validate_values(self, values: Mapping[str, Any]) -> tuple[str, ...]:
        errors: list[str] = []
        for parameter in self.parameter_definitions:
            value = values.get(parameter.parameter_id)
            if parameter.required_before_create and value is None:
                errors.append(f"{parameter.display_name} is required.")
                continue
            if value is None:
                continue
            try:
                _validate_parameter(parameter, value)
            except (TypeError, ValueError) as exc:
                errors.append(f"{parameter.display_name}: {exc}")
        for conditional in self.conditional_requirements:
            if conditional.require_any and not any(values.get(key) is not None for key in conditional.require_any):
                errors.append(conditional.label)
            if conditional.require_all and not all(values.get(key) is not None for key in conditional.require_all):
                errors.append(conditional.label)
        return tuple(errors)



def _validate_parameter(definition: EngineeringParameterDefinition, value: Any) -> None:
    unit = None
    if isinstance(value, Mapping):
        unit = value.get("unit")
        value = value.get("value")
    if unit is not None and definition.unit is not None and str(unit).strip() != str(definition.unit).strip():
        raise ValueError(f"unit must be {definition.unit!r}")
    datatype = definition.datatype.strip().lower()
    if datatype in {"float", "number"}:
        if isinstance(value, bool):
            raise TypeError("must be numeric")
        numeric = float(value)
        if definition.minimum is not None and numeric < definition.minimum:
            raise ValueError(f"must be >= {definition.minimum}")
        if definition.maximum is not None and numeric > definition.maximum:
            raise ValueError(f"must be <= {definition.maximum}")
    elif datatype in {"int", "integer"}:
        if isinstance(value, bool) or int(value) != value:
            raise TypeError("must be an integer")
        numeric = int(value)
        if definition.minimum is not None and numeric < definition.minimum:
            raise ValueError(f"must be >= {definition.minimum}")
        if definition.maximum is not None and numeric > definition.maximum:
            raise ValueError(f"must be <= {definition.maximum}")
    elif datatype in {"bool", "boolean"}:
        if not isinstance(value, bool):
            raise TypeError("must be boolean")
    elif datatype == "enum":
        if str(value) not in tuple(str(choice) for choice in definition.choices):
            raise ValueError(f"must be one of {tuple(definition.choices)!r}")
    elif datatype in {"str", "string"}:
        if not isinstance(value, str):
            raise TypeError("must be text")
    rules = dict(definition.validation)
    if rules.get("non_empty") and (value is None or (isinstance(value, str) and not value.strip())):
        raise ValueError("must not be empty")
    if rules.get("nonzero") and value == 0:
        raise ValueError("must be non-zero")
    if "allowed_values" in rules and value not in tuple(rules["allowed_values"]):
        raise ValueError(f"must be one of {tuple(rules['allowed_values'])!r}")

__all__ = [
    "EngineeringParameterDefinition",
    "CreationTerminalRequirement",
    "CreationTopologyRequirement",
    "ConditionalParameterRequirement",
    "CreationDefinition",
]
