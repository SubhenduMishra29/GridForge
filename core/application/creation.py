# ============================================================
# File: core/application/creation.py
# GridForge V2 — Application creation intent preparation boundary
# Author: Subhendu Mishra
# ============================================================
"""Application-owned translation from immutable creation intent to commands."""

from __future__ import annotations

import inspect
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .command import Command
from .commands.model_commands import (
    CreateBusCommand, CreateGridCommand, CreateGeneratorCommand, CreateLoadCommand,
    CreateShuntCommand, CreateLineCommand, CreateTransformerCommand, CreateCableCommand,
    CreateSwitchCommand, CreateDisconnectorCommand, CreateFuseCommand,
)
from .commands.breaker_commands import CreateBreakerCommand
from .commands.capacitor_commands import CreateCapacitorCommand
from .commands.reactor_commands import CreateReactorCommand
from .commands.motor_commands import CreateMotorCommand
from .commands.synchronous_machine_commands import CreateSynchronousMachineCommand
from .commands.solar_commands import CreateSolarCommand
from .commands.battery_commands import CreateBatteryCommand
from .commands.measurement_commands import CreateCurrentTransformerCommand, CreateCapacitiveVoltageTransformerCommand
from .commands.pt_commands import CreatePTCommand
from .commands.relay_commands import CreateRelayCommand

_CREATE_COMMANDS = {
    "model.create_bus": CreateBusCommand,
    "model.create_grid": CreateGridCommand,
    "model.create_generator": CreateGeneratorCommand,
    "model.create_load": CreateLoadCommand,
    "model.create_shunt": CreateShuntCommand,
    "model.create_line": CreateLineCommand,
    "model.create_transformer": CreateTransformerCommand,
    "model.create_cable": CreateCableCommand,
    "model.create_switch": CreateSwitchCommand,
    "model.create_breaker": CreateBreakerCommand,
    "model.create_disconnector": CreateDisconnectorCommand,
    "model.create_fuse": CreateFuseCommand,
    "model.create_capacitor": CreateCapacitorCommand,
    "model.create_reactor": CreateReactorCommand,
    "model.create_motor": CreateMotorCommand,
    "model.create_synchronous_machine": CreateSynchronousMachineCommand,
    "model.create_solar": CreateSolarCommand,
    "model.create_battery": CreateBatteryCommand,
    "model.create_current_transformer": CreateCurrentTransformerCommand,
    "model.create_potential_transformer": CreatePTCommand,
    "model.create_capacitive_voltage_transformer": CreateCapacitiveVoltageTransformerCommand,
    "model.create_relay": CreateRelayCommand,
}

@dataclass(frozen=True, slots=True)
class CreationCommitIntent:
    """Immutable UI intent; it contains data, not an Application command."""
    command_type: str
    id_field: str
    object_id: str
    parameter_mapping: Mapping[str, str]
    endpoint_mapping: Mapping[str, str]
    values: Mapping[str, Any]
    endpoints: Mapping[str, Any]
    position: tuple[float, float] | None = None
    parameter_contract: tuple[Mapping[str, Any], ...] = ()
    conditional_requirements: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (self.command_type, self.id_field, self.object_id)):
            raise ValueError("CreationCommitIntent requires non-empty command type, ID field, and object ID.")
        object.__setattr__(self, "command_type", self.command_type.strip())
        object.__setattr__(self, "id_field", self.id_field.strip())
        object.__setattr__(self, "object_id", self.object_id.strip())
        object.__setattr__(self, "parameter_mapping", MappingProxyType(dict(self.parameter_mapping)))
        object.__setattr__(self, "endpoint_mapping", MappingProxyType(dict(self.endpoint_mapping)))
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        object.__setattr__(self, "endpoints", MappingProxyType(dict(self.endpoints)))
        object.__setattr__(self, "parameter_contract", tuple(MappingProxyType(dict(x)) for x in self.parameter_contract))
        object.__setattr__(self, "conditional_requirements", tuple(MappingProxyType(dict(x)) for x in self.conditional_requirements))
        if self.position is not None:
            object.__setattr__(self, "position", (float(self.position[0]), float(self.position[1])))


