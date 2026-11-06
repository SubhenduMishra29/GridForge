"""
GridForge V2 Protection Relay Functions
=======================================

File
----
core/protection/relay_functions.py

Purpose
-------
Provides pure numerical primitives used by GridForge V2
protection-function implementations.

This module contains reusable protection mathematics for current-based
protection characteristics such as:

    * 50 / 51   Overcurrent
    * 50N / 51N Earth-fault overcurrent
    * 67         Directional overcurrent support
    * future current-based protection functions

Architectural Boundary
----------------------
This module is deliberately independent of:

    * core.model
    * Relay
    * RelayBase
    * ProtectionElement
    * MeasurementChannel
    * RelayInput
    * ProtectionContext
    * ProtectionDecision
    * ProtectionSystem
    * BreakerManager
    * network topology
    * power-system solvers
    * simulation scheduling
    * GUI state
    * persistence

A physical Relay may host multiple protection functions. The numerical
primitives in this module are shared by those functions but do not
represent a relay, protection element, or protection decision.

Design Principles
-----------------
1. Pure numerical behaviour.
2. Deterministic results.
3. Explicit input validation.
4. No hidden protection state.
5. No equipment control.
6. No topology modification.
7. No duplicated measurement state.
8. IEC inverse-time equations are centralized.
9. Pickup and operating-time evaluation remain distinct.
10. Non-operating characteristics are represented by ``math.inf``.
11. TCC generation is numerical only; plotting belongs elsewhere.
12. Coordination primitives provide arithmetic only; coordination
    policy belongs to the coordination subsystem.
13. No unnecessary numerical-library dependency.
14. Numerically stable evaluation is preferred near pickup.

IEC Inverse-Time Equation
-------------------------

                       k * TMS
    t = -----------------------------
         M^alpha - 1

where:

    M = |I| / Pickup

Supported IEC curves:

    SI  Standard / Normal Inverse
    VI  Very Inverse
    EI  Extremely Inverse

Numerical Stability
-------------------
The denominator:

    M^alpha - 1

is evaluated using:

    expm1(alpha * log(M))

rather than directly evaluating:

    M**alpha - 1

This avoids unnecessary floating-point cancellation when M is close
to unity.

The inverse equation is evaluated using ``log1p`` for the same reason.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import (
    exp,
    expm1,
    inf,
    isfinite,
    isinf,
    isnan,
    log,
    log1p,
)
from types import MappingProxyType
from typing import Iterable, Mapping


# =====================================================================
# PROTECTION CHARACTERISTIC TYPES
# =====================================================================


class ProtectionCharacteristic(str, Enum):
    """
    Canonical current-based protection characteristics.
    """

    INVERSE = "INVERSE"
    DEFINITE_TIME = "DEFINITE_TIME"
    INSTANTANEOUS = "INSTANTANEOUS"


# =====================================================================
# IEC CURVE DEFINITIONS
# =====================================================================


@dataclass(frozen=True, slots=True)
class IECCurveDefinition:
    """
    Immutable IEC inverse-time curve definition.

    Parameters
    ----------
    name:
        Canonical curve identifier.

    k:
        IEC time coefficient.

    alpha:
        IEC exponent.

    description:
        Human-readable engineering description.
    """

    name: str
    k: float
    alpha: float
    description: str


# =====================================================================
# IEC CURVE REGISTRY
# =====================================================================


IEC_CURVES: Mapping[str, IECCurveDefinition] = MappingProxyType(
    {
        "SI": IECCurveDefinition(
            name="SI",
            k=0.14,
            alpha=0.02,
            description="IEC Standard / Normal Inverse",
        ),
        "VI": IECCurveDefinition(
            name="VI",
            k=13.5,
            alpha=1.0,
            description="IEC Very Inverse",
        ),
        "EI": IECCurveDefinition(
            name="EI",
            k=80.0,
            alpha=2.0,
            description="IEC Extremely Inverse",
        ),
    }
)


# =====================================================================
# IEC CURVE ALIASES
# =====================================================================


IEC_CURVE_ALIASES: Mapping[str, str] = MappingProxyType(
    {
        "SI": "SI",
        "STANDARD_INVERSE": "SI",
        "NORMAL_INVERSE": "SI",
        "STANDARD": "SI",
        "NORMAL": "SI",
        "VI": "VI",
        "VERY_INVERSE": "VI",
        "VERY": "VI",
        "EI": "EI",
        "EXTREMELY_INVERSE": "EI",
        "EXTREMELY": "EI",
    }
)


# =====================================================================
# VALIDATION HELPERS
# =====================================================================


def _finite_float(
    value: float,
    name: str,
) -> float:
    """
    Convert a value to float and require finiteness.
    """

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric."
        ) from exc

    if not isfinite(result):
        raise ValueError(
            f"{name} must be finite."
        )

    return result


def _positive_float(
    value: float,
    name: str,
) -> float:
    """
    Convert a value to float and require it to be strictly positive.
    """

    result = _finite_float(
        value,
        name,
    )

    if result <= 0.0:
        raise ValueError(
            f"{name} must be positive."
        )

    return result


def _non_negative_float(
    value: float,
    name: str,
) -> float:
    """
    Convert a value to float and require it to be >= 0.
    """

    result = _finite_float(
        value,
        name,
    )

    if result < 0.0:
        raise ValueError(
            f"{name} must be >= 0."
        )

    return result


def _positive_integer(
    value: int,
    name: str,
) -> int:
    """
    Convert a value to an integer and require it to be positive.

    Boolean values are rejected explicitly.
    """

    if isinstance(value, bool):
        raise TypeError(
            f"{name} must be an integer."
        )

    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be an integer."
        ) from exc

    # Prevent silent truncation such as int(2.5) -> 2.
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be an integer."
        ) from exc

    if not isfinite(numeric_value):
        raise ValueError(
            f"{name} must be an integer."
        )

    if numeric_value != result:
        raise ValueError(
            f"{name} must be an integer."
        )

    if result <= 0:
        raise ValueError(
            f"{name} must be positive."
        )

    return result


# =====================================================================
# CURVE NORMALIZATION
# =====================================================================


def normalize_iec_curve(
    curve: str,
) -> str:
    """
    Normalize an IEC curve name to its canonical identifier.

    Supported canonical curves:

        SI
        VI
        EI
    """

    if not isinstance(curve, str):
        raise TypeError(
            "IEC curve must be a string."
        )

    normalized = curve.strip().upper()

    if not normalized:
        raise ValueError(
            "IEC curve cannot be empty."
        )

    try:
        return IEC_CURVE_ALIASES[normalized]
    except KeyError:
        raise ValueError(
            f"Unsupported IEC curve '{curve}'. "
            "Supported curves: SI, VI, EI, "
            "STANDARD_INVERSE, NORMAL_INVERSE, "
            "VERY_INVERSE, EXTREMELY_INVERSE."
        ) from None


# =====================================================================
# CURVE INFORMATION
# =====================================================================


def iec_curve_definition(
    curve: str,
) -> IECCurveDefinition:
    """
    Return the immutable definition of an IEC curve.
    """

    canonical = normalize_iec_curve(curve)

    return IEC_CURVES[canonical]


def iec_curve_constants(
    curve: str,
) -> dict[str, float]:
    """
    Return IEC curve constants.

    Returns
    -------
    dict
        Contains:

            k
            alpha
    """

    definition = iec_curve_definition(curve)

    return {
        "k": definition.k,
        "alpha": definition.alpha,
    }


# =====================================================================
# CHARACTERISTIC NORMALIZATION
# =====================================================================


def normalize_characteristic(
    characteristic: ProtectionCharacteristic | str,
) -> ProtectionCharacteristic:
    """
    Normalize a protection characteristic.
    """

    if isinstance(
        characteristic,
        ProtectionCharacteristic,
    ):
        return characteristic

    if not isinstance(
        characteristic,
        str,
    ):
        raise TypeError(
            "Protection characteristic must be a "
            "ProtectionCharacteristic or string."
        )

    normalized = characteristic.strip().upper()

    if not normalized:
        raise ValueError(
            "Protection characteristic cannot be empty."
        )

    try:
        return ProtectionCharacteristic(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported protection characteristic "
            f"'{characteristic}'. Supported characteristics: "
            "INVERSE, DEFINITE_TIME, INSTANTANEOUS."
        ) from exc


# =====================================================================
# CURRENT MULTIPLIER
# =====================================================================


def current_multiplier(
    current: float,
    pickup: float,
) -> float:
    """
    Calculate the multiple of pickup.

        M = |I| / Pickup
    """

    current = _finite_float(
        current,
        "current",
    )

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    return abs(current) / pickup


# =====================================================================
# PICKUP EVALUATION
# =====================================================================


def pickup_exceeded(
    current: float,
    pickup: float,
) -> bool:
    """
    Return True when the absolute current is strictly above pickup.

        |I| > Pickup

    Equality is intentionally treated as non-pickup.
    """

    current = _finite_float(
        current,
        "current",
    )

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    return abs(current) > pickup


def pickup_margin(
    current: float,
    pickup: float,
) -> float:
    """
    Return pickup margin as a current ratio.

        margin = |I| / Pickup - 1
    """

    return (
        current_multiplier(
            current,
            pickup,
        )
        - 1.0
    )


def iec_pickup(
    current: float,
    pickup: float,
) -> bool:
    """
    IEC-specific alias for pickup_exceeded().
    """

    return pickup_exceeded(
        current,
        pickup,
    )


# =====================================================================
# IEC OPERATING TIME
# =====================================================================


def inverse_time_from_multiple(
    multiple: float,
    curve: str = "SI",
    TMS: float = 1.0,
) -> float:
    """
    Calculate IEC operating time directly from current multiple.

    Equation
    --------
                       k * TMS
        t = -----------------------------
             M^alpha - 1

    Returns
    -------
    float
        Operating time in seconds.

        math.inf is returned for M <= 1.

    Notes
    -----
    The denominator is evaluated as:

        expm1(alpha * log(M))

    rather than:

        M**alpha - 1

    to improve numerical stability close to pickup.
    """

    multiple = _positive_float(
        multiple,
        "multiple",
    )

    TMS = _positive_float(
        TMS,
        "TMS",
    )

    definition = iec_curve_definition(
        curve
    )

    if multiple <= 1.0:
        return inf

    denominator = expm1(
        definition.alpha * log(multiple)
    )

    # For M > 1 and valid IEC alpha, denominator must be positive.
    # A non-positive result indicates a numerical/definition failure.
    if denominator <= 0.0:
        return inf

    return (
        TMS
        * definition.k
        / denominator
    )


def iec_time(
    current: float,
    pickup: float,
    curve: str = "SI",
    TMS: float = 1.0,
) -> float:
    """
    Calculate IEC inverse-time operating time.

    ``math.inf`` represents a non-operating condition.

    TMS must be strictly positive.

    Notes
    -----
    The IEC inverse-time denominator is evaluated using ``expm1`` to
    improve numerical stability near pickup.
    """

    current = _finite_float(
        current,
        "current",
    )

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    TMS = _positive_float(
        TMS,
        "TMS",
    )

    canonical_curve = normalize_iec_curve(
        curve
    )

    multiple = abs(current) / pickup

    return inverse_time_from_multiple(
        multiple=multiple,
        curve=canonical_curve,
        TMS=TMS,
    )


# =====================================================================
# DEFINITE-TIME CHARACTERISTIC
# =====================================================================


def definite_time(
    current: float,
    pickup: float,
    delay: float,
) -> float:
    """
    Evaluate a definite-time protection characteristic.

    Returns the configured delay when pickup is exceeded and
    ``math.inf`` otherwise.
    """

    current = _finite_float(
        current,
        "current",
    )

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    delay = _non_negative_float(
        delay,
        "delay",
    )

    if abs(current) <= pickup:
        return inf

    return delay


# =====================================================================
# INSTANTANEOUS CHARACTERISTIC
# =====================================================================


def instantaneous_operating_time(
    current: float,
    pickup: float,
) -> float:
    """
    Evaluate an ideal instantaneous protection characteristic.

    Returns:

        0.0
            when pickup is exceeded.

        math.inf
            otherwise.

    Relay processing time, breaker operating time, and simulation
    event scheduling belong to higher execution layers.
    """

    if pickup_exceeded(
        current,
        pickup,
    ):
        return 0.0

    return inf


# =====================================================================
# GENERIC CHARACTERISTIC EVALUATION
# =====================================================================


def operating_time(
    current: float,
    pickup: float,
    *,
    characteristic: ProtectionCharacteristic | str = (
        ProtectionCharacteristic.INVERSE
    ),
    curve: str = "SI",
    TMS: float = 1.0,
    delay: float = 0.0,
) -> float:
    """
    Evaluate a generic current-based protection characteristic.

    Supported characteristics:

        INVERSE
        DEFINITE_TIME
        INSTANTANEOUS

    Parameters irrelevant to the selected characteristic are not
    interpreted by that characteristic.
    """

    characteristic_value = normalize_characteristic(
        characteristic
    )

    if (
        characteristic_value
        is ProtectionCharacteristic.INVERSE
    ):
        return iec_time(
            current=current,
            pickup=pickup,
            curve=curve,
            TMS=TMS,
        )

    if (
        characteristic_value
        is ProtectionCharacteristic.DEFINITE_TIME
    ):
        return definite_time(
            current=current,
            pickup=pickup,
            delay=delay,
        )

    if (
        characteristic_value
        is ProtectionCharacteristic.INSTANTANEOUS
    ):
        return instantaneous_operating_time(
            current=current,
            pickup=pickup,
        )

    raise RuntimeError(
        "Unhandled ProtectionCharacteristic."
    )


# =====================================================================
# IEC CURVE GENERATION
# =====================================================================


def generate_iec_curve(
    pickup: float,
    curve: str = "SI",
    TMS: float = 1.0,
    multipliers: Iterable[float] | None = None,
) -> list[dict[str, float]]:
    """
    Generate IEC time-current characteristic data.

    If ``multipliers`` is omitted, multiples 1 through 20 are used.

    Each returned point contains:

        multiple
        current
        time

    This function generates numerical characteristic data only.
    Plotting and visualization belong to higher layers.
    """

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    TMS = _positive_float(
        TMS,
        "TMS",
    )

    canonical_curve = normalize_iec_curve(
        curve
    )

    if multipliers is None:
        multipliers = range(1, 21)

    result: list[dict[str, float]] = []

    for multiplier in multipliers:

        multiplier = _positive_float(
            multiplier,
            "current multiplier",
        )

        current = pickup * multiplier

        time = inverse_time_from_multiple(
            multiple=multiplier,
            curve=canonical_curve,
            TMS=TMS,
        )

        result.append(
            {
                "multiple": multiplier,
                "current": current,
                "time": time,
            }
        )

    return result


# =====================================================================
# INVERSE CHARACTERISTIC SOLUTION
# =====================================================================


def current_multiple_for_time(
    operating_time_seconds: float,
    curve: str = "SI",
    TMS: float = 1.0,
) -> float:
    """
    Calculate the current multiple corresponding to an IEC
    inverse-time operating point.

    Solves:

                       k * TMS
        t = -----------------------------
             M^alpha - 1

    for M.

    The inverse expression is evaluated using ``log1p`` for numerical
    stability.
    """

    operating_time_seconds = _positive_float(
        operating_time_seconds,
        "operating_time_seconds",
    )

    TMS = _positive_float(
        TMS,
        "TMS",
    )

    definition = iec_curve_definition(
        curve
    )

    ratio = (
        definition.k
        * TMS
        / operating_time_seconds
    )

    return exp(
        log1p(ratio)
        / definition.alpha
    )


# =====================================================================
# TCC POINT GENERATION
# =====================================================================


def generate_tcc_points(
    pickup: float,
    curve: str = "SI",
    TMS: float = 1.0,
    *,
    minimum_multiple: float = 1.01,
    maximum_multiple: float = 20.0,
    points: int = 200,
) -> list[dict[str, float]]:
    """
    Generate logarithmically distributed IEC TCC points.

    Each point contains:

        multiple
        current
        time

    The function produces numerical TCC data only.

    Rendering, plotting, axes, logarithmic display configuration,
    annotations, and graphical styling belong to the UI/visualization
    layer.
    """

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    TMS = _positive_float(
        TMS,
        "TMS",
    )

    canonical_curve = normalize_iec_curve(
        curve
    )

    minimum_multiple = _positive_float(
        minimum_multiple,
        "minimum_multiple",
    )

    maximum_multiple = _positive_float(
        maximum_multiple,
        "maximum_multiple",
    )

    if minimum_multiple <= 1.0:
        raise ValueError(
            "minimum_multiple must be greater than 1."
        )

    if maximum_multiple <= minimum_multiple:
        raise ValueError(
            "maximum_multiple must be greater than "
            "minimum_multiple."
        )

    points = _positive_integer(
        points,
        "points",
    )

    if points < 2:
        raise ValueError(
            "points must be >= 2."
        )

    log_min = log(
        minimum_multiple
    )

    log_max = log(
        maximum_multiple
    )

    result: list[dict[str, float]] = []

    for index in range(points):

        fraction = index / (points - 1)

        multiple = exp(
            log_min
            + fraction * (
                log_max - log_min
            )
        )

        current = pickup * multiple

        time = inverse_time_from_multiple(
            multiple=multiple,
            curve=canonical_curve,
            TMS=TMS,
        )

        result.append(
            {
                "multiple": multiple,
                "current": current,
                "time": time,
            }
        )

    return result


# =====================================================================
# COORDINATION MARGIN
# =====================================================================


def coordination_margin(
    upstream_time: float,
    downstream_time: float,
) -> float:
    """
    Calculate temporal coordination margin.

        margin = upstream_time - downstream_time

    Positive:
        upstream operation occurs later.

    Zero:
        simultaneous operating time.

    Negative:
        upstream operation occurs earlier.

    ``math.inf`` is valid because non-operating protection
    characteristics are represented by infinite operating time.

    ``inf - inf`` returns ``math.nan`` because two non-operating
    elements have no meaningful temporal separation.

    This function performs arithmetic only.

    Acceptance criteria, grading margins, CTI, primary/backup
    relationships, fault scenarios, and coordination policy belong to
    the coordination subsystem.
    """

    upstream_time = _finite_or_positive_infinity(
        upstream_time,
        "upstream_time",
    )

    downstream_time = _finite_or_positive_infinity(
        downstream_time,
        "downstream_time",
    )

    if (
        isinf(upstream_time)
        and isinf(downstream_time)
    ):
        return float("nan")

    return (
        upstream_time
        - downstream_time
    )


def _finite_or_positive_infinity(
    value: float,
    name: str,
) -> float:
    """
    Validate a protection operating time.

    Accepted values:

        finite value >= 0
        positive infinity

    Negative values and negative infinity are invalid.
    """

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric."
        ) from exc

    if isnan(result):
        raise ValueError(
            f"{name} cannot be NaN."
        )

    if result == float("-inf"):
        raise ValueError(
            f"{name} cannot be negative infinity."
        )

    if result < 0.0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    return result


# =====================================================================
# PUBLIC API
# =====================================================================


__all__ = [
    "ProtectionCharacteristic",
    "IECCurveDefinition",
    "IEC_CURVES",
    "IEC_CURVE_ALIASES",
    "normalize_iec_curve",
    "iec_curve_definition",
    "iec_curve_constants",
    "normalize_characteristic",
    "current_multiplier",
    "pickup_exceeded",
    "pickup_margin",
    "iec_pickup",
    "iec_time",
    "definite_time",
    "instantaneous_operating_time",
    "operating_time",
    "generate_iec_curve",
    "inverse_time_from_multiple",
    "current_multiple_for_time",
    "generate_tcc_points",
    "coordination_margin",
]
