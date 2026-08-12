"""
GridForge Protection Numerical Functions
========================================

File:
    core/protection/relay_functions.py

Purpose
-------
Pure, stateless numerical utilities used by GridForge protection
functions and coordination tools.

This module is deliberately independent of:

    - core.model
    - Relay
    - RelayBase
    - ProtectionSystem
    - Breaker
    - BreakerManager
    - Network
    - topology
    - Y-bus
    - load-flow
    - short-circuit studies
    - simulation scheduling
    - protection-system state

It contains reusable protection mathematics only.

Architecture
------------

    Measurement / RelayInput
              |
              v
      Protection Function
              |
              +--------------------+
              |                    |
              v                    v
       Numerical Functions   Algorithm State
              |
              v
       ProtectionDecision


IMPORTANT V2 BOUNDARY
---------------------

This module calculates quantities.

It does NOT decide what a particular protection relay should do.

For example:

    iec_time(...)
        -> calculates an IEC operating time

    impedance(...)
        -> calculates apparent impedance

    directional_characteristic(...)
        -> calculates a directional characteristic quantity

The calling protection function remains responsible for interpreting
those quantities and producing a protection decision.

FUTURE-READY DESIGN
-------------------

GridForge supports relays containing multiple protection functions.

Examples include:

    Overcurrent
    Directional Overcurrent
    Distance
    Earth Fault
    Sensitive Earth Fault
    Negative Sequence
    Zero Sequence
    Differential
    Under/Over Voltage
    Under/Over Frequency
    Rate of Change of Frequency
    Thermal
    Power
    Reverse Power
    Loss of Mains
    Out-of-Step
    Breaker Failure
    Auto-Reclose
    Synchrocheck

This module therefore provides reusable mathematical primitives
without coupling those functions together.

IEC CURVES
----------

Supported IEC 60255 inverse-time curves:

    SI  - Standard / Normal Inverse
    VI  - Very Inverse
    EI  - Extremely Inverse

Equation:

                 k × TMS
    t = -------------------------
         M^alpha - 1

where:

    M = I / Pickup

Curve constants:

    SI:
        k     = 0.14
        alpha = 0.02

    VI:
        k     = 13.5
        alpha = 1.0

    EI:
        k     = 80.0
        alpha = 2.0


NUMERICAL CONVENTIONS
---------------------

Unless explicitly stated otherwise:

- currents and voltages may be real or complex;
- magnitude-based protection calculations use abs(...);
- denominators approaching zero are handled explicitly;
- invalid physical inputs raise ValueError;
- functions do not silently manufacture measurements;
- no mutable global runtime state is maintained.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, Mapping


# =====================================================================
# IEC CURVE DEFINITIONS
# =====================================================================

IEC_CURVES: Dict[str, Dict[str, float]] = {
    "SI": {
        "k": 0.14,
        "alpha": 0.02,
    },
    "VI": {
        "k": 13.5,
        "alpha": 1.0,
    },
    "EI": {
        "k": 80.0,
        "alpha": 2.0,
    },
}


IEC_CURVE_ALIASES: Dict[str, str] = {
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
    "EXTREME": "EI",
}


# =====================================================================
# NUMERICAL CONSTANTS
# =====================================================================

DEFAULT_EPSILON = 1.0e-12
DEFAULT_CURRENT_EPSILON = 1.0e-9
DEFAULT_IMPEDANCE_EPSILON = 1.0e-12


# =====================================================================
# VALIDATION UTILITIES
# =====================================================================

def finite_real(
    value: float,
    *,
    name: str = "value",
) -> float:
    """
    Convert a value to a finite real float.

    Raises
    ------
    ValueError
        If the value cannot be represented as a finite real number.
    """

    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(value):
        raise ValueError(
            f"{name} must be finite."
        )

    return value


def positive_real(
    value: float,
    *,
    name: str = "value",
) -> float:
    """
    Convert a value to a strictly positive finite float.
    """

    value = finite_real(
        value,
        name=name,
    )

    if value <= 0.0:
        raise ValueError(
            f"{name} must be positive."
        )

    return value


def nonnegative_real(
    value: float,
    *,
    name: str = "value",
) -> float:
    """
    Convert a value to a finite float >= 0.
    """

    value = finite_real(
        value,
        name=name,
    )

    if value < 0.0:
        raise ValueError(
            f"{name} must be >= 0."
        )

    return value


# =====================================================================
# CURVE NORMALIZATION
# =====================================================================

def normalize_iec_curve(
    curve: str,
) -> str:
    """
    Normalize an IEC inverse-time curve identifier.

    Returns
    -------
    str
        Canonical identifier:

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
            "Supported curves include SI, VI, EI, "
            "NORMAL_INVERSE, VERY_INVERSE, and "
            "EXTREMELY_INVERSE."
        ) from None


