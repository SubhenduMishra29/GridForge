```python
"""
GridForge Protection Relay Functions
====================================

File:
    core/protection/relay_functions.py

Purpose
-------
Pure numerical primitives used by GridForge V2 protection-function
plugins.

This module is intentionally independent of:

    - core.model
    - Relay
    - RelayBase
    - MeasurementChannel
    - ProtectionSystem
    - BreakerManager
    - Network topology
    - Network solvers
    - Fault studies
    - Coordination state
    - Event scheduling

It provides reusable protection mathematics for protection
functions such as:

    - overcurrent
    - directional overcurrent
    - earth-fault overcurrent
    - voltage
    - frequency
    - distance
    - differential
    - future protection functions

Architectural Principle
-----------------------
A physical relay may contain multiple protection elements.

For example:

    Relay
      |
      +-- 50  Instantaneous overcurrent
      +-- 51  IDMT overcurrent
      +-- 50N Earth-fault instantaneous
      +-- 51N Earth-fault IDMT
      +-- 67  Directional overcurrent
      +-- 21  Distance
      +-- 27  Undervoltage
      +-- 59  Overvoltage
      +-- 81  Frequency
      +-- 87  Differential

This module contains the mathematical primitives required by those
elements. It does not attempt to model the relay itself.

Design goals
------------
- deterministic numerical behaviour;
- explicit validation;
- standards-oriented curve definitions;
- reusable pickup/time primitives;
- no duplicated IEC equations;
- clear distinction between pickup and operating time;
- explicit handling of non-operating conditions;
- extensibility for future standards;
- compatibility with TCC and coordination layers;
- no protection-system state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Iterable, Mapping


# =====================================================================
# NUMERICAL CONSTANTS
# =====================================================================

_EPSILON = 1.0e-12


# =====================================================================
# PROTECTION CHARACTERISTIC TYPES
# =====================================================================


class ProtectionCharacteristic(str, Enum):
    """
    Canonical protection operating characteristics.
    """

    INVERSE = "INVERSE"
    DEFINITE_TIME = "DEFINITE_TIME"
    INSTANTANEOUS = "INSTANTANEOUS"


# =====================================================================
# IEC CURVE DEFINITIONS
# =====================================================================


@dataclass(frozen=True)
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

    Equation
    --------
                       k × TMS
        t = -----------------------------
             M^alpha - 1

        M = I / Pickup
    """

    name: str
    k: float
    alpha: float
    description: str


IEC_CURVES: Mapping[str, IECCurveDefinition] = {
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


# =====================================================================
# CURVE ALIASES
# =====================================================================


IEC_CURVE_ALIASES: Mapping[str, str] = {
    "SI": "SI",
    "STANDARD_INVERSE": "SI",
    "NORMAL_INVERSE": "SI",

    "VI": "VI",
    "VERY_INVERSE": "VI",

    "EI": "EI",
    "EXTREMELY_INVERSE": "EI",
}


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

    if not math.isfinite(result):
        raise ValueError(
            f"{name} must be finite."
        )

    return result


def _positive_float(
    value: float,
    name: str,
) -> float:
    """
    Convert a value to float and require it to be positive.
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

    if curve is None:
        raise ValueError(
            "IEC curve cannot be None."
        )

    normalized = str(
        curve
    ).strip().upper()

    try:
        return IEC_CURVE_ALIASES[
            normalized
        ]
    except KeyError:
        raise ValueError(
            f"Unsupported IEC curve '{curve}'. "
            "Supported curves: SI, VI, EI, "
            "NORMAL_INVERSE, VERY_INVERSE, "
            "EXTREMELY_INVERSE."
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

    canonical = normalize_iec_curve(
        curve
    )

    return IEC_CURVES[
        canonical
    ]


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

    definition = iec_curve_definition(
        curve
    )

    return {
        "k": definition.k,
        "alpha": definition.alpha,
    }


# =====================================================================
# CURRENT MULTIPLIER
# =====================================================================


def current_multiplier(
    current: float,
    pickup: float,
) -> float:
    """
    Calculate multiple of pickup.

        M = |I| / Pickup

    Parameters
    ----------
    current:
        Measured current.

    pickup:
        Relay pickup current.

    Returns
    -------
    float
        Current multiple M.
    """

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    current = _finite_float(
        current,
        "current",
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
    Return True when current is strictly above pickup.

    The comparison is intentionally:

        |I| > Pickup
    """

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    current = _finite_float(
        current,
        "current",
    )

    return abs(current) > pickup


def pickup_margin(
    current: float,
    pickup: float,
) -> float:
    """
    Return pickup margin as a current ratio.

        margin = |I| / Pickup - 1

    Examples
    --------
    M = 1.0
        margin = 0

    M = 2.0
        margin = 1.0
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


def iec_time(
    current: float,
    pickup: float,
    curve: str = "SI",
    TMS: float = 1.0,
) -> float:
    """
    Calculate IEC 60255 inverse-time operating time.

    Equation
    --------
                       k × TMS
        t = -----------------------------
             M^alpha - 1

        M = |I| / Pickup

    Returns
    -------
    float
        Operating time in seconds.

        math.inf is returned when:

            |I| <= Pickup

    Notes
    -----
    This function does not impose a relay trip.

    It only evaluates the mathematical characteristic.
    """

    current = _finite_float(
        current,
        "current",
    )

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    TMS = _non_negative_float(
        TMS,
        "TMS",
    )

    definition = iec_curve_definition(
        curve
    )

    M = abs(current) / pickup

    if M <= 1.0:
        return math.inf

    denominator = (
        M ** definition.alpha
        - 1.0
    )

    if denominator <= _EPSILON:
        return math.inf

    return (
        TMS
        * definition.k
        / denominator
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

    Returns
    -------
    float
        Configured delay when pickup is exceeded,
        otherwise math.inf.

    This is a numerical primitive only.
    """

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    delay = _non_negative_float(
        delay,
        "delay",
    )

    current = _finite_float(
        current,
        "current",
    )

    if abs(current) <= pickup:
        return math.inf

    return delay


# =====================================================================
# INSTANTANEOUS CHARACTERISTIC
# =====================================================================


def instantaneous_operating_time(
    current: float,
    pickup: float,
) -> float:
    """
    Evaluate an instantaneous protection characteristic.

    Returns
    -------
    float
        0.0 when pickup is exceeded,
        otherwise math.inf.

    The function represents the ideal protection characteristic.

    Actual breaker operating time, relay processing time, and event
    scheduling belong to higher layers.
    """

    if pickup_exceeded(
        current,
        pickup,
    ):
        return 0.0

    return math.inf


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

    Parameters
    ----------
    characteristic:
        INVERSE
        DEFINITE_TIME
        INSTANTANEOUS

    curve:
        IEC curve used when characteristic is INVERSE.

    TMS:
        IEC Time Multiplier Setting.

    delay:
        Definite-time delay.

    Returns
    -------
    float
        Protection operating time in seconds, or math.inf when
        the element does not operate.
    """

    if isinstance(
        characteristic,
        ProtectionCharacteristic,
    ):
        characteristic_value = characteristic
    else:
        try:
            characteristic_value = (
                ProtectionCharacteristic(
                    str(characteristic).strip().upper()
                )
            )
        except ValueError as exc:
            raise ValueError(
                f"Unsupported protection characteristic "
                f"'{characteristic}'."
            ) from exc

    if characteristic_value is ProtectionCharacteristic.INVERSE:
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

    raise ValueError(
        f"Unsupported protection characteristic "
        f"'{characteristic_value}'."
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
    Generate time-current characteristic data.

    Parameters
    ----------
    pickup:
        Relay pickup current.

    curve:
        IEC curve identifier or alias.

    TMS:
        Time Multiplier Setting.

    multipliers:
        Iterable of current multiples.

        Defaults to:

            1, 2, ..., 20

    Returns
    -------
    list[dict]
        Each point contains:

            multiple
            current
            time
    """

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    TMS = _non_negative_float(
        TMS,
        "TMS",
    )

    # Validate curve before generating points.
    normalize_iec_curve(
        curve
    )

    if multipliers is None:
        multipliers = range(
            1,
            21,
        )

    result: list[dict[str, float]] = []

    for multiplier in multipliers:

        multiplier = _positive_float(
            multiplier,
            "current multiplier",
        )

        current = (
            pickup
            * multiplier
        )

        time = iec_time(
            current=current,
            pickup=pickup,
            curve=curve,
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
# INVERSE CURVE POINT
# =====================================================================


def inverse_time_from_multiple(
    multiple: float,
    curve: str = "SI",
    TMS: float = 1.0,
) -> float:
    """
    Calculate IEC operating time directly from current multiple.

    This is useful for TCC and coordination calculations where the
    current multiple is already known.
    """

    multiple = _positive_float(
        multiple,
        "multiple",
    )

    TMS = _non_negative_float(
        TMS,
        "TMS",
    )

    definition = iec_curve_definition(
        curve
    )

    if multiple <= 1.0:
        return math.inf

    denominator = (
        multiple ** definition.alpha
        - 1.0
    )

    if denominator <= _EPSILON:
        return math.inf

    return (
        TMS
        * definition.k
        / denominator
    )


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

                       k × TMS
        t = -----------------------------
             M^alpha - 1

    for M.

    Returns
    -------
    float
        Current multiple M.

    Raises
    ------
    ValueError
        If operating time is not positive.
    """

    operating_time_seconds = _positive_float(
        operating_time_seconds,
        "operating_time_seconds",
    )

    TMS = _non_negative_float(
        TMS,
        "TMS",
    )

    if TMS == 0.0:
        raise ValueError(
            "TMS must be > 0 when solving an inverse curve."
        )

    definition = iec_curve_definition(
        curve
    )

    ratio = (
        definition.k
        * TMS
        / operating_time_seconds
    )

    return (
        ratio + 1.0
    ) ** (
        1.0 / definition.alpha
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
    Generate smoothly distributed TCC points.

    Logarithmic spacing is used because inverse-time characteristics
    span a large current range and are normally displayed on
    logarithmic axes.

    This function performs no plotting.
    """

    pickup = _positive_float(
        pickup,
        "pickup",
    )

    TMS = _non_negative_float(
        TMS,
        "TMS",
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

    try:
        points = int(points)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "points must be an integer."
        ) from exc

    if points < 2:
        raise ValueError(
            "points must be >= 2."
        )

    # Import locally so this numerical module remains lightweight.
    import numpy as np

    multipliers = np.geomspace(
        minimum_multiple,
        maximum_multiple,
        points,
    )

    result: list[dict[str, float]] = []

    for multiple in multipliers:

        multiple = float(
            multiple
        )

        current = (
            pickup
            * multiple
        )

        time = iec_time(
            current=current,
            pickup=pickup,
            curve=curve,
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

    Positive value means the upstream element operates later.

    This function does not determine whether a margin is acceptable.
    Acceptance criteria belong to the coordination layer.
    """

    upstream_time = _finite_float(
        upstream_time,
        "upstream_time",
    )

    downstream_time = _finite_float(
        downstream_time,
        "downstream_time",
    )

    return (
        upstream_time
        - downstream_time
    )


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
```
