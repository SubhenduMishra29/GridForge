"""Canonical Application-owned mapping from engineering signals to Control inputs.

Author: Subhendu Mishra

The Control engine consumes already-resolved external inputs. This module owns
engineering signal identity, read-model resolution, validation, deterministic
ordering, and diagnostics; LogicEngine remains equipment-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from enum import Enum
import math
from typing import Any, Mapping

from .read_service import ReadService


def _freeze_snapshot(value: Any) -> Any:
    """Recursively detach and freeze containers in a resolved signal snapshot."""
    if isinstance(value, Mapping):
        # Stable ordering makes equivalent mapping snapshots deterministic.
        items = sorted(value.items(), key=lambda item: str(item[0]))
        return MappingProxyType({key: _freeze_snapshot(item) for key, item in items})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_snapshot(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_snapshot(item) for item in value)
    return value


class ControlSignalQuality(str, Enum):
    VALID="valid"; INVALID="invalid"; STALE="stale"; UNAVAILABLE="unavailable"; WRONG_TYPE="wrong_type"; MISSING="missing"

@dataclass(frozen=True, slots=True, order=True)
class ControlSignalSource:
    """Stable source identity for an engineering signal."""

    domain: str
    element_type: str
    object_id: str
    signal: str
    expected_type: type | tuple[type, ...] | None = None

    def __post_init__(self) -> None:
        for name in ("domain", "element_type", "object_id", "signal"):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "domain", self.domain.lower())
        object.__setattr__(self, "element_type", self.element_type.lower())
        if self.expected_type is not None:
            if isinstance(self.expected_type, tuple):
                if not self.expected_type or not all(isinstance(item, type) for item in self.expected_type):
                    raise TypeError("expected_type tuple must contain type values.")
            elif not isinstance(self.expected_type, type):
                raise TypeError("expected_type must be a type, tuple of types, or None.")


@dataclass(frozen=True, slots=True, order=True)
class ControlSignalDestination:
    """Stable destination identity inside a Control graph."""

    control_id: str
    component_id: str
    input_name: str
    expected_signal_types: tuple[str, ...] = ()
    expected_phases: tuple[str, ...] = ()
    accepted_units: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("control_id", "component_id", "input_name"):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value)
        for name in ("expected_signal_types", "expected_phases", "accepted_units"):
            raw_values = getattr(self, name)
            if not isinstance(raw_values, (tuple, list)):
                raise TypeError(f"{name} must be a tuple or list of strings.")
            values = tuple(str(item).strip() for item in raw_values)
            if any(not item for item in values):
                raise ValueError(f"{name} cannot contain empty values.")
            normalized = tuple(
                item.casefold() if name == "accepted_units" else item.upper()
                for item in values
            )
            if len(normalized) != len(set(normalized)):
                raise ValueError(f"{name} cannot contain duplicates.")
            object.__setattr__(self, name, normalized)


@dataclass(frozen=True, slots=True, order=True)
class ControlSignalBinding:
    """One source-to-Control-input mapping entry."""

    source: ControlSignalSource
    destination: ControlSignalDestination


@dataclass(frozen=True, slots=True)
class ControlSignalResolution:
    """Deterministic, immutable resolved Control input snapshot plus diagnostics."""

    external_inputs: Mapping[str, Mapping[str, Any]]
    bindings: tuple[ControlSignalBinding, ...]
    quality: Mapping[ControlSignalBinding, ControlSignalQuality] = field(default_factory=dict)
    diagnostics: tuple[str, ...] = ()
    interlock_inputs: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "external_inputs", _freeze_snapshot(self.external_inputs))
        object.__setattr__(self, "bindings", tuple(self.bindings))
        object.__setattr__(self, "quality", MappingProxyType(dict(self.quality)))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "interlock_inputs", _freeze_snapshot(self.interlock_inputs))


class ControlSignalResolutionError(ValueError):
    """One or more canonical engineering signal references could not resolve."""

    def __init__(self, diagnostics: tuple[str, ...]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("; ".join(self.diagnostics))


def _type_key(expected_type: type | tuple[type, ...] | None) -> tuple[str, ...]:
    if expected_type is None:
        return ()
    types = expected_type if isinstance(expected_type, tuple) else (expected_type,)
    return tuple(item.__name__ for item in types)


def _type_from_name(name: str) -> type:
    supported = {"bool": bool, "float": float, "int": int, "str": str}
    try:
        return supported[str(name)]
    except KeyError as exc:
        raise ValueError(f"Unsupported persisted Control signal type {name!r}.") from exc


@dataclass(frozen=True, slots=True)
class ControlSignalMapping:
    """Immutable canonical mapping owned by the Application layer."""

    bindings: tuple[ControlSignalBinding, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        values = tuple(self.bindings)
        if any(not isinstance(binding, ControlSignalBinding) for binding in values):
            raise TypeError("bindings must contain ControlSignalBinding values.")
        normalized = tuple(sorted(
            values,
            key=lambda binding: (
                binding.source.domain,
                binding.source.element_type,
                binding.source.object_id,
                binding.source.signal,
                _type_key(binding.source.expected_type),
                binding.destination.control_id,
                binding.destination.component_id,
                binding.destination.input_name,
            ),
        ))
        destinations = [
            (binding.destination.component_id, binding.destination.input_name)
            for binding in normalized
        ]
        if len(destinations) != len(set(destinations)):
            raise ValueError("A Control component input may have only one canonical engineering source.")
        object.__setattr__(self, "bindings", normalized)

    def to_dict(self) -> dict[str, Any]:
        """Return configuration-only JSON-compatible data; no live values are persisted."""
        bindings = []
        for binding in self.bindings:
            expected = binding.source.expected_type
            if isinstance(expected, tuple):
                expected_types: str | list[str] | None = list(_type_key(expected))
            elif expected is None:
                expected_types = None
            else:
                expected_types = expected.__name__
            if expected is not None:
                names = expected_types if isinstance(expected_types, list) else [expected_types]
                unsupported = [name for name in names if name not in {"bool", "float", "int", "str"}]
                if unsupported:
                    raise ValueError(f"Unsupported persisted Control signal type(s): {', '.join(unsupported)}.")
            bindings.append({
                "source": {
                    "domain": binding.source.domain,
                    "element_type": binding.source.element_type,
                    "object_id": binding.source.object_id,
                    "signal": binding.source.signal,
                    "expected_type": expected_types,
                },
                "destination": {
                    "control_id": binding.destination.control_id,
                    "component_id": binding.destination.component_id,
                    "input_name": binding.destination.input_name,
                    "expected_signal_types": list(binding.destination.expected_signal_types),
                    "expected_phases": list(binding.destination.expected_phases),
                    "accepted_units": list(binding.destination.accepted_units),
                },
            })
        return {"schema_version": 2, "bindings": bindings}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ControlSignalMapping":
        if not isinstance(data, Mapping):
            raise TypeError("Control signal mapping data must be a mapping.")
        version = int(data.get("schema_version", 1))
        if version not in {1, 2}:
            raise ValueError(f"Unsupported Control signal mapping schema version {version}.")
        records = data.get("bindings", ())
        if not isinstance(records, (list, tuple)):
            raise TypeError("Control signal mapping bindings must be a sequence.")
        bindings: list[ControlSignalBinding] = []
        for record in records:
            if not isinstance(record, Mapping):
                raise TypeError("Each Control signal binding must be a mapping.")
            source_data = record.get("source")
            destination_data = record.get("destination")
            if not isinstance(source_data, Mapping) or not isinstance(destination_data, Mapping):
                raise TypeError("Control signal binding requires source and destination mappings.")
            for field_name in ("expected_signal_types", "expected_phases", "accepted_units"):
                raw_contract = destination_data.get(field_name, ())
                if not isinstance(raw_contract, (list, tuple)):
                    raise TypeError(f"destination.{field_name} must be a list or tuple.")
            raw_expected = source_data.get("expected_type")
            if raw_expected is None:
                expected_type = None
            elif isinstance(raw_expected, str):
                expected_type = _type_from_name(raw_expected)
            elif isinstance(raw_expected, (list, tuple)) and raw_expected:
                expected_type = tuple(_type_from_name(item) for item in raw_expected)
            else:
                raise TypeError("expected_type must be a supported type name or non-empty sequence of names.")
            bindings.append(ControlSignalBinding(
                source=ControlSignalSource(
                    domain=str(source_data["domain"]),
                    element_type=str(source_data["element_type"]),
                    object_id=str(source_data["object_id"]),
                    signal=str(source_data["signal"]),
                    expected_type=expected_type,
                ),
                destination=ControlSignalDestination(
                    control_id=str(destination_data["control_id"]),
                    component_id=str(destination_data["component_id"]),
                    input_name=str(destination_data["input_name"]),
                    expected_signal_types=tuple(destination_data.get("expected_signal_types", ())),
                    expected_phases=tuple(destination_data.get("expected_phases", ())),
                    accepted_units=tuple(destination_data.get("accepted_units", ())),
                ),
            ))
        return cls(bindings=tuple(bindings))

    def resolve(self, read_service: ReadService, *, measurement_read_service: Any | None = None, current_time: float | None = None, timestamp_domain: str | None = None) -> ControlSignalResolution:
        """Resolve every source through Application read models, never Core objects."""
        if not isinstance(read_service, ReadService):
            raise TypeError("read_service must implement ReadService.")
        if current_time is not None and (
            isinstance(current_time, bool)
            or not isinstance(current_time, (int, float))
            or not math.isfinite(current_time)
        ):
            raise ValueError("current_time must be a finite numeric simulation time.")
        if timestamp_domain is not None and (
            not isinstance(timestamp_domain, str)
            or not timestamp_domain.strip()
            or timestamp_domain != timestamp_domain.strip()
        ):
            raise ValueError("timestamp_domain must be a canonical non-empty string when provided.")

        external_inputs: dict[str, dict[str, Any]] = {}
        quality: dict[ControlSignalBinding, ControlSignalQuality] = {}
        interlock_inputs: dict[str, dict[str, Any]] = {}
        diagnostics: list[str] = []

        for binding in self.bindings:
            source = binding.source
            destination = binding.destination
            try:
                if source.domain == "measurement":
                    if measurement_read_service is None or not callable(getattr(measurement_read_service, "channel", None)):
                        raise RuntimeError("MeasurementChannelReadService is required for measurement-domain bindings.")
                    channel = measurement_read_service.channel(source.object_id)
                    if source.signal not in {"value", "engineering_value", channel.signal_type.lower()}:
                        raise KeyError(
                            f"MeasurementChannel signal '{source.signal}' is not compatible with "
                            f"channel type '{channel.signal_type}'."
                        )
                    value = {
                        "value": channel.value,
                        "unit": channel.unit,
                        "signal_type": channel.signal_type,
                        "phase": channel.phase,
                        "quality": channel.quality,
                        "available": channel.available,
                        "timestamp": channel.timestamp,
                        "timestamp_domain": channel.timestamp_domain,
                        "sample_sequence": channel.sample_sequence,
                        "stale_after": channel.stale_after,
                        "producer_id": channel.producer_id,
                        "validity": channel.validity,
                    }
                elif source.domain == "core":
                    read_model = read_service.element(source.element_type, source.object_id)
                    attributes = getattr(read_model, "attributes", {})
                    if source.signal not in attributes:
                        diagnostics.append(
                            f"Signal '{source.signal}' is not available on "
                            f"{source.element_type}:{source.object_id}."
                        )
                        continue
                    value = attributes[source.signal]
                else:
                    raise ValueError(f"Unsupported signal domain '{source.domain}'.")
            except Exception as exc:
                # Read-model lookup, attribute access, membership checks, and
                # value retrieval are all part of the resolution boundary.
                # Convert failures into source-specific diagnostics so callers
                # receive an actionable resolution error and no partial inputs
                # can reach Control evaluation or command dispatch.
                diagnostics.append(
                    f"Unable to read signal '{source.signal}' from "
                    f"{source.element_type}:{source.object_id}: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue
            envelope = value if isinstance(value, Mapping) and "value" in value else None
            signal_quality = ControlSignalQuality.VALID
            if envelope is not None:
                raw_quality = envelope.get("quality", "missing")
                if isinstance(raw_quality, Enum):
                    raw_quality = raw_quality.value
                quality_key = str(raw_quality).strip().lower()
                quality_aliases = {
                    "good": ControlSignalQuality.VALID,
                    "valid": ControlSignalQuality.VALID,
                    "invalid": ControlSignalQuality.INVALID,
                    "suspect": ControlSignalQuality.INVALID,
                    "unknown": ControlSignalQuality.INVALID,
                    "stale": ControlSignalQuality.STALE,
                    "unavailable": ControlSignalQuality.UNAVAILABLE,
                    "wrong_type": ControlSignalQuality.WRONG_TYPE,
                    "missing": ControlSignalQuality.MISSING,
                }
                signal_quality = quality_aliases.get(
                    quality_key,
                    ControlSignalQuality.WRONG_TYPE,
                )
                raw_validity = envelope.get("validity")
                if isinstance(raw_validity, Enum):
                    raw_validity = raw_validity.value
                if raw_validity is not None and str(raw_validity).strip().upper() != "VALID":
                    validity_key = str(raw_validity).strip().lower()
                    signal_quality = (
                        ControlSignalQuality.UNAVAILABLE
                        if validity_key == "unavailable"
                        else ControlSignalQuality.STALE
                        if validity_key == "stale"
                        else ControlSignalQuality.INVALID
                    )

            if envelope is not None and source.domain == "measurement":
                raw_type = envelope.get("signal_type")
                raw_phase = envelope.get("phase")
                actual_type = raw_type.value if isinstance(raw_type, Enum) else str(raw_type or "")
                actual_phase = raw_phase.value if isinstance(raw_phase, Enum) else str(raw_phase or "")
                if destination.expected_signal_types and actual_type.upper() not in destination.expected_signal_types:
                    diagnostics.append(
                        f"Measurement signal '{source.object_id}' has signal type '{actual_type}', "
                        f"expected one of {destination.expected_signal_types}."
                    )
                    signal_quality = ControlSignalQuality.WRONG_TYPE
                if destination.expected_phases and actual_phase.upper() not in destination.expected_phases:
                    diagnostics.append(
                        f"Measurement signal '{source.object_id}' has phase/basis '{actual_phase}', "
                        f"expected one of {destination.expected_phases}."
                    )
                    signal_quality = ControlSignalQuality.WRONG_TYPE
                actual_unit = str(envelope.get("unit", "")).casefold()
                if destination.accepted_units and actual_unit not in destination.accepted_units:
                    diagnostics.append(
                        f"Measurement signal '{source.object_id}' has unit '{envelope.get('unit', '')}', "
                        f"accepted units are {destination.accepted_units}; no implicit conversion is performed."
                    )
                    signal_quality = ControlSignalQuality.WRONG_TYPE

                # Validate canonical MeasurementChannel snapshots against the
                # active cycle time. A connected graph edge is not availability.
                channel_fields = {"signal_type", "phase", "timestamp_domain", "sample_sequence", "stale_after", "available"}
                is_channel_envelope = bool(channel_fields.intersection(envelope))
                if is_channel_envelope:
                    timestamp = envelope.get("timestamp")
                    domain = envelope.get("timestamp_domain")
                    if envelope.get("available") is not True:
                        signal_quality = ControlSignalQuality.UNAVAILABLE
                    if current_time is None or timestamp is None:
                        diagnostics.append(f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} requires a cycle time and sample timestamp.")
                        signal_quality = ControlSignalQuality.STALE
                    elif isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp):
                        diagnostics.append(f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} has a non-finite timestamp.")
                        signal_quality = ControlSignalQuality.STALE
                    elif timestamp > current_time:
                        diagnostics.append(f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} is future-dated.")
                        signal_quality = ControlSignalQuality.STALE
                    stale_after = envelope.get("stale_after")
                    if stale_after is None:
                        diagnostics.append(
                            f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} "
                            "has no configured freshness ceiling."
                        )
                        signal_quality = ControlSignalQuality.STALE
                    elif (
                        isinstance(stale_after, bool)
                        or not isinstance(stale_after, (int, float))
                        or not math.isfinite(stale_after)
                        or stale_after < 0
                    ):
                        diagnostics.append(f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} has an invalid stale-after policy.")
                        signal_quality = ControlSignalQuality.STALE
                    elif current_time is not None and timestamp is not None and current_time - timestamp > stale_after:
                        diagnostics.append(f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} is stale.")
                        signal_quality = ControlSignalQuality.STALE
                    if (
                        not isinstance(domain, str)
                        or not domain.strip()
                        or timestamp_domain is None
                        or domain != timestamp_domain
                    ):
                        diagnostics.append(f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} has an absent or mismatched timestamp domain.")
                        signal_quality = ControlSignalQuality.STALE
                    sequence = envelope.get("sample_sequence")
                    if sequence is None:
                        diagnostics.append(
                            f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} "
                            "has no publication sequence."
                        )
                        signal_quality = ControlSignalQuality.INVALID
                    elif isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
                        diagnostics.append(f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} has an invalid sample sequence.")
                        signal_quality = ControlSignalQuality.INVALID

                # Keep the detached source envelope for freshness-sensitive gates.
                interlock_envelope = dict(envelope)
                # The resolver has already normalized and validated the source
                # quality. Preserve the source marker separately for diagnostics.
                interlock_envelope["source_quality"] = interlock_envelope.get("quality")
                interlock_envelope["quality"] = signal_quality.value
                interlock_inputs.setdefault(destination.control_id, {})[destination.input_name] = interlock_envelope
                value = envelope.get("value")
                raw_signal_type = envelope.get("signal_type") if envelope is not None else None
                if isinstance(raw_signal_type, Enum):
                    raw_signal_type = raw_signal_type.value
                digital_boolean = str(raw_signal_type).strip().upper() == "DIGITAL" and isinstance(value, bool)
                if is_channel_envelope and not digital_boolean:
                    if isinstance(value, bool) or not isinstance(value, (int, float, complex)):
                        diagnostics.append(
                            f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} "
                            f"has non-numeric engineering value type {type(value).__name__}."
                        )
                        signal_quality = ControlSignalQuality.WRONG_TYPE
                    elif not (
                        math.isfinite(value.real) and math.isfinite(value.imag)
                        if isinstance(value, complex)
                        else math.isfinite(value)
                    ):
                        diagnostics.append(
                            f"Measurement signal '{source.signal}' on {source.element_type}:{source.object_id} "
                            "has a non-finite engineering value."
                        )
                        signal_quality = ControlSignalQuality.INVALID
            # Plain values intentionally do not enter interlock_inputs:
            # no quality or timestamp metadata may be manufactured. A required
            # interlock input will therefore fail closed as missing.
            quality[binding]=signal_quality
            if signal_quality is not ControlSignalQuality.VALID:
                diagnostics.append(f"Signal '{source.signal}' on {source.element_type}:{source.object_id} has quality {signal_quality.value}.")
                continue
            if source.expected_type is not None and not isinstance(value, source.expected_type):
                expected = source.expected_type
                expected_name = (
                    ", ".join(item.__name__ for item in expected)
                    if isinstance(expected, tuple)
                    else expected.__name__
                )
                diagnostics.append(
                    f"Signal '{source.signal}' on {source.element_type}:{source.object_id} "
                    f"has type {type(value).__name__}; expected {expected_name}."
                )
                continue

            external_inputs.setdefault(destination.component_id, {})[destination.input_name] = value

        if diagnostics:
            raise ControlSignalResolutionError(tuple(diagnostics))

        return ControlSignalResolution(external_inputs=external_inputs, bindings=self.bindings, quality=quality, interlock_inputs=interlock_inputs)


__all__ = [
    "ControlSignalQuality",
    "ControlSignalSource",
    "ControlSignalDestination",
    "ControlSignalBinding",
    "ControlSignalResolution",
    "ControlSignalResolutionError",
    "ControlSignalMapping",
]
