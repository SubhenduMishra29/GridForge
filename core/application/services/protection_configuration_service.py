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
from core.protection.input_contracts import validate_protection_input_contracts
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
            contract_diagnostics = validate_protection_input_contracts(
                configuration, channels, require_all_bindings=False
            )
            if contract_diagnostics:
                raise DomainError(
                    code="PROTECTION_INPUT_CONTRACT_INVALID",
                    message="Protection input binding violates its declared measurement contract.",
                    details={"element_id": configuration.element_id, "diagnostics": contract_diagnostics},
                )
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

    def bind_measurement(self, *, element_id: str, input_name: str, channel_id: str,
                         transaction: Transaction) -> ApplicationResult[ProtectionFunctionConfiguration]:
        """Atomically bind a MeasurementChannel to a configured Relay input.

        The project configuration and the live Relay input projection are
        changed under the same Application transaction.  The Relay remains
        physical Core truth; the configuration aggregate remains persistence
        authority for the association.
        """
        self._require_transaction(transaction)
        active = self._require_configuration()
        configuration = active.get(str(element_id).strip())
        normalized_input = str(input_name).strip()
        normalized_channel = str(channel_id).strip()
        if not normalized_input or not normalized_channel:
            raise ValueError("input_name and channel_id must be non-empty strings.")
        channels = self._measurement_channel_provider() if self._measurement_channel_provider is not None else {}
        try:
            channel = channels[normalized_channel]
        except KeyError as exc:
            raise ResourceError(
                code="PROTECTION_CHANNEL_NOT_FOUND",
                message=f"Measurement channel not found: {normalized_channel}",
                details={"channel_id": normalized_channel, "element_id": configuration.element_id},
            ) from exc
        network = self._network_provider() if self._network_provider is not None else None
        if network is None:
            raise RuntimeError("No active Network is available for protection measurement binding.")
        relay = network.get_by_id("relay", configuration.relay_id)
        previous_configuration = configuration
        try:
            previous_channel = relay.get_input(normalized_input)
        except KeyError:
            previous_channel = None
        next_inputs = dict(configuration.input_channel_ids)
        next_inputs[normalized_input] = normalized_channel
        next_configuration = ProtectionFunctionConfiguration(
            element_id=configuration.element_id,
            relay_id=configuration.relay_id,
            function_code=configuration.function_code,
            settings=configuration.settings,
            input_channel_ids=next_inputs,
            enabled=configuration.enabled,
            blocked=configuration.blocked,
            priority=configuration.priority,
            name=configuration.name,
            metadata=configuration.metadata,
        )
        self._validate_configuration(next_configuration)
        relay.bind_input(normalized_input, channel)
        active.replace(next_configuration)

        def undo() -> None:
            active.replace(previous_configuration)
            if previous_channel is None:
                relay.unbind_input(normalized_input)
            else:
                relay.bind_input(normalized_input, previous_channel)

        transaction.record_undo(undo)
        return self._success(
            next_configuration,
            f"Protection measurement bound: {configuration.element_id}:{normalized_input} -> {normalized_channel}",
        )

    def unbind_measurement(self, *, element_id: str, input_name: str,
                           transaction: Transaction) -> ApplicationResult[ProtectionFunctionConfiguration]:
        """Atomically remove a MeasurementChannel from one Relay input."""
        self._require_transaction(transaction)
        active = self._require_configuration()
        configuration = active.get(str(element_id).strip())
        normalized_input = str(input_name).strip()
        if not normalized_input:
            raise ValueError("input_name must be a non-empty string.")
        if normalized_input not in configuration.input_channel_ids:
            raise ResourceError(
                code="PROTECTION_INPUT_NOT_BOUND",
                message=f"Protection input is not bound: {normalized_input}",
                details={"element_id": configuration.element_id, "input_name": normalized_input},
            )
        network = self._network_provider() if self._network_provider is not None else None
        if network is None:
            raise RuntimeError("No active Network is available for protection measurement binding.")
        relay = network.get_by_id("relay", configuration.relay_id)
        previous_configuration = configuration
        try:
            previous_channel = relay.get_input(normalized_input)
        except KeyError:
            previous_channel = None
        next_inputs = dict(configuration.input_channel_ids)
        next_inputs.pop(normalized_input, None)
        next_configuration = ProtectionFunctionConfiguration(
            element_id=configuration.element_id,
            relay_id=configuration.relay_id,
            function_code=configuration.function_code,
            settings=configuration.settings,
            input_channel_ids=next_inputs,
            enabled=configuration.enabled,
            blocked=configuration.blocked,
            priority=configuration.priority,
            name=configuration.name,
            metadata=configuration.metadata,
        )
        self._validate_configuration(next_configuration)
        relay.unbind_input(normalized_input)
        active.replace(next_configuration)

        def undo() -> None:
            active.replace(previous_configuration)
            if previous_channel is not None:
                relay.bind_input(normalized_input, previous_channel)

        transaction.record_undo(undo)
        return self._success(
            next_configuration,
            f"Protection measurement unbound: {configuration.element_id}:{normalized_input}",
        )

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
