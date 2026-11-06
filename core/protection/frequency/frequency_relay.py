"""ANSI 81 under/over-frequency protection with RoCoF confirmation.

RoCoF is a supervisory confirmation of an independently picked-up
under-frequency or over-frequency condition. It is never an initiating
trip criterion. Frequency samples are accepted only from the canonical
Application-validated MeasurementChannel snapshot path.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any, Mapping

from core.protection.context import ProtectionContext
from core.protection.decision import ProtectionDecision
from core.protection.relay_base import RelayBase
from core.protection.relay_input import RelayInput


FUNCTION_CODE = "81"
FUNCTION_NAME = "FREQUENCY (UNDER/OVER) WITH ROCOF CONFIRMATION"
FREQUENCY_INPUT = "frequency"


@dataclass(frozen=True, slots=True)
class FrequencyProtectionSettings:
    """Explicit ANSI 81 thresholds and acquisition/operating-time contract.

    The estimator requires an integral number of configured sample
    intervals across the estimation window. No nominal system frequency,
    pickup, sample rate, or timing tolerance is assumed by this model.
    """

    under_frequency_pickup_hz: float
    over_frequency_pickup_hz: float
    rocof_confirmation_threshold_hz_per_s: float
    sample_rate_hz: float
    estimation_window_seconds: float
    sample_interval_tolerance_seconds: float
    operating_delay_seconds: float

    def __post_init__(self) -> None:
        positive = (
            "under_frequency_pickup_hz",
            "over_frequency_pickup_hz",
            "rocof_confirmation_threshold_hz_per_s",
            "sample_rate_hz",
            "estimation_window_seconds",
        )
        non_negative = ("sample_interval_tolerance_seconds", "operating_delay_seconds")
        for name in positive + non_negative:
            raw = getattr(self, name)
            if isinstance(raw, bool):
                raise TypeError(f"{name} must be numeric, not boolean.")
            try:
                value = float(raw)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"{name} must be numeric.") from exc
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
            if name in positive and value <= 0.0:
                raise ValueError(f"{name} must be positive.")
            if name in non_negative and value < 0.0:
                raise ValueError(f"{name} cannot be negative.")
            object.__setattr__(self, name, value)
        if self.under_frequency_pickup_hz >= self.over_frequency_pickup_hz:
            raise ValueError("Under-frequency pickup must be below over-frequency pickup.")
        interval = 1.0 / self.sample_rate_hz
        if self.sample_interval_tolerance_seconds >= interval:
            raise ValueError("Sample interval tolerance must be smaller than the configured sample interval.")
        intervals = self.estimation_window_seconds * self.sample_rate_hz
        interval_count = round(intervals)
        if interval_count < 1 or not math.isclose(intervals, interval_count, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("Estimation window must contain at least one complete, integral sample interval.")


class FrequencyProtectionRelay(RelayBase):
    """ANSI 81 relay: frequency pickup, RoCoF confirmation, then delay."""

    FUNCTION_CODE = FUNCTION_CODE
    FUNCTION_NAME = FUNCTION_NAME
    FREQUENCY_INPUT = FREQUENCY_INPUT
    _RUNTIME_HISTORY = "ansi81_frequency_samples"
    _RUNTIME_CONFIRMATION = "ansi81_confirmed_pickup"

    def __init__(
        self,
        relay: Any,
        *,
        element_id: str,
        relay_inputs: Mapping[str, RelayInput] | None = None,
        settings: FrequencyProtectionSettings,
        enabled: bool = True,
        blocked: bool = False,
    ) -> None:
        if not isinstance(settings, FrequencyProtectionSettings):
            raise TypeError("settings must be FrequencyProtectionSettings.")
        super().__init__(
            relay=relay,
            element_id=element_id,
            function_code=self.FUNCTION_CODE,
            function_name=self.FUNCTION_NAME,
            relay_inputs=relay_inputs,
            settings={
                "under_frequency_pickup_hz": settings.under_frequency_pickup_hz,
                "over_frequency_pickup_hz": settings.over_frequency_pickup_hz,
                "rocof_confirmation_threshold_hz_per_s": settings.rocof_confirmation_threshold_hz_per_s,
                "sample_rate_hz": settings.sample_rate_hz,
                "estimation_window_seconds": settings.estimation_window_seconds,
                "sample_interval_tolerance_seconds": settings.sample_interval_tolerance_seconds,
                "operating_delay_seconds": settings.operating_delay_seconds,
            },
            enabled=enabled,
            blocked=blocked,
        )
        self._frequency_settings = settings
        self.require_inputs(self.FREQUENCY_INPUT)

    @property
    def frequency_settings(self) -> FrequencyProtectionSettings:
        return self._frequency_settings

    @staticmethod
    def _least_squares_rocof(samples: tuple[tuple[float, int, float], ...]) -> float:
        """Return least-squares frequency slope in Hz/s for timestamped samples."""
        if len(samples) < 2:
            raise ValueError("At least two samples are required for RoCoF estimation.")
        origin = samples[0][0]
        times = tuple(item[0] - origin for item in samples)
        values = tuple(item[2] for item in samples)
        mean_t = math.fsum(times) / len(times)
        mean_f = math.fsum(values) / len(values)
        denominator = math.fsum((value - mean_t) ** 2 for value in times)
        if not math.isfinite(denominator) or denominator <= 0.0:
            raise ValueError("RoCoF estimation timestamps do not span a valid interval.")
        numerator = math.fsum(
            (time_value - mean_t) * (frequency_value - mean_f)
            for time_value, frequency_value in zip(times, values)
        )
        result = numerator / denominator
        if not math.isfinite(result):
            raise ValueError("RoCoF estimate is non-finite.")
        return result

    def _reset_sample_state(self) -> None:
        self.runtime_remove(self._RUNTIME_HISTORY) if self.runtime_has(self._RUNTIME_HISTORY) else None
        self.runtime_remove(self._RUNTIME_CONFIRMATION) if self.runtime_has(self._RUNTIME_CONFIRMATION) else None

    def _validated_sample(self, context: ProtectionContext) -> tuple[float, int, float, str]:
        signal = self.get_input(self.FREQUENCY_INPUT)
        value = signal.value
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("Frequency sample must be a real numeric scalar.")
        frequency = float(value)
        if not math.isfinite(frequency) or frequency <= 0.0:
            raise ValueError("Frequency sample must be finite and positive.")
        if not signal.available or not signal.usable or not signal.valid:
            raise ValueError("Frequency MeasurementChannel sample is unavailable, unusable, or invalid.")
        timestamp = signal.timestamp
        if isinstance(timestamp, bool) or not isinstance(timestamp, Real):
            raise ValueError("Frequency sample timestamp is missing or non-numeric.")
        timestamp = float(timestamp)
        if not math.isfinite(timestamp) or timestamp < 0.0 or timestamp > context.time:
            raise ValueError("Frequency sample timestamp is invalid or later than evaluation time.")
        domain = signal.timestamp_domain
        expected_domain = context.metadata.get("evaluation_time_domain")
        if (
            not isinstance(domain, str) or not domain.strip()
            or not isinstance(expected_domain, str) or not expected_domain.strip()
            or domain != expected_domain
        ):
            raise ValueError("Frequency sample timestamp domain does not match the trusted Protection evaluation clock domain.")
        sequence = signal.sample_sequence
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ValueError("Frequency sample requires a non-negative integer producer sequence.")
        stale_after = signal.stale_after
        if isinstance(stale_after, bool) or not isinstance(stale_after, Real):
            raise ValueError("Frequency channel must declare a finite stale_after freshness limit.")
        stale_after = float(stale_after)
        age = context.time - timestamp
        if not math.isfinite(stale_after) or stale_after < 0.0 or age < 0.0 or age > stale_after:
            raise ValueError("Frequency sample exceeds its channel freshness limit.")
        return timestamp, sequence, frequency, domain

    def evaluate(self, context: ProtectionContext) -> ProtectionDecision:
        if not isinstance(context, ProtectionContext):
            return self.invalid_decision(reason="ANSI 81 requires a valid ProtectionContext.")
        timestamp = context.time
        if not self.operational:
            self._reset_sample_state()
            return self.no_operation(reason=self._inactive_reason(), timestamp=timestamp)

        try:
            sample = self._validated_sample(context)
            history = tuple(self.runtime_get(self._RUNTIME_HISTORY, ()))
            settings = self._frequency_settings
            interval = 1.0 / settings.sample_rate_hz
            if history:
                previous = history[-1]
                elapsed = sample[0] - previous[0]
                sequence_step = sample[1] - previous[1]
                if sequence_step != 1:
                    raise ValueError("Frequency sample sequence is duplicate, skipped, or non-monotonic.")
                if elapsed <= 0.0 or abs(elapsed - interval) > max(
                    settings.sample_interval_tolerance_seconds,
                    1e-9 * interval,
                ):
                    raise ValueError("Frequency sample interval is non-monotonic or outside the configured sample-rate tolerance.")
            elif self.runtime_has(self._RUNTIME_HISTORY):
                history = ()

            expected_samples = int(round(settings.estimation_window_seconds * settings.sample_rate_hz)) + 1
            updated = (history + (sample,))[-expected_samples:]
            self.runtime_set(self._RUNTIME_HISTORY, updated)
            rocof = None
            complete_window = len(updated) == expected_samples
            if complete_window:
                span = updated[-1][0] - updated[0][0]
                accumulated_tolerance = (
                    settings.sample_interval_tolerance_seconds * (expected_samples - 1)
                )
                if abs(span - settings.estimation_window_seconds) > max(
                    accumulated_tolerance,
                    1e-9 * settings.estimation_window_seconds,
                ):
                    raise ValueError("Frequency samples do not span the complete configured estimation window.")
                rocof = self._least_squares_rocof(updated)

        except (TypeError, ValueError, AttributeError, KeyError, OverflowError) as exc:
            self._reset_sample_state()
            return self.invalid_decision(
                reason=f"ANSI 81 rejected frequency sample/window: {exc}",
                timestamp=timestamp,
                metadata={"input": self.FREQUENCY_INPUT, "rocof_confirmation_only": True},
            )

        frequency = sample[2]
        direction = (
            "UNDER"
            if frequency <= settings.under_frequency_pickup_hz
            else "OVER"
            if frequency >= settings.over_frequency_pickup_hz
            else None
        )
        metadata = {
            "frequency_hz": frequency,
            "under_frequency_pickup_hz": settings.under_frequency_pickup_hz,
            "over_frequency_pickup_hz": settings.over_frequency_pickup_hz,
            "rocof_hz_per_s": rocof,
            "rocof_confirmation_threshold_hz_per_s": settings.rocof_confirmation_threshold_hz_per_s,
            "estimation_window_seconds": settings.estimation_window_seconds,
            "estimator": "sliding-window least-squares",
            "complete_estimation_window": complete_window,
            "pickup_direction": direction,
            "rocof_confirmation_only": True,
            "timestamp_domain": sample[3],
            "sample_sequence": sample[1],
        }
        if direction is None:
            if self.runtime_has(self._RUNTIME_CONFIRMATION):
                self.runtime_remove(self._RUNTIME_CONFIRMATION)
            return self.no_operation(
                reason="Frequency is within the ANSI 81 under/over-frequency pickup band; RoCoF cannot initiate a trip.",
                timestamp=timestamp,
                metadata=metadata,
            )

        confirmed = False
        if complete_window and rocof is not None:
            confirmed = (
                rocof <= -settings.rocof_confirmation_threshold_hz_per_s
                if direction == "UNDER"
                else rocof >= settings.rocof_confirmation_threshold_hz_per_s
            )
        if not confirmed:
            if self.runtime_has(self._RUNTIME_CONFIRMATION):
                self.runtime_remove(self._RUNTIME_CONFIRMATION)
            return self.pickup_decision(
                reason=f"ANSI 81 {direction.lower()}frequency pickup is present; matching RoCoF confirmation is not yet established.",
                timestamp=timestamp,
                metadata=metadata,
            )

        confirmed_since = self.runtime_get(self._RUNTIME_CONFIRMATION)
        if not isinstance(confirmed_since, tuple) or len(confirmed_since) != 2 or confirmed_since[0] != direction:
            confirmed_since = (direction, sample[0])
            self.runtime_set(self._RUNTIME_CONFIRMATION, confirmed_since)
        elapsed_confirmed = sample[0] - confirmed_since[1]
        metadata["confirmed_operating_elapsed_seconds"] = elapsed_confirmed
        metadata["rocof_confirmed"] = True
        if elapsed_confirmed < settings.operating_delay_seconds:
            return self.pickup_decision(
                reason=f"ANSI 81 {direction.lower()}frequency pickup is confirmed by matching RoCoF; operating delay is timing.",
                timestamp=timestamp,
                operating_time=elapsed_confirmed,
                metadata=metadata,
            )
        return self.trip_decision(
            reason=f"ANSI 81 {direction.lower()}frequency pickup was confirmed by matching RoCoF and the configured operating delay elapsed.",
            timestamp=timestamp,
            operating_time=elapsed_confirmed,
            metadata=metadata,
        )

    def _inactive_reason(self) -> str:
        if not self.enabled:
            return "ANSI 81 function is disabled."
        if self.blocked:
            return "ANSI 81 function is statically blocked."
        if not bool(getattr(self.relay, "operational", True)):
            return "Authoritative relay is not operational."
        return "ANSI 81 function is not operational."


__all__ = [
    "FUNCTION_CODE",
    "FUNCTION_NAME",
    "FREQUENCY_INPUT",
    "FrequencyProtectionSettings",
    "FrequencyProtectionRelay",
]
