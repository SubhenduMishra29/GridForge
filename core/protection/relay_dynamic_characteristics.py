"""Evidence-bound relay reset-memory and overshoot characteristics.

The module deliberately models manufacturer/test data as point-specific
read models. It does not invent a reset law, generic tolerance, or infer
behaviour outside the supplied test domain.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be numeric, not boolean.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _reference(value: str, name: str = "evidence_reference") -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    result = value.strip()
    if not result:
        raise ValueError(f"{name} must be non-empty.")
    return result


@dataclass(frozen=True, slots=True)
class RelayResetMemoryPoint:
    """Measured retained operating-memory fraction after current dropout."""

    interruption_duration_s: float
    retained_fraction: float

    def __post_init__(self) -> None:
        duration = _finite(self.interruption_duration_s, "interruption_duration_s")
        fraction = _finite(self.retained_fraction, "retained_fraction")
        if duration < 0.0 or not 0.0 <= fraction <= 1.0:
            raise ValueError("Reset-memory duration must be non-negative and retained_fraction in [0, 1].")
        object.__setattr__(self, "interruption_duration_s", duration)
        object.__setattr__(self, "retained_fraction", fraction)


@dataclass(frozen=True, slots=True)
class RelayResetMemoryCurve:
    """Manufacturer/test reset-memory curve at one exact pre-dropout current."""

    pre_dropout_current_multiple: float
    points: tuple[RelayResetMemoryPoint, ...]
    evidence_reference: str

    def __post_init__(self) -> None:
        multiple = _finite(self.pre_dropout_current_multiple, "pre_dropout_current_multiple")
        if multiple <= 1.0:
            raise ValueError("pre_dropout_current_multiple must be above pickup (M > 1).")
        points = tuple(self.points)
        if len(points) < 2 or any(not isinstance(p, RelayResetMemoryPoint) for p in points):
            raise ValueError("A reset-memory curve requires at least two typed points.")
        durations = tuple(p.interruption_duration_s for p in points)
        fractions = tuple(p.retained_fraction for p in points)
        if durations[0] != 0.0 or any(b <= a for a, b in zip(durations, durations[1:])):
            raise ValueError("Reset-memory points must start at zero and have strictly increasing durations.")
        if fractions[0] != 1.0 or any(b > a for a, b in zip(fractions, fractions[1:])):
            raise ValueError("Retained memory must start at 1.0 and never increase with interruption duration.")
        object.__setattr__(self, "pre_dropout_current_multiple", multiple)
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "evidence_reference", _reference(self.evidence_reference))

    def retained_fraction(self, interruption_duration_s: float) -> float | None:
        """Interpolate only inside the measured duration range; never extrapolate."""
        duration = _finite(interruption_duration_s, "interruption_duration_s")
        if duration < 0.0:
            raise ValueError("interruption_duration_s cannot be negative.")
        if duration > self.points[-1].interruption_duration_s:
            return None
        for left, right in zip(self.points, self.points[1:]):
            if left.interruption_duration_s <= duration <= right.interruption_duration_s:
                span = right.interruption_duration_s - left.interruption_duration_s
                ratio = (duration - left.interruption_duration_s) / span
                return left.retained_fraction + ratio * (right.retained_fraction - left.retained_fraction)
        return self.points[-1].retained_fraction

    def retained_progress(self, progress_at_dropout: float, interruption_duration_s: float) -> float | None:
        """Return retained normalized progress, or None outside measured evidence."""
        progress = _finite(progress_at_dropout, "progress_at_dropout")
        if not 0.0 <= progress <= 1.0:
            raise ValueError("progress_at_dropout must be in [0, 1].")
        fraction = self.retained_fraction(interruption_duration_s)
        return None if fraction is None else progress * fraction


@dataclass(frozen=True, slots=True)
class RelayOvershootEnvelope:
    """Measured relay overshoot-time bounds at one exact current multiple."""

    current_multiple: float
    minimum_overshoot_time_s: float
    maximum_overshoot_time_s: float
    evidence_reference: str

    def __post_init__(self) -> None:
        multiple = _finite(self.current_multiple, "current_multiple")
        minimum = _finite(self.minimum_overshoot_time_s, "minimum_overshoot_time_s")
        maximum = _finite(self.maximum_overshoot_time_s, "maximum_overshoot_time_s")
        if multiple <= 1.0 or minimum < 0.0 or maximum < minimum:
            raise ValueError("Overshoot requires M > 1 and 0 <= minimum <= maximum.")
        object.__setattr__(self, "current_multiple", multiple)
        object.__setattr__(self, "minimum_overshoot_time_s", minimum)
        object.__setattr__(self, "maximum_overshoot_time_s", maximum)
        object.__setattr__(self, "evidence_reference", _reference(self.evidence_reference))


@dataclass(frozen=True, slots=True)
class RelayDynamicEvidence:
    """Reset and overshoot evidence associated with one protection function."""

    function_id: str
    reset_memory_curves: tuple[RelayResetMemoryCurve, ...] = ()
    overshoot_envelopes: tuple[RelayOvershootEnvelope, ...] = ()

    def __post_init__(self) -> None:
        function_id = _reference(self.function_id, "function_id")
        reset_curves = tuple(self.reset_memory_curves)
        overshoot = tuple(self.overshoot_envelopes)
        if any(not isinstance(item, RelayResetMemoryCurve) for item in reset_curves):
            raise TypeError("reset_memory_curves must contain RelayResetMemoryCurve values.")
        if any(not isinstance(item, RelayOvershootEnvelope) for item in overshoot):
            raise TypeError("overshoot_envelopes must contain RelayOvershootEnvelope values.")
        reset_keys = [item.pre_dropout_current_multiple for item in reset_curves]
        overshoot_keys = [item.current_multiple for item in overshoot]
        if len(set(reset_keys)) != len(reset_keys) or len(set(overshoot_keys)) != len(overshoot_keys):
            raise ValueError("Dynamic evidence cannot contain duplicate current-multiple points.")
        object.__setattr__(self, "function_id", function_id)
        object.__setattr__(self, "reset_memory_curves", reset_curves)
        object.__setattr__(self, "overshoot_envelopes", overshoot)

    def reset_curve_at(self, current_multiple: float) -> RelayResetMemoryCurve | None:
        """Return an exact-current reset curve; no interpolation across current."""
        multiple = _finite(current_multiple, "current_multiple")
        return next((curve for curve in self.reset_memory_curves
                     if math.isclose(curve.pre_dropout_current_multiple, multiple,
                                     rel_tol=1e-9, abs_tol=1e-9)), None)

    def overshoot_at(self, current_multiple: float) -> RelayOvershootEnvelope | None:
        """Return an exact-current overshoot envelope; no extrapolation."""
        multiple = _finite(current_multiple, "current_multiple")
        return next((item for item in self.overshoot_envelopes
                     if math.isclose(item.current_multiple, multiple,
                                     rel_tol=1e-9, abs_tol=1e-9)), None)


__all__ = [
    "RelayResetMemoryPoint",
    "RelayResetMemoryCurve",
    "RelayOvershootEnvelope",
    "RelayDynamicEvidence",
]
