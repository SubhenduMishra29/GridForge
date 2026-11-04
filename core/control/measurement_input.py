"""Immutable MeasurementChannel-to-Control input snapshot.

Control consumes detached engineering values and provenance. It never owns or
mutates the canonical MeasurementChannel or its sample lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from core.measurement.measurement_channel import (
    MeasurementChannel,
    MeasurementPhase,
    MeasurementQuality,
    MeasurementSignalType,
    MeasurementValidity,
)


@dataclass(frozen=True, slots=True)
class ControlInput:
    """Detached measurement value and the metadata needed to assess usability."""

    source_id: str
    value: float | complex
    unit: str
    timestamp: float | None
    quality: MeasurementQuality
    available: bool
    signal_type: MeasurementSignalType | None = None
    phase: MeasurementPhase = MeasurementPhase.NONE
    timestamp_domain: str | None = None
    sample_sequence: int | None = None
    stale_after: float | None = None
    producer_id: str | None = None
    validity: MeasurementValidity | None = None

    def __post_init__(self) -> None:
        source_id = str(self.source_id).strip()
        if not source_id:
            raise ValueError("ControlInput source_id cannot be empty.")
        object.__setattr__(self, "source_id", source_id)
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float, complex)):
            raise TypeError("ControlInput value must be a real or complex numeric value, not bool.")
        if isinstance(self.value, complex):
            finite = math.isfinite(self.value.real) and math.isfinite(self.value.imag)
        else:
            finite = math.isfinite(self.value)
        if not finite:
            raise ValueError("ControlInput value must be finite.")
        if self.timestamp is not None and (
            isinstance(self.timestamp, bool)
            or not isinstance(self.timestamp, (int, float))
            or not math.isfinite(self.timestamp)
        ):
            raise ValueError("ControlInput timestamp must be a finite numeric value.")
        if not isinstance(self.quality, MeasurementQuality):
            raise TypeError("ControlInput quality must be MeasurementQuality.")
        if not isinstance(self.available, bool):
            raise TypeError("ControlInput available must be bool.")
        if self.signal_type is not None and not isinstance(self.signal_type, MeasurementSignalType):
            raise TypeError("ControlInput signal_type must be MeasurementSignalType or None.")
        if not isinstance(self.phase, MeasurementPhase):
            raise TypeError("ControlInput phase must be MeasurementPhase.")
        if self.timestamp_domain is not None:
            domain = str(self.timestamp_domain).strip()
            if not domain or domain != self.timestamp_domain:
                raise ValueError("ControlInput timestamp_domain must be canonical.")
        if self.sample_sequence is not None and (
            isinstance(self.sample_sequence, bool)
            or not isinstance(self.sample_sequence, int)
            or self.sample_sequence < 0
        ):
            raise ValueError("ControlInput sample_sequence must be a non-negative integer.")
        if self.stale_after is not None and (
            isinstance(self.stale_after, bool)
            or not isinstance(self.stale_after, (int, float))
            or not math.isfinite(self.stale_after)
            or self.stale_after < 0
        ):
            raise ValueError("ControlInput stale_after must be finite and non-negative.")
        if self.producer_id is not None and not str(self.producer_id).strip():
            raise ValueError("ControlInput producer_id cannot be empty.")
        if self.validity is not None and not isinstance(self.validity, MeasurementValidity):
            raise TypeError("ControlInput validity must be MeasurementValidity or None.")

    @property
    def is_usable(self) -> bool:
        """Basic usability only; freshness requires an authoritative cycle time."""
        return (
            self.available
            and self.quality is MeasurementQuality.GOOD
            and self.validity in (None, MeasurementValidity.VALID)
        )

    def is_usable_at(
        self,
        current_time: float,
        *,
        timestamp_domain: str | None = None,
        require_freshness: bool = False,
    ) -> bool:
        """Return fail-closed usability against the active cycle time/domain."""
        if not self.is_usable:
            return False
        if isinstance(current_time, bool) or not isinstance(current_time, (int, float)) or not math.isfinite(current_time):
            raise ValueError("current_time must be finite.")
        if require_freshness:
            if (
                not isinstance(timestamp_domain, str)
                or not timestamp_domain.strip()
                or self.timestamp_domain != timestamp_domain
            ):
                return False
            if self.timestamp is None:
                return False
            if (
                isinstance(self.sample_sequence, bool)
                or not isinstance(self.sample_sequence, int)
                or self.sample_sequence < 0
            ):
                return False
            if (
                isinstance(self.stale_after, bool)
                or not isinstance(self.stale_after, (int, float))
                or not math.isfinite(self.stale_after)
                or self.stale_after < 0
            ):
                return False
        elif timestamp_domain is not None and self.timestamp_domain != timestamp_domain:
            return False
        if self.timestamp is None:
            return not require_freshness and self.stale_after is None
        age = float(current_time) - float(self.timestamp)
        if age < 0:
            return False
        if self.stale_after is not None and age > self.stale_after:
            return False
        return True

    @classmethod
    def from_measurement(
        cls,
        channel: MeasurementChannel,
        *,
        require_usable: bool = False,
        current_time: float | None = None,
        timestamp_domain: str | None = None,
        require_freshness: bool = False,
    ) -> "ControlInput":
        """Create a detached snapshot from the canonical measurement channel."""
        if not isinstance(channel, MeasurementChannel):
            raise TypeError("channel must be a MeasurementChannel.")
        validity = channel.validity(current_time=current_time)
        result = cls(
            source_id=channel.id,
            value=channel.engineering_value,
            unit=channel.unit,
            timestamp=channel.timestamp,
            quality=channel.quality,
            available=channel.available,
            signal_type=channel.signal_type,
            phase=channel.phase,
            timestamp_domain=channel.timestamp_domain,
            sample_sequence=channel.sample_sequence,
            stale_after=channel.stale_after,
            producer_id=getattr(channel, "producer_id", None),
            validity=validity,
        )
        usable = (
            result.is_usable_at(
                current_time,
                timestamp_domain=timestamp_domain,
                require_freshness=require_freshness,
            )
            if current_time is not None
            else result.is_usable and not require_freshness and result.stale_after is None
        )
        if require_usable and not usable:
            raise ValueError(f"Measurement '{channel.id}' is not usable for Control ({validity.value}).")
        return result
