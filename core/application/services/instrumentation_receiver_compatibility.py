"""Fail-closed compatibility checks for canonical instrumentation signals.

This module validates declared signal metadata against the existing Control
and Protection input contracts. It does not invent a receiver capability,
convert units, resolve live samples, or create duplicate signal definitions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model.instrument_wiring import SignalDefinition, SignalKind
from core.measurement.measurement_channel import MeasurementPhase, MeasurementSignalType


@dataclass(frozen=True, slots=True)
class ReceiverCompatibility:
    compatible: bool
    receiver_kind: str
    receiver_id: str
    input_id: str
    diagnostics: tuple[str, ...] = ()


_SIGNAL_TYPE_MAP = {
    SignalKind.CURRENT: MeasurementSignalType.CURRENT,
    SignalKind.VOLTAGE: MeasurementSignalType.VOLTAGE,
    SignalKind.DIGITAL: MeasurementSignalType.DIGITAL,
}


def _normalized(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip()


def _check_common(signal: SignalDefinition, accepted_types: tuple[str, ...], accepted_phases: tuple[str, ...], accepted_units: tuple[str, ...]) -> tuple[str, ...]:
    diagnostics: list[str] = []
    # Empty receiver metadata is not an unrestricted contract. Legacy or
    # partially configured destinations must remain unresolved until their
    # engineering input capabilities are explicitly declared.
    if not accepted_types:
        diagnostics.append("Receiver has no declared accepted signal types; compatibility is unresolved.")
    if not accepted_phases:
        diagnostics.append("Receiver has no declared accepted phases; compatibility is unresolved.")
    if not accepted_units:
        diagnostics.append("Receiver has no declared accepted engineering units; compatibility is unresolved.")
    mapped = _SIGNAL_TYPE_MAP.get(signal.kind)
    if mapped is None:
        diagnostics.append(
            f"Signal kind {signal.kind.value!r} has no authoritative MeasurementSignalType mapping; receiver compatibility is unresolved."
        )
    else:
        accepted = {item.casefold() for item in accepted_types}
        if accepted and mapped.value.casefold() not in accepted:
            diagnostics.append(
                f"Signal type {mapped.value!r} is not accepted; receiver declares {sorted(accepted_types)!r}."
            )

    if accepted_phases:
        if signal.phase is None:
            diagnostics.append("Signal phase is not declared but the receiver requires an explicit phase/sequence.")
        elif signal.phase.upper() not in {item.upper() for item in accepted_phases}:
            diagnostics.append(
                f"Signal phase {signal.phase!r} is not accepted; receiver declares {sorted(accepted_phases)!r}."
            )

    if accepted_units:
        if signal.unit is None:
            diagnostics.append("Signal unit is not declared but the receiver requires an explicit engineering unit.")
        elif signal.unit.casefold() not in {item.casefold() for item in accepted_units}:
            diagnostics.append(
                f"Signal unit {signal.unit!r} is not accepted; receiver declares exact units {sorted(accepted_units)!r}; conversion is not inferred."
            )
    return tuple(diagnostics)


def validate_control_receiver(
    signal: SignalDefinition,
    destination: Any,
) -> ReceiverCompatibility:
    """Validate against an existing ControlSignalDestination contract."""
    from core.application.control_signal_mapping import ControlSignalDestination

    if not isinstance(signal, SignalDefinition):
        raise TypeError("signal must be a SignalDefinition.")
    if not isinstance(destination, ControlSignalDestination):
        raise TypeError("destination must be a ControlSignalDestination.")
    diagnostics = _check_common(
        signal,
        destination.expected_signal_types,
        destination.expected_phases,
        destination.accepted_units,
    )
    return ReceiverCompatibility(
        compatible=not diagnostics,
        receiver_kind="CONTROL",
        receiver_id=destination.component_id,
        input_id=destination.input_name,
        diagnostics=diagnostics,
    )


def validate_protection_receiver(
    signal: SignalDefinition,
    *,
    function_code: str,
    input_name: str,
    element_id: str,
) -> ReceiverCompatibility:
    """Validate against the canonical Protection function/input contract."""
    from core.protection.function_catalog import get_protection_function

    if not isinstance(signal, SignalDefinition):
        raise TypeError("signal must be a SignalDefinition.")
    for name, value in (("function_code", function_code), ("input_name", input_name), ("element_id", element_id)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string.")
    diagnostics: list[str] = []
    try:
        specification = get_protection_function(function_code.strip().upper())
    except (KeyError, TypeError, ValueError):
        specification = None
    contract = getattr(specification, "input_contract", None)
    input_contract = None if contract is None or not contract.supported else contract.inputs.get(input_name)
    if input_contract is None:
        diagnostics.append(
            f"Protection function {function_code.strip().upper()!r} has no supported canonical input contract for {input_name!r}; binding is fail-closed."
        )
    else:
        mapped = _SIGNAL_TYPE_MAP.get(signal.kind)
        if mapped is None:
            diagnostics.append(
                f"Signal kind {signal.kind.value!r} has no authoritative MeasurementSignalType mapping."
            )
        elif mapped not in input_contract.signal_types:
            diagnostics.append(
                f"Signal type {mapped.value!r} is not accepted by protection input {input_name!r}."
            )
        if signal.phase is None:
            diagnostics.append("Signal phase is not declared; protection phase compatibility cannot be established.")
        else:
            try:
                phase = MeasurementPhase(signal.phase.upper())
            except ValueError:
                phase = None
            if phase is None or phase not in input_contract.phases:
                diagnostics.append(
                    f"Signal phase {signal.phase!r} is not accepted by protection input {input_name!r}."
                )
        if input_contract.require_unit and signal.unit is None:
            diagnostics.append("Signal unit is missing; protection input requires an explicit unit.")
        elif signal.unit is not None and signal.unit not in input_contract.compatible_units:
            diagnostics.append(
                f"Signal unit {signal.unit!r} is not accepted by protection input {input_name!r}; no unit conversion is inferred."
            )
    return ReceiverCompatibility(
        compatible=not diagnostics,
        receiver_kind="PROTECTION",
        receiver_id=element_id.strip(),
        input_id=input_name.strip(),
        diagnostics=tuple(diagnostics),
    )


def validate_control_mapping_binding(
    signal: SignalDefinition,
    mapping: Any,
    destination: Any,
) -> ReceiverCompatibility:
    """Require an existing persisted Control mapping to reference this signal ID."""
    from core.application.control_signal_mapping import (
        ControlSignalBinding,
        ControlSignalDestination,
        ControlSignalMapping,
    )

    if not isinstance(mapping, ControlSignalMapping):
        raise TypeError("mapping must be a ControlSignalMapping.")
    if not isinstance(destination, ControlSignalDestination):
        raise TypeError("destination must be a ControlSignalDestination.")
    matches = tuple(
        binding for binding in mapping.bindings
        if binding.destination == destination
    )
    if len(matches) != 1:
        return ReceiverCompatibility(
            False, "CONTROL", destination.component_id, destination.input_name,
            (f"Control receiver {destination.component_id!r}/{destination.input_name!r} "
             f"must have exactly one persisted canonical mapping; found {len(matches)}.",),
        )
    binding = matches[0]
    if not isinstance(binding, ControlSignalBinding):
        raise TypeError("Control mapping contains an invalid binding.")
    if binding.source.object_id != signal.id:
        return ReceiverCompatibility(
            False, "CONTROL", destination.component_id, destination.input_name,
            (f"Persisted Control mapping source {binding.source.object_id!r} "
             f"does not identify instrumentation signal {signal.id!r}.",),
        )
    if binding.source.domain != "instrumentation" or binding.source.element_type != "signal":
        return ReceiverCompatibility(
            False, "CONTROL", destination.component_id, destination.input_name,
            ("Persisted Control mapping source is not an instrumentation signal reference.",),
        )
    return validate_control_receiver(signal, destination)


def validate_protection_configuration_binding(
    signal: SignalDefinition,
    configuration: Any,
    *,
    element_id: str,
    input_name: str,
    channel_id: str,
    channels: Any,
) -> ReceiverCompatibility:
    """Require the persisted Protection input to reference the matching canonical channel."""
    from core.protection.project_configuration import ProtectionProjectConfiguration
    from core.measurement.measurement_channel import MeasurementChannel

    if not isinstance(configuration, ProtectionProjectConfiguration):
        raise TypeError("configuration must be a ProtectionProjectConfiguration.")
    if not isinstance(channels, dict) and not hasattr(channels, "get"):
        raise TypeError("channels must be a channel-ID mapping.")
    elements = tuple(
        item for item in configuration.elements if item.element_id == element_id
    )
    if len(elements) != 1:
        return ReceiverCompatibility(
            False, "PROTECTION", element_id, input_name,
            (f"Protection element {element_id!r} must resolve uniquely; found {len(elements)}.",),
        )
    element = elements[0]
    configured_channel_id = element.input_channel_ids.get(input_name)
    if configured_channel_id != channel_id:
        return ReceiverCompatibility(
            False, "PROTECTION", element_id, input_name,
            (f"Persisted Protection input references {configured_channel_id!r}, not requested channel {channel_id!r}.",),
        )
    channel = channels.get(channel_id)
    if not isinstance(channel, MeasurementChannel):
        return ReceiverCompatibility(
            False, "PROTECTION", element_id, input_name,
            (f"Canonical MeasurementChannel {channel_id!r} is missing or invalid.",),
        )
    expected_type = _SIGNAL_TYPE_MAP.get(signal.kind)
    diagnostics: list[str] = []
    if expected_type is None or channel.signal_type is not expected_type:
        diagnostics.append(
            f"Instrumentation signal kind {signal.kind.value!r} does not match channel signal type {channel.signal_type.value!r}."
        )
    if signal.phase is None or channel.phase.value != signal.phase.upper():
        diagnostics.append(
            f"Instrumentation signal phase {signal.phase!r} does not match channel phase {channel.phase.value!r}."
        )
    if signal.unit is None or channel.unit.casefold() != signal.unit.casefold():
        diagnostics.append(
            f"Instrumentation signal unit {signal.unit!r} does not match channel unit {channel.unit!r}."
        )
    if diagnostics:
        return ReceiverCompatibility(False, "PROTECTION", element_id, input_name, tuple(diagnostics))
    return validate_protection_receiver(
        signal,
        function_code=element.function_code,
        input_name=input_name,
        element_id=element_id,
    )



__all__ = [
    "ReceiverCompatibility",
    "validate_control_receiver",
    "validate_protection_receiver",
    "validate_control_mapping_binding",
    "validate_protection_configuration_binding",
]
