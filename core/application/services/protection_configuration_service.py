# ============================================================
# File: core/application/services/protection_configuration_service.py
# GridForge V2 — Protection Configuration Service
# Author: Subhendu Mishra
# ============================================================

"""Application service for project-scoped protection configuration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from math import isfinite

from core.application.errors import DomainError, ResourceError
from core.application.results import ApplicationResult
from core.application.transaction import Transaction
from core.model import Branch, Bus, CurrentTransformer, EndpointReference, EquipmentType
from core.network.connectivity import ConnectivityResolver
from core.network.topology_endpoint_reference import TopologyEndpointReference
from core.network.network import Network
from core.measurement.measurement_channel import MeasurementChannel
from core.protection.factory import ProtectionFactory
from core.protection.function_catalog import ProtectionFunctionStatus, get_protection_function
from core.protection.input_contracts import validate_protection_input_contracts
from core.protection.protection_measurement_binding import ProtectionMeasurementBinding
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

    def validate_configuration(
        self,
        configuration: ProtectionFunctionConfiguration,
        *,
        network: Network | None = None,
        channels: Mapping[str, MeasurementChannel] | None = None,
    ) -> None:
        """Validate against active state or explicit candidate activation authorities.

        Candidate project activation runs before ProjectLifecycleService publishes
        its new network pointer. Supplying the candidate authorities prevents
        validation from accidentally consulting the previous project's providers.
        """
        self._validate_configuration(configuration, network=network, channels=channels)

    def _validate_configuration(
        self,
        configuration: ProtectionFunctionConfiguration,
        *,
        network: Network | None = None,
        channels: Mapping[str, MeasurementChannel] | None = None,
    ) -> None:
        if not isinstance(configuration.settings, Mapping): raise TypeError("Protection configuration settings must be a mapping.")
        spec = get_protection_function(configuration.function_code)
        if spec.status is not ProtectionFunctionStatus.IMPLEMENTED or spec.implementation is None:
            raise DomainError(code="PROTECTION_FUNCTION_NOT_IMPLEMENTED", message=f"Protection function is not implemented: {configuration.function_code}", details={"function_code": configuration.function_code})
        ProtectionFactory._build_settings(spec.implementation, configuration.settings)
        for name, channel_id in configuration.input_channel_ids.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(channel_id, str) or not channel_id.strip(): raise ValueError("Protection input channel names and IDs must be non-empty strings.")
        active_channels = channels
        if active_channels is None and self._measurement_channel_provider is not None:
            active_channels = self._measurement_channel_provider()
        if active_channels is not None:
            for name, channel_id in configuration.input_channel_ids.items():
                if channel_id not in active_channels:
                    raise ResourceError(code="PROTECTION_CHANNEL_NOT_FOUND", message=f"Measurement channel not found for protection input {name}: {channel_id}", details={"channel_id": channel_id, "element_id": configuration.element_id, "input_name": name})
                if not isinstance(active_channels[channel_id], MeasurementChannel):
                    raise TypeError(f"Measurement channel provider returned an invalid channel for {channel_id}.")
            contract_diagnostics = validate_protection_input_contracts(
                configuration, active_channels, require_all_bindings=False
            )
            if contract_diagnostics:
                raise DomainError(
                    code="PROTECTION_INPUT_CONTRACT_INVALID",
                    message="Protection input binding violates its declared measurement contract.",
                    details={"element_id": configuration.element_id, "diagnostics": contract_diagnostics},
                )
        active_network = network
        if active_network is None and self._network_provider is not None:
            active_network = self._network_provider()
        if active_network is not None:
            try:
                active_network.get_by_id("relay", configuration.relay_id)
            except KeyError as exc:
                raise ResourceError(code="PROTECTION_RELAY_NOT_FOUND", message=f"Relay not found for protection configuration: {configuration.relay_id}", details={"relay_id": configuration.relay_id, "element_id": configuration.element_id}) from exc
            if configuration.action_target_type is not None:
                try:
                    target = active_network.get_by_id(
                        configuration.action_target_type,
                        configuration.action_target_id,
                    )
                except (KeyError, ValueError) as exc:
                    raise ResourceError(
                        code="PROTECTION_ACTION_TARGET_NOT_FOUND",
                        message=(
                            "Protection action target not found: "
                            f"{configuration.action_target_type}:{configuration.action_target_id}"
                        ),
                        details={
                            "element_id": configuration.element_id,
                            "target_type": configuration.action_target_type,
                            "target_id": configuration.action_target_id,
                        },
                    ) from exc
                if target is None:
                    raise ResourceError(
                        code="PROTECTION_ACTION_TARGET_NOT_FOUND",
                        message=(
                            "Protection action target not found: "
                            f"{configuration.action_target_type}:{configuration.action_target_id}"
                        ),
                        details={
                            "element_id": configuration.element_id,
                            "target_type": configuration.action_target_type,
                            "target_id": configuration.action_target_id,
                        },
                    )

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
            action_target_type=configuration.action_target_type,
            action_target_id=configuration.action_target_id,
            action_type=configuration.action_type,
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
            action_target_type=configuration.action_target_type,
            action_target_id=configuration.action_target_id,
            action_type=configuration.action_type,
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

    def create_measurement_binding(
        self,
        *,
        binding: ProtectionMeasurementBinding,
        transaction: Transaction,
    ) -> ApplicationResult[ProtectionMeasurementBinding]:
        """Persist one element/input-scoped source binding transactionally."""
        self._require_transaction(transaction)
        if not isinstance(binding, ProtectionMeasurementBinding):
            raise TypeError("binding must be ProtectionMeasurementBinding.")
        active = self._require_configuration()
        element = active.get(binding.protection_element_id)
        if element.input_channel_ids.get(binding.relay_input_id) != binding.channel_id:
            raise DomainError(
                code="PROTECTION_MEASUREMENT_BINDING_INPUT_MISMATCH",
                message="Measurement binding does not match the configured element input channel.",
                details={
                    "element_id": binding.protection_element_id,
                    "input_name": binding.relay_input_id,
                    "channel_id": binding.channel_id,
                },
            )
        channels = self._measurement_channel_provider() if self._measurement_channel_provider is not None else {}
        channel = channels.get(binding.channel_id)
        if channel is None:
            raise ResourceError(
                code="PROTECTION_CHANNEL_NOT_FOUND",
                message=f"Measurement channel not found: {binding.channel_id}",
                details={"channel_id": binding.channel_id},
            )
        network = self._network_provider() if self._network_provider is not None else None
        if network is None:
            raise RuntimeError("No active Network is available for protection measurement binding.")
        try:
            source_equipment = network.get_by_identity(binding.source_equipment_id)
            instrument = network.get_by_identity(binding.instrument_id)
        except KeyError as exc:
            raise ResourceError(
                code="PROTECTION_MEASUREMENT_SOURCE_NOT_FOUND",
                message="Protection measurement source equipment or physical instrument is not in the active Network.",
                details={
                    "source_equipment_id": binding.source_equipment_id,
                    "instrument_id": binding.instrument_id,
                },
            ) from exc
        if source_equipment is None or instrument is None:
            raise ResourceError(
                code="PROTECTION_MEASUREMENT_SOURCE_NOT_FOUND",
                message="Protection measurement source equipment or physical instrument is not in the active Network.",
                details={
                    "source_equipment_id": binding.source_equipment_id,
                    "instrument_id": binding.instrument_id,
                },
            )
        source_reference = binding.source_endpoint_reference
        if source_reference.is_terminal:
            source_type = str(getattr(source_equipment, "TYPE", "")).strip().lower()
            if source_reference.equipment_type.value != source_type:
                raise DomainError(
                    code="PROTECTION_MEASUREMENT_TERMINAL_TYPE_MISMATCH",
                    message="Source terminal reference equipment type does not match the active source equipment.",
                    details={"source_equipment_id": binding.source_equipment_id},
                )
            source_roles = {getattr(item, "role", None) for item in getattr(source_equipment, "terminals", ())}
            if source_reference.terminal_role not in source_roles:
                raise DomainError(
                    code="PROTECTION_MEASUREMENT_TERMINAL_NOT_FOUND",
                    message="Source terminal reference is not a terminal of the active source equipment.",
                    details={
                        "source_equipment_id": binding.source_equipment_id,
                        "terminal_role": source_reference.terminal_role,
                    },
                )
        elif source_reference.is_bus:
            if not isinstance(source_equipment, Bus):
                raise DomainError(
                    code="PROTECTION_MEASUREMENT_BUS_SOURCE_INVALID",
                    message="A Bus attachment measurement source must identify an authoritative Core Bus.",
                    details={"source_equipment_id": binding.source_equipment_id},
                )
            if source_reference.attachment_id not in {
                f"attachment-{index}" for index in range(9)
            }:
                raise DomainError(
                    code="PROTECTION_MEASUREMENT_BUS_ATTACHMENT_INVALID",
                    message="Bus measurement source must use a canonical Bus attachment slot.",
                    details={
                        "bus_id": source_equipment.id,
                        "attachment_id": source_reference.attachment_id,
                    },
                )
        instrument_type = str(getattr(instrument, "TYPE", "")).strip().upper()
        measurement_type = binding.measurement_type.strip().lower()
        if measurement_type == "current":
            if not source_reference.is_terminal:
                raise DomainError(
                    code="PROTECTION_CURRENT_SOURCE_ENDPOINT_INVALID",
                    message="CT branch-current binding must reference an explicit Branch terminal, not a Bus attachment.",
                    details={"source_equipment_id": binding.source_equipment_id},
                )
            if not isinstance(source_equipment, Branch):
                raise DomainError(
                    code="PROTECTION_CURRENT_SOURCE_NOT_BRANCH",
                    message="Short-circuit feeder-current binding must identify an explicit two-terminal network Branch.",
                    details={"source_equipment_id": binding.source_equipment_id},
                )
            side = binding.electrical_side.strip().lower()
            expected_terminal_role = {"from": "FROM", "to": "TO"}.get(side)
            if expected_terminal_role is None or source_reference.terminal_role != expected_terminal_role:
                raise DomainError(
                    code="PROTECTION_CURRENT_BRANCH_SIDE_MISMATCH",
                    message="Current measurement electrical_side must explicitly match the selected Branch FROM/TO terminal.",
                    details={
                        "branch_id": binding.source_equipment_id,
                        "electrical_side": binding.electrical_side,
                        "terminal_role": source_reference.terminal_role,
                    },
                )
            if not isinstance(instrument, CurrentTransformer):
                raise DomainError(
                    code="PROTECTION_CURRENT_INSTRUMENT_INVALID",
                    message="Current measurement binding requires an authoritative CurrentTransformer.",
                    details={"instrument_id": binding.instrument_id},
                )
            resolver = ConnectivityResolver(network)
            try:
                branch_component = set(
                    resolver.terminal_component(source_reference)
                )
                primary_references = {
                    role: EndpointReference.terminal(
                        equipment_type=EquipmentType("ct"),
                        equipment_id=instrument.id,
                        terminal_role=role,
                    )
                    for role in ("P1", "P2")
                }
                primary_components = {
                    role: set(resolver.terminal_component(reference))
                    for role, reference in primary_references.items()
                }
            except (TypeError, ValueError, KeyError) as exc:
                raise DomainError(
                    code="PROTECTION_CT_PRIMARY_TOPOLOGY_INVALID",
                    message="The selected Branch terminal and CT primary terminals must resolve through canonical SimpleWire connectivity.",
                    details={
                        "branch_id": binding.source_equipment_id,
                        "instrument_id": binding.instrument_id,
                        "reason": str(exc),
                    },
                ) from exc
            matching_ct_roles = tuple(
                role
                for role, component in primary_components.items()
                if primary_references[role] in branch_component
            )
            if (
                len(matching_ct_roles) != 1
                or primary_components["P1"] == primary_components["P2"]
            ):
                raise DomainError(
                    code="PROTECTION_CT_BRANCH_ASSOCIATION_AMBIGUOUS",
                    message="The selected Branch terminal must share exactly one CT primary SimpleWire component; CT P1 and P2 must remain on separate components so the CT is inserted in series.",
                    details={
                        "branch_id": binding.source_equipment_id,
                        "instrument_id": binding.instrument_id,
                        "branch_terminal_role": expected_terminal_role,
                        "matching_ct_primary_roles": matching_ct_roles,
                    },
                )
            expected_types = {"CT"}
            ratio_attribute = "ratio"
        elif measurement_type == "voltage":
            expected_types = {"PT", "CVT"}
            ratio_attribute = "voltage_ratio"
            if instrument_type in expected_types:
                primary_roles = {
                    "PT": ("primary_a", "primary_b"),
                    "CVT": ("H1", "H2"),
                }[instrument_type]
                resolver = ConnectivityResolver(network)
                if source_reference.is_bus:
                    selected_topology_endpoint = TopologyEndpointReference.from_bus(source_reference)
                else:
                    selected_topology_endpoint = TopologyEndpointReference.from_terminal(source_reference)
                try:
                    selected_component = set(
                        resolver.topology_component(selected_topology_endpoint)
                    )
                    primary_components = {
                        role: set(
                            resolver.terminal_component(
                                EndpointReference.terminal(
                                    equipment_type=EquipmentType(instrument_type.lower()),
                                    equipment_id=instrument.id,
                                    terminal_role=role,
                                )
                            )
                        )
                        for role in primary_roles
                    }
                except (TypeError, ValueError, KeyError) as exc:
                    raise DomainError(
                        code="PROTECTION_VOLTAGE_PRIMARY_TOPOLOGY_INVALID",
                        message="PT/CVT primary terminals and the selected voltage source must resolve through canonical Core connectivity.",
                        details={
                            "instrument_id": binding.instrument_id,
                            "source_endpoint": str(source_reference),
                            "reason": str(exc),
                        },
                    ) from exc
                matching_primary_roles = tuple(
                    role for role, component in primary_components.items()
                    if selected_topology_endpoint in component
                )
                if (
                    len(matching_primary_roles) != 1
                    or primary_components[primary_roles[0]] == primary_components[primary_roles[1]]
                ):
                    raise DomainError(
                        code="PROTECTION_VOLTAGE_PRIMARY_ASSOCIATION_INVALID",
                        message="The selected Bus/line endpoint must connect to exactly one PT/CVT primary terminal; the two primary terminals must remain on distinct topology components.",
                        details={
                            "instrument_id": binding.instrument_id,
                            "source_endpoint": str(source_reference),
                            "matching_primary_roles": matching_primary_roles,
                        },
                    )
        else:
            raise DomainError(
                code="PROTECTION_MEASUREMENT_TYPE_UNSUPPORTED",
                message=f"Unsupported physical measurement type: {binding.measurement_type!r}",
                details={"measurement_type": binding.measurement_type},
            )
        if instrument_type not in expected_types:
            raise DomainError(
                code="PROTECTION_MEASUREMENT_INSTRUMENT_TYPE_MISMATCH",
                message="Physical instrument type does not match the measurement quantity.",
                details={
                    "instrument_id": binding.instrument_id,
                    "instrument_type": instrument_type,
                    "measurement_type": measurement_type,
                },
            )
        try:
            actual_ratio = float(getattr(instrument, ratio_attribute))
        except (AttributeError, TypeError, ValueError) as exc:
            raise DomainError(
                code="PROTECTION_MEASUREMENT_RATIO_UNAVAILABLE",
                message="Physical instrument does not expose the required authoritative ratio.",
                details={"instrument_id": binding.instrument_id, "ratio_attribute": ratio_attribute},
            ) from exc
        if not isfinite(actual_ratio) or abs(actual_ratio - binding.instrument_ratio) > max(1e-9, actual_ratio * 1e-9):
            raise DomainError(
                code="PROTECTION_MEASUREMENT_RATIO_MISMATCH",
                message="Persisted instrument ratio does not match the authoritative physical instrument ratio.",
                details={
                    "instrument_id": binding.instrument_id,
                    "configured_ratio": binding.instrument_ratio,
                    "physical_ratio": actual_ratio,
                },
            )
        secondary_terminal = getattr(channel, "source_terminal", None)
        secondary_roles = {
            "CT": {"S1", "S2"},
            "PT": {"secondary_a", "secondary_b"},
            "CVT": {"X1", "X2"},
        }[instrument_type]
        if (
            secondary_terminal is None
            or not getattr(secondary_terminal, "is_terminal", False)
            or secondary_terminal.equipment_id != binding.instrument_id
            or secondary_terminal.terminal_role not in secondary_roles
            or secondary_terminal.terminal_role not in {
                getattr(item, "role", None) for item in getattr(instrument, "terminals", ())
            }
        ):
            raise DomainError(
                code="PROTECTION_MEASUREMENT_SECONDARY_TERMINAL_MISMATCH",
                message="MeasurementChannel must reference a secondary terminal belonging to the configured physical instrument.",
                details={
                    "channel_id": binding.channel_id,
                    "instrument_id": binding.instrument_id,
                    "secondary_terminal": str(secondary_terminal) if secondary_terminal is not None else None,
                },
            )
        channel_signal = str(getattr(getattr(channel, "signal_type", None), "value", "")).strip().lower()
        if channel_signal != measurement_type:
            raise DomainError(
                code="PROTECTION_MEASUREMENT_CHANNEL_TYPE_MISMATCH",
                message="MeasurementChannel signal type does not match the declared physical measurement type.",
                details={
                    "channel_id": binding.channel_id,
                    "channel_signal_type": channel_signal,
                    "measurement_type": measurement_type,
                },
            )
        relay = network.get_by_id("relay", element.relay_id)
        relay_input = relay.get_input(binding.relay_input_id)
        if relay_input.channel_id != binding.channel_id or relay_input.channel is not channel:
            raise DomainError(
                code="PROTECTION_MEASUREMENT_BINDING_RUNTIME_MISMATCH",
                message="Persisted measurement binding does not match the active RelayInput channel reference.",
                details={
                    "element_id": element.element_id,
                    "input_name": binding.relay_input_id,
                    "channel_id": binding.channel_id,
                },
            )
        active.add_measurement_binding(binding)
        transaction.record_undo(lambda: active.remove_measurement_binding(binding.binding_id))
        return ApplicationResult.success_result(
            value=binding,
            message=f"Protection source binding created: {binding.binding_id}",
            metadata={
                "object_type": "protection_measurement_binding",
                "object_id": binding.binding_id,
                "element_id": binding.protection_element_id,
                "input_name": binding.relay_input_id,
            },
        )

    def delete_measurement_binding(
        self,
        *,
        binding_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[ProtectionMeasurementBinding]:
        """Remove one source binding transactionally without changing channels."""
        self._require_transaction(transaction)
        if not isinstance(binding_id, str) or not binding_id.strip():
            raise ValueError("binding_id must be a non-empty string.")
        active = self._require_configuration()
        binding = active.remove_measurement_binding(binding_id.strip())
        transaction.record_undo(lambda: active.add_measurement_binding(binding))
        return ApplicationResult.success_result(
            value=binding,
            message=f"Protection source binding removed: {binding.binding_id}",
            metadata={
                "object_type": "protection_measurement_binding",
                "object_id": binding.binding_id,
                "element_id": binding.protection_element_id,
                "input_name": binding.relay_input_id,
            },
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
