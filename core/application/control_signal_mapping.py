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

    def __post_init__(self) -> None:
        frozen_inputs = {
            str(component): MappingProxyType(dict(values))
            for component, values in self.external_inputs.items()
        }
        object.__setattr__(self, "external_inputs", MappingProxyType(frozen_inputs))
        object.__setattr__(self, "bindings", tuple(self.bindings))
        object.__setattr__(self, "quality", MappingProxyType(dict(self.quality)))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))


class ControlSignalResolutionError(ValueError):
    """One or more canonical engineering signal references could not resolve."""

    def __init__(self, diagnostics: tuple[str, ...]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("; ".join(self.diagnostics))


@dataclass(frozen=True, slots=True)
class ControlSignalMapping:
    """Immutable canonical mapping owned by the Application layer."""

    bindings: tuple[ControlSignalBinding, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        normalized = tuple(sorted(self.bindings))
        if any(not isinstance(binding, ControlSignalBinding) for binding in normalized):
            raise TypeError("bindings must contain ControlSignalBinding values.")
        destinations = [binding.destination for binding in normalized]
        if len(destinations) != len(set(destinations)):
            raise ValueError("A Control destination may have only one canonical engineering source.")
        object.__setattr__(self, "bindings", normalized)

    def resolve(self, read_service: ReadService) -> ControlSignalResolution:
        """Resolve every source through Application read models, never Core objects."""
        if not isinstance(read_service, ReadService):
            raise TypeError("read_service must implement ReadService.")

        external_inputs: dict[str, dict[str, Any]] = {}
        quality: dict[ControlSignalBinding, ControlSignalQuality] = {}
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
            except Exception as exc:
                diagnostics.append(
                    f"Unable to resolve signal source {source.element_type}:{source.object_id}: {exc}"
                )
                continue

            attributes = getattr(read_model, "attributes", {})
            if source.signal not in attributes:
                diagnostics.append(
                    f"Signal '{source.signal}' is not available on "
                    f"{source.element_type}:{source.object_id}."
                )
                continue

            value = attributes[source.signal]
            signal_quality=ControlSignalQuality.VALID
            if isinstance(value, Mapping) and "value" in value:
                try: signal_quality=ControlSignalQuality(str(value.get("quality","valid")))
                except ValueError: signal_quality=ControlSignalQuality.WRONG_TYPE
                value=value.get("value")
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

        return ControlSignalResolution(external_inputs=external_inputs, bindings=self.bindings, quality=quality)


__all__ = [
    "ControlSignalQuality",
    "ControlSignalSource",
    "ControlSignalDestination",
    "ControlSignalBinding",
    "ControlSignalResolution",
    "ControlSignalResolutionError",
    "ControlSignalMapping",
]
