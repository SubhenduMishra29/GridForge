# Author: Subhendu Mishra
"""Application command handlers for project-scoped protection configuration."""

from __future__ import annotations

from typing import Mapping

from .commands.protection_configuration_commands import (
    CREATE_PROTECTION_CONFIGURATION,
    UPDATE_PROTECTION_CONFIGURATION,
    DELETE_PROTECTION_CONFIGURATION,
    BIND_PROTECTION_MEASUREMENT,
    UNBIND_PROTECTION_MEASUREMENT,
    REBIND_PROTECTION_MEASUREMENT_BINDING,
    SET_SYNCHRONISM_CHECK_CONFIGURATION,
    CREATE_DIFFERENTIAL_SCHEME,
    UPDATE_DIFFERENTIAL_SCHEME,
    DELETE_DIFFERENTIAL_SCHEME,
)


class ProtectionConfigurationHandlers:
    """Bind protection configuration commands to the canonical Application service."""

    def __init__(self, service) -> None:
        if service is None:
            raise ValueError("service is required.")
        self._service = service

    def handlers(self) -> Mapping[str, object]:
        return {
            CREATE_PROTECTION_CONFIGURATION: self.create_configuration,
            UPDATE_PROTECTION_CONFIGURATION: self.update_configuration,
            DELETE_PROTECTION_CONFIGURATION: self.delete_configuration,
            BIND_PROTECTION_MEASUREMENT: self.bind_measurement,
            UNBIND_PROTECTION_MEASUREMENT: self.unbind_measurement,
            REBIND_PROTECTION_MEASUREMENT_BINDING: self.rebind_measurement_binding,
            SET_SYNCHRONISM_CHECK_CONFIGURATION: self.set_synchronism_check_configuration,
            CREATE_DIFFERENTIAL_SCHEME: self.create_differential_scheme,
            UPDATE_DIFFERENTIAL_SCHEME: self.update_differential_scheme,
            DELETE_DIFFERENTIAL_SCHEME: self.delete_differential_scheme,
        }

    def create_configuration(self, command, context, transaction):
        return self._service.create_configuration(transaction=transaction, **command.payload)

    def update_configuration(self, command, context, transaction):
        return self._service.update_configuration(transaction=transaction, **command.payload)

    def delete_configuration(self, command, context, transaction):
        return self._service.delete_configuration(transaction=transaction, **command.payload)

    def bind_measurement(self, command, context, transaction):
        return self._service.bind_measurement(transaction=transaction, **command.payload)

    def unbind_measurement(self, command, context, transaction):
        return self._service.unbind_measurement(transaction=transaction, **command.payload)

    def rebind_measurement_binding(self, command, context, transaction):
        binding = command.payload["binding"]
        if (
            command.payload["binding_id"] != binding.binding_id
            or command.payload["protection_element_id"] != binding.protection_element_id
        ):
            raise ValueError("Rebind command identity metadata does not match its immutable binding.")
        return self._service.rebind_measurement_binding(transaction=transaction, binding=binding)

    def set_synchronism_check_configuration(self, command, context, transaction):
        return self._service.set_synchronism_check_configuration(transaction=transaction, **command.payload)

    @staticmethod
    def _differential_scheme_from_command(command):
        scheme = command.payload["scheme"]
        owner_id = command.payload["protection_element_id"]
        if owner_id != scheme.protection_element_id:
            raise ValueError("Differential command owner metadata does not match its immutable scheme.")
        return scheme

    def create_differential_scheme(self, command, context, transaction):
        scheme = self._differential_scheme_from_command(command)
        return self._service.create_differential_scheme(transaction=transaction, scheme=scheme)

    def update_differential_scheme(self, command, context, transaction):
        scheme = self._differential_scheme_from_command(command)
        return self._service.update_differential_scheme(transaction=transaction, scheme=scheme)

    def delete_differential_scheme(self, command, context, transaction):
        return self._service.delete_differential_scheme(transaction=transaction, **command.payload)

__all__ = ["ProtectionConfigurationHandlers"]
