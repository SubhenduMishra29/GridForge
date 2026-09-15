"""Immutable Application commands for project-scoped protection configuration."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID, uuid4

from core.protection.project_configuration import ProtectionFunctionConfiguration

from ..command import Command

CREATE_PROTECTION_CONFIGURATION = "protection.create_configuration"
UPDATE_PROTECTION_CONFIGURATION = "protection.update_configuration"
DELETE_PROTECTION_CONFIGURATION = "protection.delete_configuration"


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


class DeleteProtectionConfigurationCommand(Command):
    def __init__(self, *, element_id: str,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(element_id, str) or not element_id.strip():
            raise ValueError("element_id must be a non-empty string.")
        super().__init__(**_command(DELETE_PROTECTION_CONFIGURATION, {"element_id": element_id.strip()},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


__all__ = [
    "CREATE_PROTECTION_CONFIGURATION", "UPDATE_PROTECTION_CONFIGURATION", "DELETE_PROTECTION_CONFIGURATION",
    "CreateProtectionConfigurationCommand", "UpdateProtectionConfigurationCommand",
    "DeleteProtectionConfigurationCommand",
]
