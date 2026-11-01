"""IEEE C37.112 inverse-time overcurrent characteristic calculations.

This module provides a pure numerical curve engine. It does not construct
relay elements, acquire measurements, schedule trips, or mutate equipment.
The 51 relay settings/factory integration is deliberately a separate step.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, expm1, isfinite, log


@dataclass(frozen=True, slots=True)
class IEEECurveDefinition:
    """IEEE C37.112 curve coefficients for t = TD * (A/(M**p - 1) + B)."""

    name: str
    a: float
    b: float
    p: float
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("IEEE curve name must be non-empty.")
        for field_name in ("a", "b", "p"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{field_name} must be numeric.")
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{field_name} must be finite and non-negative.")
        if self.a <= 0.0 or self.p <= 0.0:
            raise ValueError("IEEE curve A and p coefficients must be positive.")


IEEE_CURVES = {
    "MODERATELY_INVERSE": IEEECurveDefinition(
        "MODERATELY_INVERSE", 0.0515, 0.114, 0.02,
        "IEEE C37.112 moderately inverse",
    ),
    "VERY_INVERSE": IEEECurveDefinition(
        "VERY_INVERSE", 19.61, 0.491, 2.0,
        "IEEE C37.112 very inverse",
    ),
    "EXTREMELY_INVERSE": IEEECurveDefinition(
        "EXTREMELY_INVERSE", 28.2, 0.1217, 2.0,
        "IEEE C37.112 extremely inverse",
    ),
}


def normalize_ieee_curve(curve: str) -> str:
    """Return a canonical IEEE curve name; IEC curve names are not accepted."""
    if not isinstance(curve, str):
        raise TypeError("IEEE curve must be a string.")
    key = curve.strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "MI": "MODERATELY_INVERSE",
        "MODERATE_INVERSE": "MODERATELY_INVERSE",
        "VI": "VERY_INVERSE",
        "EI": "EXTREMELY_INVERSE",
    }
    key = aliases.get(key, key)
    if key not in IEEE_CURVES:
        raise ValueError(
            f"Unsupported IEEE curve {curve!r}; expected one of "
            "MODERATELY_INVERSE, VERY_INVERSE, EXTREMELY_INVERSE."
        )
    return key


def ieee_inverse_time(
    current: float,
    pickup: float,
    *,
    curve: str = "MODERATELY_INVERSE",
    time_dial: float = 1.0,
) -> float:
    """Return IEEE C37.112 operating time in seconds; infinity means no pickup."""
    values = (current, pickup, time_dial)
    if any(isinstance(v, bool) for v in values):
        raise TypeError("Current, pickup and time dial must be numeric, not bool.")
    try:
        current_value, pickup_value, dial_value = map(float, values)
    except (TypeError, ValueError) as exc:
        raise ValueError("Current, pickup and time dial must be numeric.") from exc
    if not all(isfinite(v) for v in (current_value, pickup_value, dial_value)):
        raise ValueError("Current, pickup and time dial must be finite.")
    if pickup_value <= 0.0 or dial_value <= 0.0:
        raise ValueError("Pickup and time dial must be positive.")

    multiple = abs(current_value) / pickup_value
    if multiple <= 1.0:
        return float("inf")

    definition = IEEE_CURVES[normalize_ieee_curve(curve)]
    # expm1(p*log(M)) avoids cancellation for M close to unity.
    denominator = expm1(definition.p * log(multiple))
    if denominator <= 0.0:
        return float("inf")
    return dial_value * (definition.a / denominator + definition.b)


def generate_ieee_tcc_points(
    pickup: float,
    *,
    curve: str = "MODERATELY_INVERSE",
    time_dial: float = 1.0,
    minimum_multiple: float = 1.01,
    maximum_multiple: float = 20.0,
    points: int = 200,
) -> list[dict[str, float]]:
    """Generate log-spaced IEEE TCC data; rendering remains outside Core."""
    numeric = (pickup, time_dial, minimum_multiple, maximum_multiple)
    if any(isinstance(v, bool) for v in numeric):
        raise TypeError("TCC parameters must be numeric, not bool.")
    try:
        pickup_value, dial_value, low, high = map(float, numeric)
    except (TypeError, ValueError) as exc:
        raise ValueError("TCC parameters must be numeric.") from exc
    if not all(isfinite(v) for v in (pickup_value, dial_value, low, high)):
        raise ValueError("TCC parameters must be finite.")
    if pickup_value <= 0.0 or dial_value <= 0.0:
        raise ValueError("Pickup and time dial must be positive.")
    if low <= 1.0 or high <= low:
        raise ValueError("Require 1 < minimum_multiple < maximum_multiple.")
    if isinstance(points, bool) or not isinstance(points, int) or points < 2:
        raise ValueError("points must be an integer >= 2.")

    canonical = normalize_ieee_curve(curve)
    log_low, log_high = log(low), log(high)
    result: list[dict[str, float]] = []
    for index in range(points):
        multiple = exp(log_low + (log_high - log_low) * index / (points - 1))
        current = pickup_value * multiple
        result.append({
            "multiple": multiple,
            "current": current,
            "time": ieee_inverse_time(
                current, pickup_value, curve=canonical, time_dial=dial_value
            ),
        })
    return result


__all__ = [
    "IEEECurveDefinition", "IEEE_CURVES", "normalize_ieee_curve",
    "ieee_inverse_time", "generate_ieee_tcc_points",
]
