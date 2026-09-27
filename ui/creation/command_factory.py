# ============================================================
# File: ui/creation/command_factory.py
# GridForge V2 — Canonical creation command preparation
# Author: Subhendu Mishra
# ============================================================
"""Translate validated CreationDrafts into immutable Application commands."""

from __future__ import annotations

import inspect
from typing import Any, Mapping

from ui.creation.creation_context import CreationDraft
from ui.creation.creation_definition import creation_definition_for


class CreationCommandFactory:
    """Single adapter from declarative creation contracts to commands."""

    @classmethod
    def build(
        cls,
        draft: CreationDraft,
        *,
        object_id: str,
        position: tuple[float, float] | None,
        endpoints: Mapping[str, Any] | None = None,
    ) -> Any:
        if not isinstance(draft, CreationDraft):
            raise TypeError("draft must be a CreationDraft.")
        if not draft.validate_for_commit():
            raise ValueError(
                f"{draft.equipment_type} creation is incomplete: "
                + "; ".join(draft.validation_state.get("final", ()))
            )
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError("object_id must be non-empty.")
        definition = draft.definition
        payload: dict[str, Any] = {definition.id_field: object_id.strip()}
        values = dict(draft.snapshot_values())

        for parameter_id, command_field in definition.parameter_mapping.items():
            if parameter_id not in values:
                continue
            value = values[parameter_id]
            if value is not None:
                payload[command_field] = value

        acquired = dict(draft.snapshot_endpoints())
        acquired.update(endpoints or {})
        for semantic_name, command_field in definition.endpoint_mapping.items():
            if semantic_name in acquired and acquired[semantic_name] is not None:
                payload[command_field] = acquired[semantic_name]

        if position is not None:
            signature = inspect.signature(definition.command_class)
            if "presentation_x" in signature.parameters:
                payload["presentation_x"] = float(position[0])
            if "presentation_y" in signature.parameters:
                payload["presentation_y"] = float(position[1])
            if "x" in signature.parameters:
                payload["x"] = float(position[0])
            if "y" in signature.parameters:
                payload["y"] = float(position[1])

        cls._verify_payload_contract(definition, payload)
        return definition.command_class(**payload)

    @staticmethod
    def _verify_payload_contract(definition: Any, payload: Mapping[str, Any]) -> None:
        signature = inspect.signature(definition.command_class)
        fields = {
            name for name, parameter in signature.parameters.items()
            if name not in {"self", "command_id", "correlation_id", "causation_id"}
        }
        unknown = set(payload) - fields
        if unknown:
            raise ValueError(
                f"{definition.equipment_type} command payload contains unmapped fields: {sorted(unknown)!r}"
            )

        missing = [
            name for name, parameter in signature.parameters.items()
            if name not in {"self", "command_id", "correlation_id", "causation_id"}
            and parameter.default is inspect.Parameter.empty
            and name not in payload
        ]
        if missing:
            raise ValueError(
                f"{definition.equipment_type} command requires unmapped fields: {missing!r}"
            )


def verify_creation_contracts(definitions: Any) -> tuple[str, ...]:
    """Statically verify the supplied EquipmentDefinition catalogue.

    The caller supplies the authoritative EquipmentRegistry catalogue; this
    function never maintains a second equipment/tool registry.
    """

    errors: list[str] = []
    for equipment_definition in definitions:
        definition = getattr(equipment_definition, "creation_definition", None)
        if definition is None:
            errors.append(f"{getattr(equipment_definition, 'equipment_type', '<unknown>')}: missing CreationDefinition")
            continue
        try:
            signature = inspect.signature(definition.command_class)
            command_fields = set(signature.parameters)
            parameter_ids = {item.parameter_id for item in definition.parameter_definitions}
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
            handled = {
                definition.id_field, "presentation_x", "presentation_y", "x", "y",
                "command_id", "correlation_id", "causation_id",
            }
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
