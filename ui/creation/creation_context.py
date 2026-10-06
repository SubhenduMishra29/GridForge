# ============================================================
# File: ui/creation/creation_context.py
# GridForge V2 — Canonical transient equipment creation workflow
# Author: Subhendu Mishra
# ============================================================
"""Generic transient creation lifecycle.

CreationDefinition owns creation semantics. CreationContext only owns the
active session; CreationDraft stores transient intent and validation state.
Neither object is a Core entity or persistence/study state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from ui.creation.creation_definition import CreationDefinition
from ui.equipment.equipment_definition import EquipmentDefinition, EngineeringParameterDefinition


class CreationLifecycleState(str, Enum):
    INACTIVE = "INACTIVE"
    ACTIVATING = "ACTIVATING"
    CONFIGURING = "CONFIGURING"
    PREVIEWING = "PREVIEWING"
    PLACING = "PLACING"
    VALIDATING = "VALIDATING"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    CANCELLED = "CANCELLED"
    INSPECTION = "INSPECTION"


@dataclass(frozen=True, slots=True)
class CreationRequirements:
    """Compatibility projection of a CreationDefinition, not a second schema."""

    configuration_required: bool
    placement_required: bool
    endpoint_required: bool
    multi_endpoint_required: bool
    preview_supported: bool
    commit_supported: bool = True

    @classmethod
    def from_definition(cls, definition: CreationDefinition) -> "CreationRequirements":
        topology = tuple(item for item in definition.topology_requirements if item.required)
        terminals = tuple(item for item in definition.terminal_requirements if item.initial_endpoint_required)
        endpoint_required = bool(topology or terminals)
        multi_endpoint_required = (
            len(topology) + len(terminals) > 1
            or any(item.cardinality in {"pair", "multiple"} for item in (*topology, *terminals))
        )
        return cls(
            configuration_required=definition.configuration_required,
            placement_required=definition.placement_required,
            endpoint_required=endpoint_required,
            multi_endpoint_required=multi_endpoint_required,
            preview_supported=definition.preview_supported,
        )


@dataclass
class CreationDraft:
    """Mutable transient creation intent; never a Core/domain object."""

    definition: CreationDefinition
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
    phase: CreationLifecycleState = CreationLifecycleState.CONFIGURING
    requirements: CreationRequirements | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.definition, CreationDefinition):
            raise TypeError("definition must be a CreationDefinition.")
        self.parameter_schema = tuple(self.parameter_schema)
        self.values = dict(self.values)
        self.endpoints = dict(self.endpoints)
        self.preview_state = dict(self.preview_state)
        self.requirements = self.requirements or CreationRequirements.from_definition(self.definition)
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
        self._refresh_preview_state()
        self.validate_configuration()

    def set_values(self, values: Mapping[str, Any]) -> None:
        for parameter_id, value in values.items():
            self.set_value(parameter_id, value)

    def set_placement(self, position: tuple[float, float], orientation: float = 0.0) -> None:
        self.placement_position = (float(position[0]), float(position[1]))
        self.orientation = float(orientation)
        self._refresh_preview_state()
        self.phase = CreationLifecycleState.PLACING
        self.validate_placement()

    def set_endpoint(self, name: str, endpoint: Any) -> None:
        if name not in self.definition.endpoint_mapping:
            raise KeyError(f"Unknown creation endpoint: {name!r}")
        requirement = next(
            (item for item in self.definition.terminal_requirements if item.terminal_name == name),
            None,
        )
        if requirement is not None and requirement.allowed_connection_types:
            connection_type = getattr(endpoint, "connection_type", None)
            if connection_type is not None and str(connection_type) not in requirement.allowed_connection_types:
                raise ValueError(
                    f"Endpoint for {name!r} has unsupported connection type {connection_type!r}."
                )
        self.endpoints[name] = endpoint
        self._refresh_preview_state()
        self.validate_placement()

    def _refresh_preview_state(self) -> None:
        self.preview_state = {
            "equipment_type": self.equipment_type,
            "parameters": dict(self.values),
            "acquired_terminals": tuple(
                name for name in self.definition.endpoint_mapping if self.endpoints.get(name) is not None
            ),
            "placement": self.placement_position,
            "orientation": self.orientation,
        }

    def set_endpoints(self, endpoints: Mapping[str, Any]) -> None:
        for name, endpoint in endpoints.items():
            self.set_endpoint(name, endpoint)

    def mark_previewing(self) -> None:
        self.phase = CreationLifecycleState.PREVIEWING

    def mark_validating(self) -> None:
        self.phase = CreationLifecycleState.VALIDATING

    def mark_committing(self) -> None:
        self.phase = CreationLifecycleState.COMMITTING

    def validate_configuration(self) -> bool:
        errors = self.definition.validate_values(self.values)
        self.validation_state["configuration"] = errors
        self.configuration_complete = not errors
        return self.configuration_complete

    def validate_placement(self) -> bool:
        errors: list[str] = []
        if self.definition.placement_required and self.placement_position is None:
            errors.append("Placement position is required.")
        for requirement in self.definition.topology_requirements:
            if requirement.required and self.endpoints.get(requirement.name) is None:
                errors.append(f"Required topology endpoint {requirement.name!r} is missing.")
        self.validation_state["placement"] = tuple(errors)
        self.validation_state["endpoint"] = tuple(
            error for error in errors if "endpoint" in error.lower()
        )
        return not errors

    def validate_for_commit(self) -> bool:
        self.mark_validating()
        configuration_ok = self.validate_configuration()
        placement_ok = self.validate_placement()
        self.validation_state["terminal"] = tuple(
            f"Required terminal {item.terminal_name!r} is not acquired."
            for item in self.definition.terminal_requirements
            if item.initial_endpoint_required and self.endpoints.get(item.terminal_name) is None
        )
        final = (
            tuple(self.validation_state.get("configuration", ()))
            + tuple(self.validation_state.get("placement", ()))
            + tuple(self.validation_state.get("terminal", ()))
        )
        self.validation_state["final"] = final
        return not final and configuration_ok and placement_ok

    def snapshot_values(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.values))

    def snapshot_endpoints(self) -> Mapping[str, Any]:
        return MappingProxyType(dict(self.endpoints))


class CreationContext:
    """Single generic authority for the active equipment creation session."""

    def __init__(self) -> None:
        self._draft: CreationDraft | None = None

    @property
    def draft(self) -> CreationDraft | None:
        return self._draft

    @property
    def active(self) -> bool:
        return self._draft is not None

    @property
    def state(self) -> CreationLifecycleState:
        return self._draft.phase if self._draft is not None else CreationLifecycleState.INACTIVE

    def begin(
        self,
        definition: EquipmentDefinition | CreationDefinition,
        requirements: CreationRequirements | None = None,
    ) -> CreationDraft:
        if isinstance(definition, EquipmentDefinition):
            creation_definition = definition.creation_definition
            if not isinstance(creation_definition, CreationDefinition):
                raise ValueError(
                    f"Equipment definition {definition.equipment_type!r} has no canonical CreationDefinition."
                )
        elif isinstance(definition, CreationDefinition):
            creation_definition = definition
        else:
            raise TypeError("definition must be an EquipmentDefinition or CreationDefinition.")
        if self._draft is not None:
            self.discard()
        draft = CreationDraft(
            definition=creation_definition,
            equipment_type=creation_definition.equipment_type,
            tool_id=creation_definition.tool_id,
            parameter_schema=creation_definition.parameter_definitions,
            values=dict(creation_definition.default_values),
            requirements=requirements or CreationRequirements.from_definition(creation_definition),
            phase=CreationLifecycleState.ACTIVATING,
        )
        draft.phase = CreationLifecycleState.CONFIGURING
        self._draft = draft
        return draft

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

    def snapshot_draft(self) -> CreationDraft | None:
        return None if self._draft is None else deepcopy(self._draft)

    def restore_draft(self, draft: CreationDraft | None) -> None:
        if draft is not None and not isinstance(draft, CreationDraft):
            raise TypeError('draft must be a CreationDraft or None.')
        self._draft = deepcopy(draft) if draft is not None else None

    def require_draft(self) -> CreationDraft:
        if self._draft is None:
            raise RuntimeError("No active equipment creation session.")
        return self._draft

    def complete(self) -> None:
        if self._draft is not None:
            self._draft.phase = CreationLifecycleState.COMMITTED
        self._draft = None

    def end_interaction(self) -> None:
        """End transient placement UI state without implying Core commitment."""
        self._draft = None

    def cancel(self) -> None:
        if self._draft is not None:
            self._draft.phase = CreationLifecycleState.CANCELLED
        self._draft = None

    def discard(self) -> None:
        self.cancel()


__all__ = [
    "CreationLifecycleState",
    "CreationRequirements",
    "CreationDraft",
    "CreationContext",
]
