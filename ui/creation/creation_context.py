# ============================================================
# File: ui/creation/creation_context.py
# GridForge V2 — Canonical transient equipment creation workflow
# Author: Subhendu Mishra
# ============================================================
"""Transient creation intent and validation for SLD equipment placement.

CreationContext is presentation/application workflow state only. It is never
registered with Core, topology, persistence, studies, or solvers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from ui.equipment.equipment_definition import EquipmentDefinition, EngineeringParameterDefinition


@dataclass(frozen=True, slots=True)
class CreationRequirements:
    """Declarative requirements for one creation workflow."""

    configuration_required: bool = False
    placement_required: bool = True
    endpoint_required: bool = False
    multi_endpoint_required: bool = False
    preview_supported: bool = True
    commit_supported: bool = True


@dataclass
class CreationDraft:
    """Mutable, transient creation intent; never a Core/domain object."""

    equipment_type: str
    tool_id: str
    parameter_schema: tuple[EngineeringParameterDefinition, ...]
    values: dict[str, Any]
    validation_state: dict[str, tuple[str, ...]] = field(default_factory=dict)
    configuration_complete: bool = False
    placement_position: tuple[float, float] | None = None
    orientation: float = 0.0
    endpoints: dict[str, Any] = field(default_factory=dict)
    preview_state: dict[str, Any] = field(default_factory=dict)
    requirements: CreationRequirements = field(default_factory=CreationRequirements)

    def __post_init__(self) -> None:
        self.parameter_schema = tuple(self.parameter_schema)
        self.values = dict(self.values)
        self.endpoints = dict(self.endpoints)
        self.preview_state = dict(self.preview_state)
        self.validate_configuration()

    @property
    def parameter_definitions(self) -> Mapping[str, EngineeringParameterDefinition]:
        return MappingProxyType({item.parameter_id: item for item in self.parameter_schema})

    def set_value(self, parameter_id: str, value: Any) -> None:
        definition = self.parameter_definitions.get(parameter_id)
        if definition is None:
            raise KeyError(f"Unknown creation parameter: {parameter_id!r}")
        if definition.derived or not definition.editable:
            raise ValueError(f"Creation parameter is read-only: {parameter_id!r}")
        self.values[parameter_id] = value
        self.validate_configuration()

    def set_values(self, values: Mapping[str, Any]) -> None:
        for parameter_id, value in values.items():
            self.set_value(parameter_id, value)

    def set_placement(self, position: tuple[float, float], orientation: float = 0.0) -> None:
        self.placement_position = (float(position[0]), float(position[1]))
        self.orientation = float(orientation)
        self.validate_placement()

    def set_endpoint(self, name: str, endpoint: Any) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Endpoint name must be non-empty.")
        self.endpoints[name.strip()] = endpoint

    def set_endpoints(self, endpoints: Mapping[str, Any]) -> None:
        self.endpoints.update(endpoints)

    def validate_configuration(self) -> bool:
        errors: list[str] = []
        warnings: list[str] = []
        for definition in self.parameter_schema:
            value = self.values.get(definition.parameter_id)
            if definition.required_before_create and value is None:
                errors.append(f"{definition.display_name} is required.")
                continue
            if value is None:
                continue
            try:
                self._validate_value(definition, value)
            except (TypeError, ValueError) as exc:
                errors.append(f"{definition.display_name}: {exc}")
        if self.equipment_type == "transformer":
            if self.values.get("impedance_base_mva") is None and self.values.get("rate_mva") is None:
                errors.append("Transformer requires impedance_base_mva or rate_mva.")
        self.validation_state["configuration"] = tuple(errors)
        self.validation_state["configuration_warnings"] = tuple(warnings)
        self.configuration_complete = not errors
        return self.configuration_complete

    def validate_placement(self) -> bool:
        errors: list[str] = []
        if self.requirements.placement_required and self.placement_position is None:
            errors.append("Placement position is required.")
        if self.requirements.endpoint_required:
            required_count = 2 if self.requirements.multi_endpoint_required else 1
            present = sum(value is not None for value in self.endpoints.values())
            if present < required_count:
                errors.append("Required topology endpoints are incomplete.")
        self.validation_state["placement"] = tuple(errors)
        return not errors

    def validate_for_commit(self) -> bool:
        configuration_ok = self.validate_configuration()
        placement_ok = self.validate_placement()
        endpoint_errors = tuple(self.validation_state.get("endpoint", ()))
        self.validation_state["final"] = endpoint_errors
        return configuration_ok and placement_ok and not endpoint_errors

    def snapshot_values(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))

    @staticmethod
    def _validate_value(definition: EngineeringParameterDefinition, value: Any) -> None:
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


class CreationContext:
    """Single transient authority for the active equipment creation session."""

    def __init__(self) -> None:
        self._draft: CreationDraft | None = None

    @property
    def draft(self) -> CreationDraft | None:
        return self._draft

    @property
    def active(self) -> bool:
        return self._draft is not None

    def begin(self, definition: EquipmentDefinition, requirements: CreationRequirements | None = None) -> CreationDraft:
        if not isinstance(definition, EquipmentDefinition):
            raise TypeError("definition must be an EquipmentDefinition.")
        if self._draft is not None:
            self.discard()
        schema = tuple(definition.engineering_parameters)
        values = {
            item.parameter_id: item.default_value
            for item in schema
            if item.default_value is not None
        }
        self._draft = CreationDraft(
            equipment_type=definition.equipment_type,
            tool_id=definition.tool_id,
            parameter_schema=schema,
            values=values,
            requirements=requirements or CreationRequirements(
                configuration_required=any(item.required_before_create for item in schema),
                endpoint_required=definition.category in {"branch", "switching", "measurement"},
                multi_endpoint_required=len(definition.terminal_names) > 2,
            ),
        )
        return self._draft

    def update(self, parameter_id: str, value: Any) -> CreationDraft:
        draft = self.require_draft()
        draft.set_value(parameter_id, value)
        return draft

    def update_many(self, values: Mapping[str, Any]) -> CreationDraft:
        draft = self.require_draft()
        draft.set_values(values)
        return draft

    def set_placement(self, position: tuple[float, float], orientation: float = 0.0) -> CreationDraft:
        draft = self.require_draft()
        draft.set_placement(position, orientation)
        return draft

    def set_endpoints(self, endpoints: Mapping[str, Any]) -> CreationDraft:
        draft = self.require_draft()
        draft.set_endpoints(endpoints)
        return draft

    def require_draft(self) -> CreationDraft:
        if self._draft is None:
            raise RuntimeError("No active equipment creation session.")
        return self._draft

    def discard(self) -> None:
        self._draft = None

    def complete(self) -> None:
        self._draft = None


__all__ = ["CreationRequirements", "CreationDraft", "CreationContext"]
