"""Detached preparation boundary for offline protection studies."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from core.measurement.measurement_channel import MeasurementChannel


@dataclass(frozen=True, slots=True)
class PreparedMeasurementValue:
    """Immutable measurement value detached from its live channel."""

    channel_id: str
    engineering_value: float | complex
    unit: str
    available: bool
    quality: str
    timestamp: float | None


@dataclass(frozen=True, slots=True)
class PreparedProtectionInput:
    """Detached protection-function input for one evaluation."""

    relay_id: str
    element_id: str
    function_code: str
    measurements: Mapping[str, PreparedMeasurementValue]
    settings: Mapping[str, Any]
    in_service: bool
    enabled: bool
    blocked: bool

    def __post_init__(self) -> None:
        for name in ("relay_id", "element_id", "function_code"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        object.__setattr__(self, "measurements", MappingProxyType(dict(self.measurements)))
        object.__setattr__(self, "settings", MappingProxyType(dict(self.settings)))


class ProtectionPreparation:
    """Prepare a detached offline protection input without mutating Core state."""

    def prepare(
        self,
        relay: Any,
        channels: Mapping[str, MeasurementChannel],
        *,
        element_id: str,
        function_code: str | None = None,
    ) -> PreparedProtectionInput:
        if relay is None or not isinstance(getattr(relay, "id", None), str):
            raise TypeError("relay must expose a string id.")
        if not isinstance(channels, Mapping):
            raise TypeError("channels must be a mapping of protection input names to MeasurementChannel.")
        if not isinstance(element_id, str) or not element_id.strip():
            raise ValueError("element_id must be a non-empty string.")

        normalized_measurements: dict[str, PreparedMeasurementValue] = {}
        for name, channel in channels.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("measurement input names must be non-empty strings.")
            if not isinstance(channel, MeasurementChannel):
                raise TypeError("protection preparation requires MeasurementChannel inputs.")
            normalized_measurements[name.strip()] = PreparedMeasurementValue(
                channel_id=channel.id,
                engineering_value=channel.engineering_value,
                unit=channel.unit,
                available=bool(channel.available),
                quality=getattr(channel.quality, "value", str(channel.quality)),
                timestamp=channel.timestamp,
            )

        settings = getattr(relay, "settings", {})
        if not isinstance(settings, Mapping):
            raise TypeError("relay settings must be a mapping.")

        resolved_function_code = function_code
        if resolved_function_code is None:
            resolved_function_code = getattr(relay, "function_type", None)
        if not isinstance(resolved_function_code, str) or not resolved_function_code.strip():
            raise ValueError("function_code must be declared by the relay or preparation input.")

        return PreparedProtectionInput(
            relay_id=relay.id,
            element_id=element_id,
            function_code=resolved_function_code.strip().upper(),
            measurements=normalized_measurements,
            settings=settings,
            in_service=bool(getattr(relay, "in_service", True)),
            enabled=bool(getattr(relay, "enabled", True)),
            blocked=bool(getattr(relay, "blocked", False)),
        )


__all__ = [
    "PreparedMeasurementValue",
    "PreparedProtectionInput",
    "ProtectionPreparation",
]