def validate_creation_values(equipment_type, values, parameter_mapping, parameter_contract, conditional_requirements=()):
    """Validate draft engineering values using a serialized, framework-neutral contract."""
    if not parameter_contract:
        raise ValueError(f"{equipment_type}: canonical engineering parameter contract is missing.")
    definitions = {str(x.get("parameter_id", "")): x for x in parameter_contract}
    if "" in definitions or len(definitions) != len(parameter_contract):
        raise ValueError(f"{equipment_type}: invalid or duplicate parameter contract identifiers.")
    unknown = set(values) - set(definitions)
    unmapped = set(values) - set(parameter_mapping)
    missing_mappings = set(definitions) - set(parameter_mapping)
    invalid_mappings = {key for key, target in parameter_mapping.items() if not isinstance(target, str) or not target.strip()}
    if unknown or unmapped or missing_mappings or invalid_mappings:
        raise ValueError(
            f"{equipment_type}: invalid engineering contract mappings; "
            f"unknown={sorted(unknown)!r}, unmapped_values={sorted(unmapped)!r}, "
            f"missing_mappings={sorted(missing_mappings)!r}, invalid_targets={sorted(invalid_mappings)!r}"
        )
    normalized = dict(values)
    errors = []
    for key, definition in definitions.items():
        value = normalized.get(key)
        if value is None and definition.get("default_value") is not None:
            value = definition["default_value"]
            normalized[key] = value
        if value is None:
            if definition.get("required_before_create", False):
                errors.append(f"{key}: required value is missing")
            continue
        unit = None
        if isinstance(value, Mapping):
            unit = value.get("unit")
            if "value" not in value:
                errors.append(f"{key}: value mapping must contain 'value'")
                continue
            raw = value["value"]
        else:
            raw = value
        expected_unit = definition.get("unit")
        if unit is not None and expected_unit is None:
            errors.append(f"{key}: unit metadata is not defined by the canonical contract")
            continue
        if unit is not None and expected_unit is not None and str(unit).strip() != str(expected_unit).strip():
            errors.append(f"{key}: unit must be {expected_unit!r}")
            continue
        datatype = str(definition.get("datatype", "str")).lower()
        try:
            if datatype in {"float", "number"}:
                if isinstance(raw, bool): raise TypeError("must be numeric, not boolean")
                n = float(raw)
                if not math.isfinite(n): raise ValueError("must be finite")
                if definition.get("minimum") is not None and n < float(definition["minimum"]): raise ValueError(f"must be >= {definition['minimum']}")
                if definition.get("maximum") is not None and n > float(definition["maximum"]): raise ValueError(f"must be <= {definition['maximum']}")
            elif datatype in {"int", "integer"}:
                if isinstance(raw, bool) or int(raw) != raw: raise TypeError("must be an integer")
                n = int(raw)
                if definition.get("minimum") is not None and n < float(definition["minimum"]): raise ValueError(f"must be >= {definition['minimum']}")
                if definition.get("maximum") is not None and n > float(definition["maximum"]): raise ValueError(f"must be <= {definition['maximum']}")
            elif datatype in {"bool", "boolean"}:
                if not isinstance(raw, bool): raise TypeError("must be boolean")
            elif datatype == "enum":
                if str(raw) not in tuple(str(v) for v in definition.get("choices", ())): raise ValueError(f"must be one of {tuple(definition.get('choices', ()))!r}")
            elif datatype in {"str", "string"}:
                if not isinstance(raw, str): raise TypeError("must be text")
            canonical = n if datatype in {"float", "number", "int", "integer"} else raw
            rules = dict(definition.get("validation", {}))
            if rules.get("non_empty") and isinstance(canonical, str) and not canonical.strip(): raise ValueError("must not be empty")
            if rules.get("nonzero") and canonical == 0: raise ValueError("must be non-zero")
            if "allowed_values" in rules and canonical not in tuple(rules["allowed_values"]): raise ValueError(f"must be one of {tuple(rules['allowed_values'])!r}")
            normalized[key] = canonical
        except (TypeError, ValueError, OverflowError) as exc:
            errors.append(f"{key}: {exc}")
    for rule in conditional_requirements:
        any_keys = tuple(rule.get("require_any", ()))
        all_keys = tuple(rule.get("require_all", ()))
        label = str(rule.get("label") or "Conditional parameter requirement is not satisfied")
        for key in (*any_keys, *all_keys):
            if key not in definitions: errors.append(f"conditional rule references unknown parameter {key!r}")
        if any_keys and not any(normalized.get(key) is not None for key in any_keys): errors.append(label)
        if all_keys and not all(normalized.get(key) is not None for key in all_keys): errors.append(label)
    if errors:
        raise ValueError(f"{equipment_type} engineering validation failed: " + "; ".join(errors))
    return normalized


