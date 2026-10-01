# Author: Subhendu Mishra
"""Immutable Application commands for project-scoped protection configuration."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID, uuid4

from core.protection.project_configuration import ProtectionFunctionConfiguration

from ..command import Command

CREATE_PROTECTION_CONFIGURATION = "protection.create_configuration"
UPDATE_PROTECTION_CONFIGURATION = "protection.update_configuration"
DELETE_PROTECTION_CONFIGURATION = "protection.delete_configuration"
BIND_PROTECTION_MEASUREMENT = "protection.bind_measurement"
UNBIND_PROTECTION_MEASUREMENT = "protection.unbind_measurement"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


class CreateProtectionConfigurationCommand(Command):
    def __init__(self, *, configuration: ProtectionFunctionConfiguration,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(configuration, ProtectionFunctionConfiguration):
            raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        super().__init__(**_command(CREATE_PROTECTION_CONFIGURATION, {"configuration": configuration},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class UpdateProtectionConfigurationCommand(Command):
    def __init__(self, *, configuration: ProtectionFunctionConfiguration,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(configuration, ProtectionFunctionConfiguration):
            raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        super().__init__(**_command(UPDATE_PROTECTION_CONFIGURATION, {"configuration": configuration},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class BindProtectionMeasurementCommand(Command):
    """Bind one canonical MeasurementChannel to one configured relay input."""

    def __init__(self, *, element_id: str, input_name: str, channel_id: str,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        for name, value in (("element_id", element_id), ("input_name", input_name), ("channel_id", channel_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        super().__init__(**_command(
            BIND_PROTECTION_MEASUREMENT,
            {"element_id": element_id.strip(), "input_name": input_name.strip(), "channel_id": channel_id.strip()},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class UnbindProtectionMeasurementCommand(Command):
    """Remove one relay-input MeasurementChannel binding."""

    def __init__(self, *, element_id: str, input_name: str,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        for name, value in (("element_id", element_id), ("input_name", input_name)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        super().__init__(**_command(
            UNBIND_PROTECTION_MEASUREMENT,
            {"element_id": element_id.strip(), "input_name": input_name.strip()},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))

class DeleteProtectionConfigurationCommand(Command):
    def __init__(self, *, element_id: str,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(element_id, str) or not element_id.strip():
            raise ValueError("element_id must be a non-empty string.")
        super().__init__(**_command(DELETE_PROTECTION_CONFIGURATION, {"element_id": element_id.strip()},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


__all__ = [
    "CREATE_PROTECTION_CONFIGURATION", "UPDATE_PROTECTION_CONFIGURATION", "DELETE_PROTECTION_CONFIGURATION", "BIND_PROTECTION_MEASUREMENT", "UNBIND_PROTECTION_MEASUREMENT",
    "CreateProtectionConfigurationCommand", "UpdateProtectionConfigurationCommand",
    "DeleteProtectionConfigurationCommand", "BindProtectionMeasurementCommand", "UnbindProtectionMeasurementCommand",
]
