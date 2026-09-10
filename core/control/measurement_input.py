"""Measurement-to-Control input boundary."""

from __future__ import annotations

from dataclasses import dataclass
import math

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementQuality,
)


@dataclass(frozen=True, slots=True)
class ControlInput:
    """Immutable value-transfer contract from MeasurementChannel to Control.

    Control receives the resolved engineering value and signal-quality
    metadata. It never receives ownership of the measurement source object.
    """

    source_id: str
    value: float | complex
    unit: str
    timestamp: float | None
    quality: MeasurementQuality
    available: bool

    def __post_init__(self) -> None:
        source_id = str(self.source_id).strip()
        if not source_id:
            raise ValueError("ControlInput source_id cannot be empty.")
        object.__setattr__(self, "source_id", source_id)

        if isinstance(self.value, bool):
            raise TypeError("ControlInput value cannot be bool.")
        if isinstance(self.value, complex):
            if not math.isfinite(self.value.real) or not math.isfinite(self.value.imag):
                raise ValueError("ControlInput value must be finite.")
        elif not math.isfinite(float(self.value)):
            raise ValueError("ControlInput value must be finite.")

        if self.timestamp is not None and not math.isfinite(float(self.timestamp)):
            raise ValueError("ControlInput timestamp must be finite.")

        if not isinstance(self.quality, MeasurementQuality):
            raise TypeError("ControlInput quality must be MeasurementQuality.")

    @property
    def is_usable(self) -> bool:
        """Return whether the measurement is available and good quality."""
        return self.available and self.quality is MeasurementQuality.GOOD

    @classmethod
    def from_measurement(
        cls,
        channel: MeasurementChannel,
        *,
        require_usable: bool = False,
    ) -> "ControlInput":
        """Create a detached Control input from a canonical measurement channel."""
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")

        result = cls(
            source_id=channel.id,
            value=channel.engineering_value,
            unit=channel.unit,
            timestamp=channel.timestamp,
            quality=channel.quality,
            available=channel.available,
        )

        if require_usable and not result.is_usable:
            raise ValueError(
                f"Measurement '{channel.id}' is not usable for Control."
            )

        return result
