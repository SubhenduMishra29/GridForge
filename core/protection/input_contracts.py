"""Fail-closed contracts between configured protection inputs and measurement channels.

Contracts describe the current implementations, not inferred physical wiring.
No unit conversion is performed. Where a function's settings do not declare
enough information to validate engineering dimensions, its contract rejects
composition until that ambiguity is resolved in the settings model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.measurement.measurement_channel import MeasurementPhase, MeasurementSignalType


@dataclass(frozen=True, slots=True)
class ProtectionInputContract:
    name: str
    signal_types: frozenset[MeasurementSignalType]
    phases: frozenset[MeasurementPhase]
    representation: str
    require_unit: bool = True


@dataclass(frozen=True, slots=True)
class ProtectionFunctionInputContract:
    function_code: str
    inputs: Mapping[str, ProtectionInputContract]
    supported: bool = True
    unsupported_reason: str = ""


_CURRENT_PHASES = frozenset({
    MeasurementPhase.A, MeasurementPhase.B, MeasurementPhase.C,
    MeasurementPhase.N, MeasurementPhase.NONE,
})
_VOLTAGE_PHASES = frozenset({
    MeasurementPhase.A, MeasurementPhase.B, MeasurementPhase.C,
    MeasurementPhase.N, MeasurementPhase.AB, MeasurementPhase.BC,
    MeasurementPhase.CA, MeasurementPhase.NONE,
})
_CURRENT = frozenset({MeasurementSignalType.CURRENT})
_VOLTAGE = frozenset({MeasurementSignalType.VOLTAGE})
_SCALAR_OR_PHASOR = "finite numeric scalar or complex phasor (function consumes magnitude)"
_SCALAR = "finite real scalar"
_SEQUENCE_CURRENT = ProtectionInputContract(
    "negative_sequence_current", _CURRENT,
    frozenset({MeasurementPhase.NEGATIVE_SEQUENCE}), _SCALAR_OR_PHASOR,
)
_CURRENT_INPUT = ProtectionInputContract("current", _CURRENT, _CURRENT_PHASES, _SCALAR_OR_PHASOR)
_VOLTAGE_INPUT = ProtectionInputContract("voltage", _VOLTAGE, _VOLTAGE_PHASES, _SCALAR)
_RESIDUAL_INPUT = ProtectionInputContract(
    "residual_current", _CURRENT,
    frozenset({MeasurementPhase.ZERO_SEQUENCE}), _SCALAR_OR_PHASOR,
)
_TEMP_INPUT = ProtectionInputContract(
    "temperature", frozenset({MeasurementSignalType.CUSTOM}),
    frozenset({MeasurementPhase.NONE}), _SCALAR,
)

# Contract phase choices are deliberately narrow and use only canonical enums.
# Unit strings must be explicit; pickup/reach values are interpreted in the
# same engineering convention as their inputs. This layer never rescales data.
_CONTRACTS: dict[str, ProtectionFunctionInputContract] = {
    "50": ProtectionFunctionInputContract("50", {"current": _CURRENT_INPUT}),
    "51": ProtectionFunctionInputContract("51", {"current": _CURRENT_INPUT}),
    "50N": ProtectionFunctionInputContract("50N", {"residual_current": _RESIDUAL_INPUT}),
    "51N": ProtectionFunctionInputContract("51N", {"residual_current": _RESIDUAL_INPUT}),
    "27": ProtectionFunctionInputContract("27", {"voltage": _VOLTAGE_INPUT}),
    "59": ProtectionFunctionInputContract("59", {"voltage": _VOLTAGE_INPUT}),
    "46": ProtectionFunctionInputContract("46", {"negative_sequence_current": _SEQUENCE_CURRENT}),
    "49": ProtectionFunctionInputContract("49", {"temperature": _TEMP_INPUT}),
    "67": ProtectionFunctionInputContract("67", {"current": _CURRENT_INPUT}),
    # Distance reach settings currently carry complex values but no engineering
    # unit. A V/I quotient cannot be proven comparable to those reaches without
    # a declared reach unit; reject rather than silently assuming ohms.
    "21": ProtectionFunctionInputContract(
        "21", {"voltage": _VOLTAGE_INPUT, "current": _CURRENT_INPUT},
        supported=False,
        unsupported_reason="distance zone reach settings do not declare an engineering unit; V/I cannot be proven comparable to configured reach",
    ),
}


def validate_protection_input_contracts(
    configuration: Any, channels: Mapping[str, Any]
) -> tuple[str, ...]:
    """Return all configuration/channel contract violations without executing relays."""
    diagnostics: list[str] = []
    for element in configuration.elements:
        if not element.enabled:
            continue
        code = str(element.function_code).strip().upper()
        contract = _CONTRACTS.get(code)
        prefix = f"element={element.element_id!r}, function={code!r}"
        if contract is None:
            diagnostics.append(f"{prefix}: no declared input contract; function is fail-closed.")
            continue
        if not contract.supported:
            diagnostics.append(f"{prefix}: no defensible input contract: {contract.unsupported_reason}.")
            continue
        configured = dict(element.input_channel_ids)
        for extra in sorted(set(configured) - set(contract.inputs)):
            channel_id = configured[extra]
            diagnostics.append(
                f"{prefix}, input={extra!r}, channel={channel_id!r}: input is not declared by the function contract."
            )
        for name, requirement in contract.inputs.items():
            channel_id = configured.get(name)
            detail = f"{prefix}, input={name!r}, channel={channel_id!r}"
            if not isinstance(channel_id, str) or not channel_id:
                diagnostics.append(f"{detail}: required input binding is missing.")
                continue
            channel = channels.get(channel_id)
            if channel is None:
                diagnostics.append(f"{detail}: channel is absent from the authoritative measurement registry.")
                continue
            signal_type = getattr(channel, "signal_type", None)
            if signal_type not in requirement.signal_types:
                diagnostics.append(
                    f"{detail}: signal type {getattr(signal_type, 'value', signal_type)!r} violates contract; "
                    f"expected {[item.value for item in sorted(requirement.signal_types, key=lambda item: item.value)]}."
                )
            phase = getattr(channel, "phase", None)
            if phase not in requirement.phases:
                diagnostics.append(
                    f"{detail}: phase/sequence {getattr(phase, 'value', phase)!r} violates contract; "
                    f"expected {[item.value for item in sorted(requirement.phases, key=lambda item: item.value)]}."
                )
            unit = getattr(channel, "unit", None)
            if requirement.require_unit and (not isinstance(unit, str) or not unit.strip()):
                diagnostics.append(f"{detail}: engineering unit is missing; implicit units/conversions are forbidden.")
            value = getattr(channel, "engineering_value", None)
            if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
                diagnostics.append(
                    f"{detail}: representation violates contract; expected {requirement.representation}."
                )
            elif isinstance(value, complex):
                # Scalar-only functions explicitly convert with float() and must not
                # receive a complex representation even if its imaginary part is zero.
                if requirement.representation == _SCALAR:
                    diagnostics.append(f"{detail}: complex phasor violates scalar-only contract.")
    # ANSI 67 additionally reads both phase angles from ProtectionContext metadata.
    # Those values are live evaluation inputs, so Application validates them at
    # evaluation time rather than treating them as channel bindings.
    return tuple(diagnostics)


def validate_directional_context(metadata: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Validate ANSI 67's explicitly consumed angle metadata before any element runs."""
    if metadata is None:
        return ("function='67': ProtectionContext metadata is missing voltage_angle/current_angle.",)
    diagnostics: list[str] = []
    for key in ("voltage_angle", "current_angle"):
        value = metadata.get(key)
        if isinstance(value, bool):
            diagnostics.append(f"function='67', context={key!r}: expected a finite numeric angle in degrees.")
            continue
        try:
            import math
            finite = math.isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            finite = False
        if not finite:
            diagnostics.append(f"function='67', context={key!r}: expected a finite numeric angle in degrees.")
    return tuple(diagnostics)


__all__ = [
    "ProtectionInputContract", "ProtectionFunctionInputContract",
    "validate_protection_input_contracts", "validate_directional_context",
]