# =====================================================================
# IEC CURVE CONSTANTS
# =====================================================================

def iec_curve_constants(
    curve: str,
) -> Mapping[str, float]:
    """
    Return the immutable IEC characteristic constants.

    Returns
    -------
    Mapping[str, float]
        Contains:

            k
            alpha
    """

    canonical = normalize_iec_curve(
        curve
    )

    constants = IEC_CURVES[
        canonical
    ]

    return {
        "k": constants["k"],
        "alpha": constants["alpha"],
    }


# =====================================================================
# PICKUP MULTIPLE
# =====================================================================

def current_multiplier(
    current: complex | float,
    pickup: float,
) -> float:
    """
    Calculate current multiple:

        M = |I| / Pickup
    """

    pickup = positive_real(
        pickup,
        name="pickup",
    )

    magnitude = abs(current)

    if not math.isfinite(
        magnitude
    ):
        raise ValueError(
            "Current magnitude must be finite."
        )

    return magnitude / pickup


# =====================================================================
# IEC PICKUP
# =====================================================================

def iec_pickup(
    current: complex | float,
    pickup: float,
) -> bool:
    """
    Determine whether current is strictly above pickup.

    The criterion is:

        |I| > Pickup
    """

    pickup = positive_real(
        pickup,
        name="pickup",
    )

    magnitude = abs(current)

    if not math.isfinite(
        magnitude
    ):
        raise ValueError(
            "Current magnitude must be finite."
        )

    return magnitude > pickup


# =====================================================================
# IEC OPERATING TIME
# =====================================================================

def iec_time(
    current: complex | float,
    pickup: float,
    curve: str = "SI",
    TMS: float = 1.0,
) -> float:
    """
    Calculate IEC inverse-time operating time.

    Equation:

                 k × TMS
        t = -------------------
             M^alpha - 1

        M = |I| / Pickup

    Returns
    -------
    float
        Operating time in seconds.

        math.inf is returned when:

            |I| <= Pickup
    """

    pickup = positive_real(
        pickup,
        name="pickup",
    )

    tms = nonnegative_real(
        TMS,
        name="TMS",
    )

    magnitude = abs(current)

    if not math.isfinite(
        magnitude
    ):
        raise ValueError(
            "Current magnitude must be finite."
        )

    canonical = normalize_iec_curve(
        curve
    )

    constants = IEC_CURVES[
        canonical
    ]

    k = constants["k"]
    alpha = constants["alpha"]

    M = magnitude / pickup

    if M <= 1.0:
        return math.inf

    denominator = (
        M ** alpha
        - 1.0
    )

    if denominator <= DEFAULT_EPSILON:
        return math.inf

    return (
        tms
        * k
        / denominator
    )


# =====================================================================
# IEC CURVE DATA
# =====================================================================

