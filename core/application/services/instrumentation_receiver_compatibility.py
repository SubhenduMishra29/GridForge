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


__all__ = [
    "ReceiverCompatibility",
    "validate_control_receiver",
    "validate_protection_receiver",
]