class CreationCommandPreparer:
    """Single Application boundary that constructs immutable create commands."""

    @staticmethod
    def command_class(command_type: str) -> type[Command]:
        try:
            return _CREATE_COMMANDS[command_type]
        except KeyError as exc:
            raise ValueError(f"Unsupported creation command type: {command_type!r}") from exc

    @classmethod
    def prepare(cls, intent: CreationCommitIntent) -> Command:
        if not isinstance(intent, CreationCommitIntent):
            raise TypeError("intent must be a CreationCommitIntent.")
        values = validate_creation_values(intent.command_type, intent.values, intent.parameter_mapping, intent.parameter_contract, intent.conditional_requirements)
        command_class = cls.command_class(intent.command_type)
        signature = inspect.signature(command_class)
        fields = {
            name for name, parameter in signature.parameters.items()
            if name not in {"self", "command_id", "correlation_id", "causation_id"}
        }
        unknown_values = set(values) - set(intent.parameter_mapping)
        if unknown_values:
            raise ValueError(
                f"{intent.command_type}: unmapped engineering values: {sorted(unknown_values)!r}"
            )
        unknown_endpoints = set(intent.endpoints) - set(intent.endpoint_mapping)
        if unknown_endpoints:
            raise ValueError(
                f"{intent.command_type}: unmapped endpoint values: {sorted(unknown_endpoints)!r}"
            )

        # Validate destinations before constructing the payload: ordinary dict
        # assignment would otherwise silently overwrite engineering values,
        # endpoints, the object identity, or generated presentation coordinates.
        parameter_targets: dict[str, list[str]] = {}
        for parameter_id, command_field in intent.parameter_mapping.items():
            if isinstance(command_field, str) and command_field.strip():
                parameter_targets.setdefault(command_field, []).append(parameter_id)
        duplicate_parameter_targets = {
            field: sorted(keys)
            for field, keys in parameter_targets.items()
            if len(keys) > 1
        }
        if duplicate_parameter_targets:
            details = "; ".join(
                f"{field!r} <- {keys!r}"
                for field, keys in sorted(duplicate_parameter_targets.items())
            )
            raise ValueError(
                f"{intent.command_type}: multiple engineering parameters target the same "
                f"command field: {details}"
            )

        endpoint_targets: dict[str, list[str]] = {}
        for semantic_name, command_field in intent.endpoint_mapping.items():
            if isinstance(command_field, str) and command_field.strip():
                endpoint_targets.setdefault(command_field, []).append(semantic_name)
        duplicate_endpoint_targets = {
            field: sorted(keys)
            for field, keys in endpoint_targets.items()
            if len(keys) > 1
        }
        if duplicate_endpoint_targets:
            details = "; ".join(
                f"{field!r} <- {keys!r}"
                for field, keys in sorted(duplicate_endpoint_targets.items())
            )
            raise ValueError(
                f"{intent.command_type}: multiple endpoint roles target the same "
                f"command field: {details}"
            )

        parameter_fields = set(parameter_targets)
        endpoint_fields = set(endpoint_targets)
        cross_collisions = parameter_fields & endpoint_fields
        if cross_collisions:
            details = "; ".join(
                f"{field!r} (parameters={sorted(parameter_targets[field])!r}, "
                f"endpoints={sorted(endpoint_targets[field])!r})"
                for field in sorted(cross_collisions)
            )
            raise ValueError(
                f"{intent.command_type}: engineering and endpoint mappings collide: {details}"
            )

        mapped_fields = parameter_fields | endpoint_fields
        if intent.id_field in mapped_fields:
            owners = []
            if intent.id_field in parameter_targets:
                owners.append(f"parameters={sorted(parameter_targets[intent.id_field])!r}")
            if intent.id_field in endpoint_targets:
                owners.append(f"endpoints={sorted(endpoint_targets[intent.id_field])!r}")
            raise ValueError(
                f"{intent.command_type}: mapped field {intent.id_field!r} collides with "
                f"the object ID field ({', '.join(owners)})."
            )

        generated_position_fields = set()
        if intent.position is not None:
            generated_position_fields = {
                field for field in ("presentation_x", "presentation_y", "x", "y")
                if field in fields
            }
            position_collisions = mapped_fields & generated_position_fields
            if position_collisions:
                details = "; ".join(
                    f"{field!r} (parameters={sorted(parameter_targets.get(field, []))!r}, "
                    f"endpoints={sorted(endpoint_targets.get(field, []))!r})"
                    for field in sorted(position_collisions)
                )
                raise ValueError(
                    f"{intent.command_type}: explicit mappings collide with generated "
                    f"position fields: {details}"
                )

        payload: dict[str, Any] = {intent.id_field: intent.object_id}
        for parameter_id, command_field in intent.parameter_mapping.items():
            if parameter_id in values and values[parameter_id] is not None:
                payload[command_field] = values[parameter_id]
        for semantic_name, command_field in intent.endpoint_mapping.items():
            endpoint = intent.endpoints.get(semantic_name)
            if endpoint is not None:
                payload[command_field] = endpoint
        if intent.position is not None:
            x, y = intent.position
            if "presentation_x" in fields: payload["presentation_x"] = x
            if "presentation_y" in fields: payload["presentation_y"] = y
            if "x" in fields: payload["x"] = x
            if "y" in fields: payload["y"] = y
        unknown = set(payload) - fields
        if unknown:
            raise ValueError(f"{intent.command_type}: unmapped creation payload fields: {sorted(unknown)!r}")
        missing = [
            name for name, parameter in signature.parameters.items()
            if name not in {"self", "command_id", "correlation_id", "causation_id"}
            and parameter.default is inspect.Parameter.empty
            and name not in payload
        ]
        if missing:
            raise ValueError(f"{intent.command_type}: required command fields have no creation source: {missing!r}")
        return command_class(**payload)

def creation_command_contract(command_type: str) -> type[Command]:
    return CreationCommandPreparer.command_class(command_type)

__all__ = ["CreationCommitIntent", "CreationCommandPreparer", "creation_command_contract"]