def generate_iec_curve(
    pickup: float,
    curve: str = "SI",
    TMS: float = 1.0,
    multipliers: Iterable[float] | None = None,
) -> list[dict[str, float]]:
    """
    Generate time-current characteristic points.

    Returns records of:

        {
            "multiple": M,
            "current": I,
            "time": t,
        }
    """

    pickup = positive_real(
        pickup,
        name="pickup",
    )

    if multipliers is None:
        multipliers = range(
            1,
            21,
        )

    points: list[
        dict[str, float]
    ] = []

    for multiplier in multipliers:

        multiplier = positive_real(
            multiplier,
            name="current multiplier",
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

        points.append(
            {
                "multiple": multiplier,
                "current": current,
                "time": time,
            }
        )

    return points


# =====================================================================
# PHASOR MAGNITUDE
# =====================================================================

def magnitude(
    value: complex | float,
) -> float:
    """
    Return the magnitude of a real or complex quantity.
    """

    result = abs(value)

    if not math.isfinite(
        result
    ):
        raise ValueError(
            "Quantity magnitude must be finite."
        )

    return float(result)


# =====================================================================
# PHASOR ANGLE
# =====================================================================

def angle(
    value: complex | float,
) -> float:
    """
    Return the phase angle in radians.

    For zero magnitude, the angle is defined as zero.

    This convention avoids manufacturing an undefined numerical
    angle for zero-valued phasors.
    """

    value = complex(value)

    if not (
        math.isfinite(value.real)
        and math.isfinite(value.imag)
    ):
        raise ValueError(
            "Phasor must be finite."
        )

    if abs(value) <= DEFAULT_EPSILON:
        return 0.0

    return math.atan2(
        value.imag,
        value.real,
    )


# =====================================================================
# PHASOR POLAR CONVERSION
# =====================================================================

def polar_phasor(
    magnitude_value: float,
    angle_radians: float,
) -> complex:
    """
    Construct a complex phasor from magnitude and angle.
    """

    magnitude_value = nonnegative_real(
        magnitude_value,
        name="magnitude",
    )

    angle_radians = finite_real(
        angle_radians,
        name="angle_radians",
    )

    return (
        magnitude_value
        * complex(
            math.cos(angle_radians),
            math.sin(angle_radians),
        )
    )


# =====================================================================
# SAFE COMPLEX DIVISION
# =====================================================================

def safe_divide(
    numerator: complex | float,
    denominator: complex | float,
    *,
    epsilon: float = DEFAULT_EPSILON,
) -> complex:
    """
    Perform protected complex division.

    Raises
    ------
    ZeroDivisionError
        When denominator magnitude is below epsilon.
    """

    epsilon = positive_real(
        epsilon,
        name="epsilon",
    )

    denominator_complex = complex(
        denominator
    )

    if abs(
        denominator_complex
    ) <= epsilon:
        raise ZeroDivisionError(
            "Complex denominator is too small."
        )

    return (
        complex(numerator)
        / denominator_complex
    )


# =====================================================================
# APPARENT IMPEDANCE
# =====================================================================

def apparent_impedance(
    voltage: complex | float,
    current: complex | float,
    *,
    epsilon: float = DEFAULT_IMPEDANCE_EPSILON,
) -> complex:
    """
    Calculate apparent impedance:

        Z = V / I

    This is a mathematical quantity only.

    It does not implement a distance relay characteristic.
    """

    return safe_divide(
        voltage,
        current,
        epsilon=epsilon,
    )


# =====================================================================
# IMPEDANCE MAGNITUDE
# =====================================================================

def impedance_magnitude(
    voltage: complex | float,
    current: complex | float,
    *,
    epsilon: float = DEFAULT_IMPEDANCE_EPSILON,
) -> float:
    """
    Calculate apparent impedance magnitude:

        |Z| = |V / I|
    """

    return magnitude(
        apparent_impedance(
            voltage,
            current,
            epsilon=epsilon,
        )
    )


# =====================================================================
# IMPEDANCE ANGLE
# =====================================================================

def impedance_angle(
    voltage: complex | float,
    current: complex | float,
    *,
    epsilon: float = DEFAULT_IMPEDANCE_EPSILON,
) -> float:
    """
    Calculate apparent impedance angle in radians.
    """

    impedance = apparent_impedance(
        voltage,
        current,
        epsilon=epsilon,
    )

    return angle(
        impedance
    )


# =====================================================================
# DIRECTIONAL CHARACTERISTIC
# =====================================================================

def directional_characteristic(
    voltage: complex | float,
    current: complex | float,
    *,
    characteristic_angle: float = 0.0,
) -> float:
    """
    Calculate a generic directional characteristic quantity.

    The mathematical characteristic is:

        T = Re{ V × conj(I) × exp(-jθc) }

    where:

        V  = polarizing voltage phasor
        I  = operating current phasor
        θc = relay characteristic angle

    Positive values indicate one directional half-plane and
    negative values indicate the opposite half-plane.

    This function does NOT decide forward/reverse operation.
    """

    voltage = complex(
        voltage
    )

    current = complex(
        current
    )

    characteristic_angle = finite_real(
        characteristic_angle,
        name="characteristic_angle",
    )

    if not (
        math.isfinite(voltage.real)
        and math.isfinite(voltage.imag)
        and math.isfinite(current.real)
        and math.isfinite(current.imag)
    ):
        raise ValueError(
            "Voltage and current phasors must be finite."
        )

    rotation = complex(
        math.cos(
            -characteristic_angle
        ),
        math.sin(
            -characteristic_angle
        ),
    )

    return float(
        (
            voltage
            * current.conjugate()
            * rotation
        ).real
    )


# =====================================================================
# DIRECTIONAL POLARIZING ANGLE
# =====================================================================

def directional_angle(
    voltage: complex | float,
    current: complex | float,
) -> float:
    """
    Return the angle difference:

        angle(V) - angle(I)

    in radians.

    This is a numerical quantity only.
    """

    return angle(
        complex(voltage)
        / complex(current)
    )


# =====================================================================
# SEQUENCE COMPONENTS
# =====================================================================

def symmetrical_components(
    phase_a: complex | float,
    phase_b: complex | float,
    phase_c: complex | float,
) -> Mapping[str, complex]:
    """
    Calculate positive-, negative-, and zero-sequence components.

    Returns
    -------

        {
            "zero": V0,
            "positive": V1,
            "negative": V2,
        }

    The transformation is:

        V0 = (Va + Vb + Vc) / 3

        V1 = (Va + aVb + a²Vc) / 3

        V2 = (Va + a²Vb + aVc) / 3

    where:

        a = exp(j 120°)

    This function is reusable by:

        - negative-sequence protection;
        - zero-sequence protection;
        - earth-fault protection;
        - unbalance protection;
        - generator protection;
        - motor protection.
    """

    a = complex(
        -0.5,
        math.sqrt(3.0) / 2.0,
    )

    a_squared = a * a

    va = complex(
        phase_a
    )
    vb = complex(
        phase_b
    )
    vc = complex(
        phase_c
    )

    for name, value in (
        ("phase_a", va),
        ("phase_b", vb),
        ("phase_c", vc),
    ):
        if not (
            math.isfinite(value.real)
            and math.isfinite(value.imag)
        ):
            raise ValueError(
                f"{name} must be finite."
            )

    zero = (
        va
        + vb
        + vc
    ) / 3.0

    positive = (
        va
        + a * vb
        + a_squared * vc
    ) / 3.0

    negative = (
        va
        + a_squared * vb
        + a * vc
    ) / 3.0

    return {
        "zero": zero,
        "positive": positive,
        "negative": negative,
    }


# =====================================================================
# RESIDUAL / ZERO-SEQUENCE QUANTITY
# =====================================================================

def residual_quantity(
    phase_a: complex | float,
    phase_b: complex | float,
    phase_c: complex | float,
) -> complex:
    """
    Calculate the residual quantity:

        Xres = Xa + Xb + Xc

    This is useful for current or voltage residual quantities.

    The caller determines whether the quantity represents:

        3I0
        3V0
        residual current
        residual voltage
    """

    result = (
        complex(phase_a)
        + complex(phase_b)
        + complex(phase_c)
    )

    if not (
        math.isfinite(result.real)
        and math.isfinite(result.imag)
    ):
        raise ValueError(
            "Phase quantities must be finite."
        )

    return result


# =====================================================================
# RATE OF CHANGE
# =====================================================================

def rate_of_change(
    current_value: float,
    previous_value: float,
    delta_time: float,
) -> float:
    """
    Calculate a finite-difference rate of change:

        dx/dt = (x2 - x1) / Δt

    This primitive can support future functions such as:

        - ROCOF;
        - voltage rate-of-change;
        - frequency rate-of-change;
        - thermal derivative functions.
    """

    current_value = finite_real(
        current_value,
        name="current_value",
    )

    previous_value = finite_real(
        previous_value,
        name="previous_value",
    )

    delta_time = positive_real(
        delta_time,
        name="delta_time",
    )

    return (
        current_value
        - previous_value
    ) / delta_time


# =====================================================================
# LINEAR INTERPOLATION
# =====================================================================

def linear_interpolate(
    x: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:
    """
    Perform linear interpolation.

    This is intentionally generic and is useful for future
    protection characteristics and TCC calculations.
    """

    x = finite_real(
        x,
        name="x",
    )
    x1 = finite_real(
        x1,
        name="x1",
    )
    y1 = finite_real(
        y1,
        name="y1",
    )
    x2 = finite_real(
        x2,
        name="x2",
    )
    y2 = finite_real(
        y2,
        name="y2",
    )

    if abs(
        x2 - x1
    ) <= DEFAULT_EPSILON:
        raise ValueError(
            "Interpolation x coordinates must be distinct."
        )

    return (
        y1
        + (
            (x - x1)
            / (x2 - x1)
        )
        * (y2 - y1)
    )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    # IEC
    "IEC_CURVES",
    "IEC_CURVE_ALIASES",
    "normalize_iec_curve",
    "iec_curve_constants",
    "current_multiplier",
    "iec_pickup",
    "iec_time",
    "generate_iec_curve",

    # Validation
    "finite_real",
    "positive_real",
    "nonnegative_real",

    # Phasor mathematics
    "magnitude",
    "angle",
    "polar_phasor",
    "safe_divide",

    # Impedance
    "apparent_impedance",
    "impedance_magnitude",
    "impedance_angle",

    # Directional
    "directional_characteristic",
    "directional_angle",

    # Sequence quantities
    "symmetrical_components",
    "residual_quantity",

    # Dynamic numerical primitives
    "rate_of_change",

    # Characteristic utilities
    "linear_interpolate",
]
