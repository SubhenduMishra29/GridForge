# ============================================================
# File: core/application/creation.py
# GridForge V2 — Application creation intent preparation boundary
# Author: Subhendu Mishra
# ============================================================
"""Application-owned translation from immutable creation intent to commands."""

from __future__ import annotations

import inspect
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
        if self.position is not None:
            object.__setattr__(self, "position", (float(self.position[0]), float(self.position[1])))

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
        command_class = cls.command_class(intent.command_type)
        signature = inspect.signature(command_class)
        fields = {
            name for name, parameter in signature.parameters.items()
            if name not in {"self", "command_id", "correlation_id", "causation_id"}
        }
        unknown_values = set(intent.values) - set(intent.parameter_mapping)
        if unknown_values:
            raise ValueError(
                f"{intent.command_type}: unmapped engineering values: {sorted(unknown_values)!r}"
            )
        unknown_endpoints = set(intent.endpoints) - set(intent.endpoint_mapping)
        if unknown_endpoints:
            raise ValueError(
                f"{intent.command_type}: unmapped endpoint values: {sorted(unknown_endpoints)!r}"
            )

        payload: dict[str, Any] = {intent.id_field: intent.object_id}
        for parameter_id, command_field in intent.parameter_mapping.items():
            if parameter_id in intent.values and intent.values[parameter_id] is not None:
                payload[command_field] = intent.values[parameter_id]
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
