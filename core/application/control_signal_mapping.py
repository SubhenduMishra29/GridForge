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

    def __post_init__(self) -> None:
        for name in ("control_id", "component_id", "input_name"):
            value = str(getattr(self, name)).strip()
            if not value:
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value)


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
                },
            })
        return {"schema_version": 1, "bindings": bindings}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ControlSignalMapping":
        if not isinstance(data, Mapping):
            raise TypeError("Control signal mapping data must be a mapping.")
        version = int(data.get("schema_version", 1))
        if version != 1:
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
                ),
            ))
        return cls(bindings=tuple(bindings))

    def resolve(self, read_service: ReadService) -> ControlSignalResolution:
        """Resolve every source through Application read models, never Core objects."""
        if not isinstance(read_service, ReadService):
            raise TypeError("read_service must implement ReadService.")

        external_inputs: dict[str, dict[str, Any]] = {}
        quality: dict[ControlSignalBinding, ControlSignalQuality] = {}
        interlock_inputs: dict[str, dict[str, Any]] = {}
        diagnostics: list[str] = []

        for binding in self.bindings:
            source = binding.source
            destination = binding.destination
            if source.domain != "core":
                diagnostics.append(
                    f"Unsupported signal domain '{source.domain}' for "
                    f"{source.element_type}:{source.object_id}:{source.signal}."
                )
                continue
            try:
                read_model = read_service.element(source.element_type, source.object_id)
                attributes = getattr(read_model, "attributes", {})
                if source.signal not in attributes:
                    diagnostics.append(
                        f"Signal '{source.signal}' is not available on "
                        f"{source.element_type}:{source.object_id}."
                    )
                    continue
                value = attributes[source.signal]
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
                try:
                    signal_quality = ControlSignalQuality(str(raw_quality))
                except (ValueError, TypeError):
                    signal_quality = ControlSignalQuality.WRONG_TYPE
                # Keep the complete source envelope for freshness-sensitive gates.
                interlock_inputs.setdefault(destination.control_id, {})[destination.input_name] = dict(envelope)
                value = envelope.get("value")
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
