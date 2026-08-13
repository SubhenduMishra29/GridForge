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

This module contains reusable protection mathematics for functions such
as:

    * 50 / 51  Overcurrent
    * 50N / 51N Earth-fault overcurrent
    * 67        Directional overcurrent
    * 27 / 59   Voltage protection
    * 81        Frequency protection
    * 21        Distance protection
    * 87        Differential protection

Architectural Boundary
----------------------
This module is deliberately independent of:

    * core.model
    * Relay
    * RelayBase
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
represent a relay or protection element themselves.

Example
-------

    Relay
      |
      +-- 50
      +-- 51
      +-- 50N
      +-- 51N
      +-- 67
      +-- 21
      +-- 87
             |
             v
      relay_functions.py

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

    Equation
    --------
                       k * TMS
        t = -----------------------------
             M^alpha - 1

        M = I / Pickup
    """

    name: str
    k: float
    alpha: float
    description: str


# =====================================================================
# IEC CURVE REGISTRY
# =====================================================================

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
# IEC CURVE ALIASES
# =====================================================================

IEC_CURVE_ALIASES: Mapping[str, str] = {
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


# =====================================================================
# VALIDATION HELPERS
# =====================================================================


def _finite_float(
    value: float,
    name: str,
) -> float:
    """
    Convert a value to float and require finiteness.

    This helper is used where infinity is not a valid configured or
    measured input.
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

    Boolean values are rejected explicitly because ``bool`` is an
    ``int`` subclass in Python.
    """

    if isinstance(value, bool):
        raise ValueError(
            f"{name} must be an integer."
        )

    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be an integer."
        ) from exc

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

    Supported aliases include:

        STANDARD_INVERSE
        NORMAL_INVERSE
        VERY_INVERSE
        EXTREMELY_INVERSE
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
        return IEC_CURVE_ALIASES[
            normalized
        ]
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
# CHARACTERISTIC NORMALIZATION
# =====================================================================


def normalize_characteristic(
    characteristic: ProtectionCharacteristic | str,
) -> ProtectionCharacteristic:
    """
    Normalize a protection characteristic.

    Parameters
    ----------
    characteristic:
        ProtectionCharacteristic instance or string.

    Returns
    -------
    ProtectionCharacteristic
        Canonical characteristic enumeration.
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
        return ProtectionCharacteristic(
            normalized
        )
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

    Examples
    --------
    M = 1.0
        margin = 0

    M = 2.0
        margin = 1
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
    Calculate IEC inverse-time operating time.

    Equation
    --------
                       k * TMS
        t = -----------------------------
             M^alpha - 1

        M = |I| / Pickup

    Returns
    -------
    float
        Operating time.

        math.inf is returned when:

            |I| <= Pickup

    Raises
    ------
    ValueError
        If pickup or TMS is invalid.

    Notes
    -----
    TMS must be strictly positive for an inverse-time characteristic.

    This function evaluates only the mathematical characteristic.
    It does not generate a protection trip or operate equipment.
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
        Configured delay when pickup is exceeded.

        math.inf otherwise.

    This is a numerical characteristic only.
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
    Evaluate an ideal instantaneous protection characteristic.

    Returns
    -------
    float
        0.0 when pickup is exceeded.

        math.inf otherwise.

    Actual relay processing time, breaker operating time, and event
    scheduling belong to higher execution layers.
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
    current:
        Measured current.

    pickup:
        Protection pickup current.

    characteristic:
        One of:

            INVERSE
            DEFINITE_TIME
            INSTANTANEOUS

    curve:
        IEC curve used for INVERSE.

    TMS:
        IEC Time Multiplier Setting.

    delay:
        Definite-time delay.

    Returns
    -------
    float
        Operating time or math.inf when the element does not operate.

    Notes
    -----
    Parameters not relevant to the selected characteristic are not
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

    Parameters
    ----------
    pickup:
        Relay pickup current.

    curve:
        IEC curve identifier or alias.

    TMS:
        IEC Time Multiplier Setting.

    multipliers:
        Iterable of current multiples.

        If omitted:

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

    TMS = _positive_float(
        TMS,
        "TMS",
    )

    canonical_curve = normalize_iec_curve(
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
# INVERSE CURVE POINT
# =====================================================================


def inverse_time_from_multiple(
    multiple: float,
    curve: str = "SI",
    TMS: float = 1.0,
) -> float:
    """
    Calculate IEC operating time directly from current multiple.

    This is useful when TCC or coordination calculations already
    operate in normalized current-multiple space.

    Returns
    -------
    float
        Operating time.

        math.inf is returned for M <= 1.
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
    Calculate the current multiple corresponding to an IEC inverse-time
    operating point.

    Solves:

                       k * TMS
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
        If operating time or TMS is invalid.
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
    Generate logarithmically distributed IEC TCC points.

    Logarithmic spacing is used because inverse-time characteristics
    normally span several decades of current.

    Parameters
    ----------
    pickup:
        Relay pickup current.

    curve:
        IEC curve identifier or alias.

    TMS:
        IEC Time Multiplier Setting.

    minimum_multiple:
        Minimum current multiple.

        Must be > 1.

    maximum_multiple:
        Maximum current multiple.

    points:
        Number of generated points.

        Must be >= 2.

    Returns
    -------
    list[dict]
        Each point contains:

            multiple
            current
            time

    Notes
    -----
    This function intentionally uses only the Python standard library.
    It performs no plotting.
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

    log_min = math.log(
        minimum_multiple
    )

    log_max = math.log(
        maximum_multiple
    )

    result: list[dict[str, float]] = []

    for index in range(points):

        fraction = (
            index
            / (points - 1)
        )

        multiple = math.exp(
            log_min
            + fraction
            * (
                log_max
                - log_min
            )
        )

        current = (
            pickup
            * multiple
        )

        time = iec_time(
            current=current,
            pickup=pickup,
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

    Positive value
        Upstream operation occurs later.

    Zero
        Simultaneous operating time.

    Negative value
        Upstream operation occurs earlier.

    Infinity handling
    ------------------
    ``math.inf`` is a valid protection-analysis value because an
    element that does not operate is represented by infinite operating
    time.

    Therefore:

        finite - inf = -inf
        inf - finite = inf
        inf - inf     = nan

    The ``inf - inf`` case is retained as ``math.nan`` because two
    non-operating elements do not have a meaningful temporal
    coordination margin.

    This function does not determine whether a margin is acceptable.
    Acceptance criteria belong to the coordination subsystem.
    """

    try:
        upstream_time = float(
            upstream_time
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "upstream_time must be numeric."
        ) from exc

    try:
        downstream_time = float(
            downstream_time
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "downstream_time must be numeric."
        ) from exc

    if math.isnan(upstream_time):
        raise ValueError(
            "upstream_time cannot be NaN."
        )

    if math.isnan(downstream_time):
        raise ValueError(
            "downstream_time cannot be NaN."
        )

    if (
        math.isinf(upstream_time)
        and math.isinf(downstream_time)
    ):
        return math.nan

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
