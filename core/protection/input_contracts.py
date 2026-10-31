"""Fail-closed contracts between protection inputs and measurement channels.

These checks cover stable channel configuration only. Sample availability, quality,
timestamps, freshness and numeric validity belong to explicit evaluation time.
No unit conversion or physical-source inference is performed.
"""
from __future__ import annotations

# Opaque in-process marker for measurement snapshots created by Application.
APPLICATION_MEASUREMENT_SNAPSHOT_AUTHORITY = object()

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
from math import isfinite
from numbers import Real

from core.measurement.measurement_channel import MeasurementPhase, MeasurementSignalType


@dataclass(frozen=True, slots=True)
class ProtectionInputContract:
    name: str
    signal_types: frozenset[MeasurementSignalType]
    phases: frozenset[MeasurementPhase]
    representation: str
    compatible_units: frozenset[str]
    require_unit: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Protection input contract name must be non-empty.")
        if not self.signal_types or any(not isinstance(v, MeasurementSignalType) for v in self.signal_types):
            raise ValueError("Protection input contract requires explicit signal types.")
        if not self.phases or any(not isinstance(v, MeasurementPhase) for v in self.phases):
            raise ValueError("Protection input contract requires explicit phase/sequence classifications.")
        if self.representation not in {
            "real numeric scalar; sample validity checked at evaluation",
            "real numeric scalar or complex phasor; sample validity checked at evaluation",
        }:
            raise ValueError(
                f"Unsupported protection input representation policy: {self.representation!r}."
            )
        if not self.compatible_units or any(not isinstance(v, str) or not v.strip() for v in self.compatible_units):
            raise ValueError("Protection input contract requires explicit compatible engineering units.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "compatible_units", frozenset(v.strip() for v in self.compatible_units))


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
        if not self.supported and (not isinstance(self.unsupported_reason, str) or not self.unsupported_reason.strip()):
            raise ValueError("Fail-closed input contracts require an explicit reason.")
        normalized = dict(self.inputs)
        for name, contract in normalized.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(contract, ProtectionInputContract):
                raise TypeError("Protection input contracts require named ProtectionInputContract values.")
        object.__setattr__(self, "function_code", self.function_code.strip().upper())
        object.__setattr__(self, "inputs", MappingProxyType(normalized))


# Ordinary overcurrent inputs explicitly exclude sequence-classified channels.
# Sequence-specific ANSI 46 accepts negative-sequence current only.
_PHASE_CURRENT = frozenset({MeasurementPhase.A, MeasurementPhase.B, MeasurementPhase.C, MeasurementPhase.N})
_PHASE_VOLTAGE = frozenset({
    MeasurementPhase.A, MeasurementPhase.B, MeasurementPhase.C,
    MeasurementPhase.AB, MeasurementPhase.BC, MeasurementPhase.CA,
})
_CURRENT = frozenset({MeasurementSignalType.CURRENT})
_VOLTAGE = frozenset({MeasurementSignalType.VOLTAGE})
_SCALAR_OR_PHASOR = "real numeric scalar or complex phasor; sample validity checked at evaluation"
_SCALAR = "real numeric scalar; sample validity checked at evaluation"

_SEQUENCE_CURRENT = ProtectionInputContract(
    "negative_sequence_current", _CURRENT,
    frozenset({MeasurementPhase.NEGATIVE_SEQUENCE}), _SCALAR_OR_PHASOR,
    frozenset({"A"}),
)
_CURRENT_INPUT = ProtectionInputContract(
    "current", _CURRENT, _PHASE_CURRENT, _SCALAR_OR_PHASOR, frozenset({"A"}),
)
# ANSI 27/59 implementations consume voltage magnitude from a scalar or
# complex phasor, so their contracts must match the actual relay input path.
_VOLTAGE_INPUT = ProtectionInputContract(
    "voltage", _VOLTAGE, _PHASE_VOLTAGE, _SCALAR_OR_PHASOR, frozenset({"V"}),
)

# The accepted units are exact canonical units; this layer does not rescale
# kA/mA or kV/mV. Settings models must declare semantics before broader units
# can be safely accepted.
CONTRACT_50 = ProtectionFunctionInputContract("50", {"current": _CURRENT_INPUT})
CONTRACT_51 = ProtectionFunctionInputContract("51", {"current": _CURRENT_INPUT})
_RESIDUAL_CURRENT_INPUT = ProtectionInputContract(
    "residual_current",
    frozenset({MeasurementSignalType.CURRENT}),
    frozenset({MeasurementPhase.A, MeasurementPhase.B, MeasurementPhase.C, MeasurementPhase.N}),
    "real numeric scalar or complex phasor; sample validity checked at evaluation",
    frozenset({"A"}),
)
CONTRACT_50N = ProtectionFunctionInputContract("50N", {"residual_current": _RESIDUAL_CURRENT_INPUT})
CONTRACT_51N = ProtectionFunctionInputContract("51N", {"residual_current": _RESIDUAL_CURRENT_INPUT})
CONTRACT_27 = ProtectionFunctionInputContract("27", {"voltage": _VOLTAGE_INPUT})
CONTRACT_59 = ProtectionFunctionInputContract("59", {"voltage": _VOLTAGE_INPUT})
CONTRACT_46 = ProtectionFunctionInputContract("46", {"negative_sequence_current": _SEQUENCE_CURRENT})
CONTRACT_49 = ProtectionFunctionInputContract(
    "49", {}, supported=False,
    unsupported_reason="CUSTOM signal type and an arbitrary unit do not establish temperature semantics or the pickup unit",
)
CONTRACT_67 = ProtectionFunctionInputContract("67", {"voltage": _VOLTAGE_INPUT, "current": _CURRENT_INPUT})
CONTRACT_21 = ProtectionFunctionInputContract(
    "21", {"voltage": _VOLTAGE_INPUT, "current": _CURRENT_INPUT},
    supported=False,
    unsupported_reason="distance zone reach settings do not declare an engineering unit; V/I cannot be proven comparable to configured reach",
)


def validate_sample_representation(value: Any, requirement: ProtectionInputContract) -> str | None:
    """Return a rejection reason when a live value violates its declared representation."""
    if isinstance(value, bool):
        return f"Boolean value is not permitted by representation {requirement.representation!r}."
    permits_complex = requirement.representation.startswith("real numeric scalar or complex phasor")
    if isinstance(value, complex):
        if not permits_complex:
            return f"Complex value is not permitted by real-scalar representation {requirement.representation!r}."
        if not isfinite(value.real) or not isfinite(value.imag):
            return "Complex phasor has a non-finite real or imaginary component."
        return None
    if not isinstance(value, Real):
        return f"Value type {type(value).__name__!r} is not a real numeric scalar."
    try:
        if not isfinite(value):
            return "Real numeric scalar is non-finite."
    except (TypeError, ValueError, OverflowError):
        return f"Value type {type(value).__name__!r} cannot be validated as a finite real scalar."
    return None


def input_contract_for(configuration: Any, element: Any, input_name: str) -> ProtectionInputContract | None:
    """Resolve the canonical input contract for one configured element/input."""
    from core.protection.function_catalog import get_protection_function
    try:
        specification = get_protection_function(str(element.function_code).strip().upper())
    except (KeyError, TypeError, ValueError):
        return None
    contract = getattr(specification, "input_contract", None)
    if contract is None or not contract.supported:
        return None
    return contract.inputs.get(input_name)


def validate_protection_input_contracts(
    configuration: Any, channels: Mapping[str, Any], *, require_all_bindings: bool = True
) -> tuple[str, ...]:
    """Validate stable function/channel configuration, never live sample state."""
    from core.protection.function_catalog import get_protection_function

    diagnostics: list[str] = []
    elements = getattr(configuration, "elements", None)
    if elements is None:
        elements = (configuration,)
    project_id = getattr(configuration, "project_id", None)
    for element in elements:
        if not element.enabled:
            continue
        code = str(element.function_code).strip().upper()
        prefix = (
            f"project={project_id!r}, element={element.element_id!r}, "
            f"function={code!r}"
        )
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
        if code in {"50N", "51N"}:
            if getattr(element, "input_channel_ids", {}):
                diagnostics.append(f"{prefix}: ANSI 50N/51N must use only the derived residual_current input; physical input_channel_ids are forbidden.")
                continue
            residual = getattr(element, "residual_current_input", None)
            if residual is None:
                diagnostics.append(f"{prefix}: explicit residual_current_input configuration is required.")
                continue
            if residual.mode != "THREE_PHASE_SUM":
                diagnostics.append(
                    f"{prefix}: {residual.mode} is not executable from the current short-circuit terminal-current model; a dedicated neutral-conductor or multi-conductor CBCT source model is required."
                )
                continue
            expected_ids = dict(residual.phase_binding_ids or {})
            configured_bindings = {
                binding.binding_id: binding
                for binding in getattr(configuration, "measurement_bindings", ())
                if binding.protection_element_id == element.element_id
                and binding.relay_input_id == "residual_current"
            }
            if set(configured_bindings) != set(expected_ids.values()):
                diagnostics.append(
                    f"{prefix}: residual-current binding set must exactly match the persisted {residual.mode} source configuration."
                )
                continue
            source_channels = set()
            for phase, binding_id in expected_ids.items():
                binding = configured_bindings[binding_id]
                channel = channels.get(binding.channel_id)
                detail = f"{prefix}, residual_source={phase!r}, binding={binding_id!r}"
                if binding.measurement_type.strip().lower() != "current":
                    diagnostics.append(f"{detail}: residual-current source must be a current measurement.")
                if binding.phase_or_sequence.strip().upper() != phase:
                    diagnostics.append(f"{detail}: configured source phase/sequence does not match its declared residual role.")
                if channel is None:
                    diagnostics.append(f"{detail}: physical MeasurementChannel is absent from the authoritative registry.")
                    continue
                source_channels.add(binding.channel_id)
                if getattr(getattr(channel, "signal_type", None), "value", None) != "CURRENT":
                    diagnostics.append(f"{detail}: source channel must be CURRENT.")
                if getattr(getattr(channel, "phase", None), "value", None) != phase:
                    diagnostics.append(f"{detail}: source channel phase does not match its configured residual role.")
                if getattr(channel, "unit", None) != "A":
                    diagnostics.append(f"{detail}: source channel must expose amperes; implicit conversion is forbidden.")
                if getattr(channel, "source_id", None) != binding.instrument_id:
                    diagnostics.append(f"{detail}: source channel instrument identity does not match its binding.")
                if residual.mode != "THREE_PHASE_SUM":
                    if binding.metadata.get("residual_source_mode") != residual.mode:
                        diagnostics.append(f"{detail}: binding metadata must explicitly declare residual_source_mode={residual.mode!r}.")
                if binding.metadata.get("measurement_point_id") != residual.measurement_point_id:
                    diagnostics.append(f"{detail}: binding metadata must match the configured measurement_point_id.")
            if residual.mode == "THREE_PHASE_SUM" and len(source_channels) != 3:
                diagnostics.append(f"{prefix}: A/B/C residual sum requires three distinct physical MeasurementChannels.")
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
            elif requirement.require_unit and unit.strip() not in requirement.compatible_units:
                diagnostics.append(
                    f"{detail}: unit {unit!r} is incompatible; accepted canonical units are "
                    f"{sorted(requirement.compatible_units)!r}; no implicit conversion is performed."
                )
    return tuple(diagnostics)


def validate_directional_context(metadata: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Validate ANSI 67's consumed angle values and provenance before evaluation."""
    if metadata is None:
        return ("function='67': ProtectionContext metadata is missing voltage_angle/current_angle and provenance.",)
    diagnostics: list[str] = [
        "function='67', context='angle_provenance': authoritative angle derivation from configured voltage/current channel samples is not implemented; caller-supplied angle metadata cannot establish channel provenance, so directional evaluation is refused."
    ]
    provenance_key = "angle_provenance"
    provenance = metadata.get(provenance_key)
    if not isinstance(provenance, Mapping):
        diagnostics.append(
            "function='67', context='angle_provenance': explicit provenance mapping is required "
            "(source channel IDs and angle reference convention)."
        )
    else:
        for key in ("voltage_channel_id", "current_channel_id", "reference_convention"):
            value = provenance.get(key)
            if not isinstance(value, str) or not value.strip():
                diagnostics.append(
                    f"function='67', context={provenance_key}.{key}: non-empty provenance value is required."
                )
    for key in ("voltage_angle", "current_angle"):
        value = metadata.get(key)
        if isinstance(value, bool):
            diagnostics.append(f"function='67', context={key!r}: expected a finite numeric angle in degrees.")
            continue
        try:
            from math import isfinite
            finite = isfinite(float(value))
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
    "validate_sample_representation", "input_contract_for",
]
