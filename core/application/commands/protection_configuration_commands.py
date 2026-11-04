# Author: Subhendu Mishra
"""Immutable Application commands for project-scoped protection configuration."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID, uuid4

from core.protection.project_configuration import (
    DifferentialProtectionSchemeConfiguration,
    ProtectionFunctionConfiguration,
)

from ..command import Command

CREATE_PROTECTION_CONFIGURATION = "protection.create_configuration"
UPDATE_PROTECTION_CONFIGURATION = "protection.update_configuration"
DELETE_PROTECTION_CONFIGURATION = "protection.delete_configuration"
BIND_PROTECTION_MEASUREMENT = "protection.bind_measurement"
UNBIND_PROTECTION_MEASUREMENT = "protection.unbind_measurement"
SET_SYNCHRONISM_CHECK_CONFIGURATION = "protection.set_synchronism_check_configuration"
CREATE_DIFFERENTIAL_SCHEME = "protection.create_differential_scheme"
UPDATE_DIFFERENTIAL_SCHEME = "protection.update_differential_scheme"
DELETE_DIFFERENTIAL_SCHEME = "protection.delete_differential_scheme"


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



class CreateDifferentialSchemeCommand(Command):
    def __init__(self, *, scheme: DifferentialProtectionSchemeConfiguration,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
            raise TypeError("scheme must be DifferentialProtectionSchemeConfiguration.")
        super().__init__(**_command(CREATE_DIFFERENTIAL_SCHEME, {
            "scheme": scheme, "protection_element_id": scheme.protection_element_id,
        },
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class UpdateDifferentialSchemeCommand(Command):
    def __init__(self, *, scheme: DifferentialProtectionSchemeConfiguration,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
            raise TypeError("scheme must be DifferentialProtectionSchemeConfiguration.")
        super().__init__(**_command(UPDATE_DIFFERENTIAL_SCHEME, {
            "scheme": scheme, "protection_element_id": scheme.protection_element_id,
        },
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class DeleteDifferentialSchemeCommand(Command):
    def __init__(self, *, scheme_id: str,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        if not isinstance(scheme_id, str) or not scheme_id.strip():
            raise ValueError("scheme_id must be a non-empty string.")
        super().__init__(**_command(DELETE_DIFFERENTIAL_SCHEME, {"scheme_id": scheme_id.strip()},
                                   command_id=command_id, correlation_id=correlation_id, causation_id=causation_id))


class SetSynchronismCheckConfigurationCommand(Command):
    """Replace or disable the active project's typed ANSI 25 breaker-policy registry."""

    def __init__(
        self,
        *,
        configuration: Mapping[str, Any] | None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if configuration is not None and not isinstance(configuration, Mapping):
            raise TypeError("configuration must be a mapping or None.")
        payload = None if configuration is None else dict(configuration)
        super().__init__(**_command(
            SET_SYNCHRONISM_CHECK_CONFIGURATION,
            {"configuration": payload},
            command_id=command_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
        ))


__all__ = [
    "CREATE_PROTECTION_CONFIGURATION", "UPDATE_PROTECTION_CONFIGURATION", "DELETE_PROTECTION_CONFIGURATION", "BIND_PROTECTION_MEASUREMENT", "UNBIND_PROTECTION_MEASUREMENT", "SET_SYNCHRONISM_CHECK_CONFIGURATION",
    "CREATE_DIFFERENTIAL_SCHEME", "UPDATE_DIFFERENTIAL_SCHEME", "DELETE_DIFFERENTIAL_SCHEME",
    "CreateDifferentialSchemeCommand", "UpdateDifferentialSchemeCommand", "DeleteDifferentialSchemeCommand",
    "CreateProtectionConfigurationCommand", "UpdateProtectionConfigurationCommand",
    "DeleteProtectionConfigurationCommand", "BindProtectionMeasurementCommand", "UnbindProtectionMeasurementCommand",
    "SetSynchronismCheckConfigurationCommand",
]
