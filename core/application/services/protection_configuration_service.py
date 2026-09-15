"""Application service for project-scoped protection configuration."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.transaction import Transaction
from core.errors import DomainError, ResourceError
from core.protection.project_configuration import (
    ProtectionFunctionConfiguration,
    ProtectionProjectConfiguration,
)


class ProtectionConfigurationService:
    """Own mutable project association state without owning physical equipment."""

    def __init__(self, configuration: ProtectionProjectConfiguration) -> None:
        self._configuration: ProtectionProjectConfiguration | None = None
        self.activate(configuration)

    @property
    def configuration(self) -> ProtectionProjectConfiguration | None:
        return self._configuration

    def activate(self, configuration: ProtectionProjectConfiguration) -> None:
        if not isinstance(configuration, ProtectionProjectConfiguration):
            raise TypeError("configuration must be ProtectionProjectConfiguration.")
        self._configuration = configuration

    def deactivate(self) -> None:
        """Detach project-scoped protection configuration when no project is active."""
        self._configuration = None

    def _require_configuration(self) -> ProtectionProjectConfiguration:
        if self._configuration is None:
            raise RuntimeError("No active project protection configuration.")
        return self._configuration

    def create_configuration(
        self,
        *,
        configuration: ProtectionFunctionConfiguration,
        transaction: Transaction,
    ) -> ApplicationResult[ProtectionFunctionConfiguration]:
        self._require_transaction(transaction)
        if not isinstance(configuration, ProtectionFunctionConfiguration):
            raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        active = self._require_configuration()
        try:
            active.get(configuration.element_id)
        except KeyError:
            pass
        else:
            raise DomainError(
                code="PROTECTION_CONFIGURATION_ALREADY_EXISTS",
                message=f"Protection configuration already exists: {configuration.element_id}",
                details={"element_id": configuration.element_id},
            )
        active.add(configuration)
        transaction.record_undo(lambda: active.remove(configuration.element_id))
        return self._success(configuration, f"Protection configuration created: {configuration.element_id}")

    def update_configuration(
        self,
        *,
        configuration: ProtectionFunctionConfiguration,
        transaction: Transaction,
    ) -> ApplicationResult[ProtectionFunctionConfiguration]:
        self._require_transaction(transaction)
        if not isinstance(configuration, ProtectionFunctionConfiguration):
            raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        active = self._require_configuration()
        try:
            previous = active.get(configuration.element_id)
        except KeyError as exc:
            raise ResourceError(
                code="PROTECTION_CONFIGURATION_NOT_FOUND",
                message=f"Protection configuration not found: {configuration.element_id}",
                details={"element_id": configuration.element_id},
            ) from exc
        active.replace(configuration)
        transaction.record_undo(lambda previous=previous: active.replace(previous))
        return self._success(configuration, f"Protection configuration updated: {configuration.element_id}")

    def delete_configuration(
        self,
        *,
        element_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[ProtectionFunctionConfiguration]:
        self._require_transaction(transaction)
        if not isinstance(element_id, str) or not element_id.strip():
            raise ValueError("element_id must be a non-empty string.")
        active = self._require_configuration()
        try:
            previous = active.remove(element_id.strip())
        except KeyError as exc:
            raise ResourceError(
                code="PROTECTION_CONFIGURATION_NOT_FOUND",
                message=f"Protection configuration not found: {element_id}",
                details={"element_id": element_id},
            ) from exc
        transaction.record_undo(lambda previous=previous: active.add(previous))
        return self._success(previous, f"Protection configuration deleted: {element_id}")

    @staticmethod
    def _require_transaction(transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction.")
        if not transaction.active:
            raise RuntimeError("Transaction must be active.")

    def _success(self, value: ProtectionFunctionConfiguration, message: str) -> ApplicationResult[ProtectionFunctionConfiguration]:
        return ApplicationResult.success_result(
            value=value,
            message=message,
            metadata={"object_type": "protection_configuration", "object_id": value.element_id},
        )


__all__ = ["ProtectionConfigurationService"]
