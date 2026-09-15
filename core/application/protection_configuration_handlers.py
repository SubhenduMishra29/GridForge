"""Application command handlers for project-scoped protection configuration."""

from __future__ import annotations

from typing import Mapping

from .commands.protection_configuration_commands import (
    CREATE_PROTECTION_CONFIGURATION,
    UPDATE_PROTECTION_CONFIGURATION,
    DELETE_PROTECTION_CONFIGURATION,
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
        }

    def create_configuration(self, command, context, transaction):
        return self._service.create_configuration(transaction=transaction, **command.payload)

    def update_configuration(self, command, context, transaction):
        return self._service.update_configuration(transaction=transaction, **command.payload)

    def delete_configuration(self, command, context, transaction):
        return self._service.delete_configuration(transaction=transaction, **command.payload)


__all__ = ["ProtectionConfigurationHandlers"]
