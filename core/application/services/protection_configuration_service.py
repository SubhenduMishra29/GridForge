# ============================================================
# File: core/application/services/protection_configuration_service.py
# GridForge V2 — Protection Configuration Service
# Author: Subhendu Mishra
# ============================================================

"""Application service for project-scoped protection configuration."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from core.application.errors import DomainError, ResourceError
from core.application.results import ApplicationResult
from core.application.transaction import Transaction
from core.network.network import Network
from core.measurement.measurement_channel import MeasurementChannel
from core.protection.factory import ProtectionFactory
from core.protection.function_catalog import ProtectionFunctionStatus, get_protection_function
from core.protection.project_configuration import (
    ProtectionFunctionConfiguration,
    ProtectionProjectConfiguration,
)


class ProtectionConfigurationService:
    """Own mutable project association state without owning physical equipment."""

    def __init__(self, configuration: ProtectionProjectConfiguration, network_provider: Callable[[], Network | None] | None = None, measurement_channel_provider: Callable[[], Mapping[str, MeasurementChannel]] | None = None) -> None:
        self._configuration: ProtectionProjectConfiguration | None = None
        if network_provider is not None and not callable(network_provider): raise TypeError("network_provider must be callable.")
        if measurement_channel_provider is not None and not callable(measurement_channel_provider): raise TypeError("measurement_channel_provider must be callable.")
        self._network_provider = network_provider
        self._measurement_channel_provider = measurement_channel_provider; self.activate(configuration)

    @property
    def configuration(self) -> ProtectionProjectConfiguration | None: return self._configuration
    def activate(self, configuration: ProtectionProjectConfiguration) -> None:
        if not isinstance(configuration, ProtectionProjectConfiguration): raise TypeError("configuration must be ProtectionProjectConfiguration.")
        self._configuration = configuration
    def deactivate(self) -> None: self._configuration = None
    def _require_configuration(self) -> ProtectionProjectConfiguration:
        if self._configuration is None: raise RuntimeError("No active project protection configuration.")
        return self._configuration

    def validate_configuration(self, configuration: ProtectionFunctionConfiguration) -> None:
        """Validate one protection configuration against active Application state."""
        self._validate_configuration(configuration)

    def _validate_configuration(self, configuration: ProtectionFunctionConfiguration) -> None:
        if not isinstance(configuration.settings, Mapping): raise TypeError("Protection configuration settings must be a mapping.")
        spec = get_protection_function(configuration.function_code)
        if spec.status is not ProtectionFunctionStatus.IMPLEMENTED or spec.implementation is None:
            raise DomainError(code="PROTECTION_FUNCTION_NOT_IMPLEMENTED", message=f"Protection function is not implemented: {configuration.function_code}", details={"function_code": configuration.function_code})
        ProtectionFactory._build_settings(spec.implementation, configuration.settings)
        for name, channel_id in configuration.input_channel_ids.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(channel_id, str) or not channel_id.strip(): raise ValueError("Protection input channel names and IDs must be non-empty strings.")
        if self._measurement_channel_provider is not None:
            channels = self._measurement_channel_provider()
            for name, channel_id in configuration.input_channel_ids.items():
                if channel_id not in channels:
                    raise ResourceError(code="PROTECTION_CHANNEL_NOT_FOUND", message=f"Measurement channel not found for protection input {name}: {channel_id}", details={"channel_id": channel_id, "element_id": configuration.element_id, "input_name": name})
                if not isinstance(channels[channel_id], MeasurementChannel):
                    raise TypeError(f"Measurement channel provider returned an invalid channel for {channel_id}.")
        if self._network_provider is not None:
            network = self._network_provider()
            if network is None: raise RuntimeError("No active Network is available for protection configuration validation.")
            try: network.get_by_id("relay", configuration.relay_id)
            except KeyError as exc:
                raise ResourceError(code="PROTECTION_RELAY_NOT_FOUND", message=f"Relay not found for protection configuration: {configuration.relay_id}", details={"relay_id": configuration.relay_id, "element_id": configuration.element_id}) from exc

    def create_configuration(self, *, configuration: ProtectionFunctionConfiguration, transaction: Transaction) -> ApplicationResult[ProtectionFunctionConfiguration]:
        self._require_transaction(transaction)
        if not isinstance(configuration, ProtectionFunctionConfiguration): raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        self._validate_configuration(configuration); active = self._require_configuration()
        try: active.get(configuration.element_id)
        except KeyError: pass
        else: raise DomainError(code="PROTECTION_CONFIGURATION_ALREADY_EXISTS", message=f"Protection configuration already exists: {configuration.element_id}", details={"element_id": configuration.element_id})
        active.add(configuration); transaction.record_undo(lambda: active.remove(configuration.element_id)); return self._success(configuration, f"Protection configuration created: {configuration.element_id}")

    def update_configuration(self, *, configuration: ProtectionFunctionConfiguration, transaction: Transaction) -> ApplicationResult[ProtectionFunctionConfiguration]:
        self._require_transaction(transaction)
        if not isinstance(configuration, ProtectionFunctionConfiguration): raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        self._validate_configuration(configuration); active = self._require_configuration()
        try: previous = active.get(configuration.element_id)
        except KeyError as exc: raise ResourceError(code="PROTECTION_CONFIGURATION_NOT_FOUND", message=f"Protection configuration not found: {configuration.element_id}", details={"element_id": configuration.element_id}) from exc
        active.replace(configuration); transaction.record_undo(lambda previous=previous: active.replace(previous)); return self._success(configuration, f"Protection configuration updated: {configuration.element_id}")

    def delete_configuration(self, *, element_id: str, transaction: Transaction) -> ApplicationResult[ProtectionFunctionConfiguration]:
        self._require_transaction(transaction)
        if not isinstance(element_id, str) or not element_id.strip(): raise ValueError("element_id must be a non-empty string.")
        active = self._require_configuration()
        try: previous = active.remove(element_id.strip())
        except KeyError as exc: raise ResourceError(code="PROTECTION_CONFIGURATION_NOT_FOUND", message=f"Protection configuration not found: {element_id}", details={"element_id": element_id}) from exc
        transaction.record_undo(lambda previous=previous: active.add(previous)); return self._success(previous, f"Protection configuration deleted: {element_id}")

    @staticmethod
    def _require_transaction(transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction): raise TypeError("transaction must be a Transaction.")
        if not transaction.active: raise RuntimeError("Transaction must be active.")

    def _success(self, value: ProtectionFunctionConfiguration, message: str) -> ApplicationResult[ProtectionFunctionConfiguration]:
        return ApplicationResult.success_result(value=value, message=message, metadata={"object_type": "protection_configuration", "object_id": value.element_id})


__all__ = ["ProtectionConfigurationService"]
