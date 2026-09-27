# ============================================================
# File: ui/creation/command_factory.py
# GridForge V2 — Creation intent preparation adapter
# Author: Subhendu Mishra
# ============================================================
"""Create immutable Application intent; never construct Application commands in UI."""

from __future__ import annotations

import inspect
from typing import Any, Mapping

from core.application.creation import CreationCommitIntent, creation_command_contract
from ui.creation.creation_context import CreationDraft


class CreationCommandFactory:
    """Compatibility-named UI adapter that emits immutable Application intent."""

    @classmethod
    def build(
        cls,
        draft: CreationDraft,
        *,
        object_id: str,
        position: tuple[float, float] | None,
        endpoints: Mapping[str, Any] | None = None,
    ) -> CreationCommitIntent:
        if not isinstance(draft, CreationDraft):
            raise TypeError("draft must be a CreationDraft.")
        if not draft.validate_for_commit():
            raise ValueError(
                f"{draft.equipment_type} creation is incomplete: "
                + "; ".join(draft.validation_state.get("final", ()))
            )
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError("object_id must be non-empty.")
        acquired = dict(draft.snapshot_endpoints())
        acquired.update(endpoints or {})
        return CreationCommitIntent(
            command_type=draft.definition.command_type,
            id_field=draft.definition.id_field,
            object_id=object_id.strip(),
            parameter_mapping=draft.definition.parameter_mapping,
            endpoint_mapping=draft.definition.endpoint_mapping,
            values=draft.snapshot_values(),
            endpoints=acquired,
            position=position,
        )


def verify_creation_contracts(definitions: Any) -> tuple[str, ...]:
    """Statically verify CreationDefinition against Application command signatures."""
    errors: list[str] = []
    for equipment_definition in definitions:
        definition = getattr(equipment_definition, "creation_definition", None)
        if definition is None:
            errors.append(f"{getattr(equipment_definition, 'equipment_type', '<unknown>')}: missing CreationDefinition")
            continue
        try:
            signature = inspect.signature(creation_command_contract(definition.command_type))
            command_fields = set(signature.parameters)
            parameter_ids = {item.parameter_id for item in definition.parameter_definitions}
            if definition.id_field not in command_fields:
                errors.append(f"{definition.equipment_type}: ID field {definition.id_field!r} is absent from command")
            for parameter_id, command_field in definition.parameter_mapping.items():
                if parameter_id not in parameter_ids:
                    errors.append(f"{definition.equipment_type}: unknown schema parameter {parameter_id!r}")
                if command_field not in command_fields:
                    errors.append(f"{definition.equipment_type}: parameter {parameter_id!r} maps to missing command field {command_field!r}")
            terminal_names = {item.terminal_name for item in definition.terminal_requirements}
            topology_names = {item.name for item in definition.topology_requirements}
            for semantic_name, command_field in definition.endpoint_mapping.items():
                if semantic_name not in terminal_names and semantic_name not in topology_names:
                    errors.append(f"{definition.equipment_type}: endpoint mapping uses unknown semantic name {semantic_name!r}")
                if command_field not in command_fields:
                    errors.append(f"{definition.equipment_type}: endpoint {semantic_name!r} maps to missing command field {command_field!r}")
            canonical_terminals = set(getattr(equipment_definition, "terminal_names", ()))
            for requirement in definition.terminal_requirements:
                if requirement.terminal_name not in canonical_terminals:
                    errors.append(f"{definition.equipment_type}: terminal requirement references non-canonical terminal {requirement.terminal_name!r}")
                if requirement.required and requirement.acquisition_state not in {"required", "acquired"}:
                    errors.append(f"{definition.equipment_type}: required terminal {requirement.terminal_name!r} has invalid acquisition state")
            known = {item.parameter_id for item in definition.parameter_definitions}
            for conditional in definition.conditional_requirements:
                for key in (*conditional.require_any, *conditional.require_all):
                    if key not in known:
                        errors.append(f"{definition.equipment_type}: conditional rule references unknown parameter {key!r}")
            handled = {definition.id_field, "presentation_x", "presentation_y", "x", "y", "command_id", "correlation_id", "causation_id"}
            handled.update(definition.parameter_mapping.values())
            handled.update(definition.endpoint_mapping.values())
            for name, parameter in signature.parameters.items():
                if name in handled or parameter.default is not inspect.Parameter.empty:
                    continue
                errors.append(f"{definition.equipment_type}: required command field {name!r} has no creation-contract source")
        except Exception as exc:
            errors.append(f"{getattr(definition, 'equipment_type', '<unknown>')}: {exc}")
    return tuple(errors)


__all__ = ["CreationCommandFactory", "verify_creation_contracts"]
