"""Fail-closed contracts between configured protection inputs and measurement channels.

Contracts describe the current implementations, not inferred physical wiring.
No unit conversion is performed. Where a function's settings do not declare
enough information to validate engineering dimensions, its contract rejects
composition until that ambiguity is resolved in the settings model.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
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

    def __post_init__(self) -> None:
        if not isinstance(self.function_code, str) or not self.function_code.strip():
            raise ValueError("Protection input contract requires a function code.")
        if not isinstance(self.inputs, Mapping):
            raise TypeError("Protection input contract inputs must be a mapping.")
        if not isinstance(self.supported, bool):
            raise TypeError("Protection input contract supported flag must be boolean.")
        if not self.supported and not self.unsupported_reason.strip():
            raise ValueError("Fail-closed input contracts require an explicit reason.")
        normalized = dict(self.inputs)
        for name, contract in normalized.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(contract, ProtectionInputContract):
                raise TypeError("Protection input contracts require named ProtectionInputContract values.")
        object.__setattr__(self, "function_code", self.function_code.strip().upper())
        object.__setattr__(self, "inputs", MappingProxyType(normalized))


_CURRENT_PHASES = frozenset({
    MeasurementPhase.A, MeasurementPhase.B, MeasurementPhase.C,
    MeasurementPhase.N, MeasurementPhase.NONE,
    MeasurementPhase.AB, MeasurementPhase.BC, MeasurementPhase.CA,
    MeasurementPhase.THREE_PHASE, MeasurementPhase.POSITIVE_SEQUENCE,
    MeasurementPhase.NEGATIVE_SEQUENCE, MeasurementPhase.ZERO_SEQUENCE,
})
_VOLTAGE_PHASES = _CURRENT_PHASES
_CURRENT = frozenset({MeasurementSignalType.CURRENT})
_VOLTAGE = frozenset({MeasurementSignalType.VOLTAGE})
_SCALAR_OR_PHASOR = "numeric scalar or complex phasor (function consumes magnitude); live finiteness is checked at evaluation"
_SCALAR = "real scalar; live finiteness is checked at evaluation"
_SEQUENCE_CURRENT = ProtectionInputContract(
    "negative_sequence_current", _CURRENT,
    frozenset({MeasurementPhase.NEGATIVE_SEQUENCE}), _SCALAR_OR_PHASOR,
)
_CURRENT_INPUT = ProtectionInputContract("current", _CURRENT, _CURRENT_PHASES, _SCALAR_OR_PHASOR)
_VOLTAGE_INPUT = ProtectionInputContract("voltage", _VOLTAGE, _VOLTAGE_PHASES, _SCALAR)


# Contracts use canonical phase enums; phases are unconstrained where the implementation does not inspect them.
# Unit strings must be explicit; pickup/reach values are interpreted in the
# same engineering convention as their inputs. This layer never rescales data.
CONTRACT_50 = ProtectionFunctionInputContract("50", {"current": _CURRENT_INPUT})
CONTRACT_51 = ProtectionFunctionInputContract("51", {"current": _CURRENT_INPUT})
CONTRACT_50N = ProtectionFunctionInputContract(
    "50N", {}, supported=False,
    unsupported_reason="MeasurementSignalType has no residual-current classification; CURRENT/ZERO_SEQUENCE alone does not distinguish residual current from I0 semantics",
)
CONTRACT_51N = ProtectionFunctionInputContract(
    "51N", {}, supported=False,
    unsupported_reason="MeasurementSignalType has no residual-current classification; CURRENT/ZERO_SEQUENCE alone does not distinguish residual current from I0 semantics",
)
CONTRACT_27 = ProtectionFunctionInputContract("27", {"voltage": _VOLTAGE_INPUT})
CONTRACT_59 = ProtectionFunctionInputContract("59", {"voltage": _VOLTAGE_INPUT})
CONTRACT_46 = ProtectionFunctionInputContract("46", {"negative_sequence_current": _SEQUENCE_CURRENT})
CONTRACT_49 = ProtectionFunctionInputContract(
    "49", {}, supported=False,
    unsupported_reason="CUSTOM signal type and an arbitrary unit do not establish temperature semantics or the pickup unit",
)
CONTRACT_67 = ProtectionFunctionInputContract("67", {"current": _CURRENT_INPUT})
# Distance reach has no declared engineering unit; the catalog marks ANSI 21 fail-closed.
CONTRACT_21 = ProtectionFunctionInputContract(
    "21", {"voltage": _VOLTAGE_INPUT, "current": _CURRENT_INPUT},
    supported=False,
    unsupported_reason="distance zone reach settings do not declare an engineering unit; V/I cannot be proven comparable to configured reach",
)


def validate_protection_input_contracts(
    configuration: Any, channels: Mapping[str, Any], *, require_all_bindings: bool = True
) -> tuple[str, ...]:
    """Return all configuration/channel contract violations without executing relays."""
    from core.protection.function_catalog import get_protection_function
    diagnostics: list[str] = []
    elements = getattr(configuration, "elements", None)
    if elements is None:
        elements = (configuration,)
    for element in elements:
        if not element.enabled:
            continue
        code = str(element.function_code).strip().upper()
        prefix = f"element={element.element_id!r}, function={code!r}"
        try:
            specification = get_protection_function(code)
        except (KeyError, TypeError, ValueError):
            diagnostics.append(f"{prefix}: no canonical function specification/input contract; function is fail-closed.")
            continue
        contract = specification.input_contract
        if contract is None:
            diagnostics.append(f"{prefix}: canonical catalog has no declared input contract; function is fail-closed.")
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
                if require_all_bindings:
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
    "CONTRACT_50", "CONTRACT_51", "CONTRACT_50N", "CONTRACT_51N",
    "CONTRACT_27", "CONTRACT_59", "CONTRACT_46", "CONTRACT_49",
    "CONTRACT_67", "CONTRACT_21",
    "validate_protection_input_contracts", "validate_directional_context",
]
