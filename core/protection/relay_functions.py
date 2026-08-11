```python
"""
GridForge Protection Relay Functions
====================================

File:
    core/protection/relay_functions.py

Purpose
-------
Pure numerical functions used by GridForge protection algorithms.

This module provides the IEC 60255 inverse-time characteristic
calculation used by:

    core/protection/overcurrent/iec_relay.py
    core/protection/coordination/tcc_curve.py

Supported IEC curves
--------------------
    SI  - Standard / Normal Inverse
    VI  - Very Inverse
    EI  - Extremely Inverse

IEC inverse-time equation
-------------------------

             k × TMS
    t = -------------------
         M^alpha - 1

where:

    M = I / Pickup

The curve constants are:

    SI:
        k     = 0.14
        alpha = 0.02

    VI:
        k     = 13.5
        alpha = 1.0

    EI:
        k     = 80.0
        alpha = 2.0

Architecture
------------
This module MUST remain independent of:

    - core.model
    - Relay
    - Breaker
    - ProtectionSystem
    - BreakerManager
    - Network topology
    - Fault calculation
    - Relay coordination state

It contains only reusable protection mathematics.

Design principle
----------------
The numerical IEC characteristic is implemented once here.

Protection classes should call these functions rather than
duplicating IEC equations.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

import math
from typing import Dict


# ================================================================
# IEC CURVE DEFINITIONS
# ================================================================

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


# ================================================================
# CURVE ALIASES
# ================================================================

IEC_CURVE_ALIASES = {
    "SI": "SI",
    "STANDARD_INVERSE": "SI",
    "NORMAL_INVERSE": "SI",

    "VI": "VI",
    "VERY_INVERSE": "VI",

    "EI": "EI",
    "EXTREMELY_INVERSE": "EI",
}


# ================================================================
# CURVE NORMALIZATION
# ================================================================

def normalize_iec_curve(
    curve: str,
) -> str:
    """
    Normalize an IEC curve name.

    Parameters
    ----------
    curve:
        IEC curve identifier or supported descriptive alias.

    Returns
    -------
    str
        Canonical curve identifier:

            SI
            VI
            EI

    Raises
    ------
    ValueError
        If the curve is unsupported.
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
            "Supported curves: "
            "SI, VI, EI, "
            "NORMAL_INVERSE, VERY_INVERSE, "
            "EXTREMELY_INVERSE."
        ) from None


# ================================================================
# CURVE CONSTANTS
# ================================================================

def iec_curve_constants(
    curve: str,
) -> Dict[str, float]:
    """
    Return IEC curve constants.

    Parameters
    ----------
    curve:
        IEC curve identifier or alias.

    Returns
    -------
    dict
        Dictionary containing:

            k
            alpha
    """

    canonical_curve = normalize_iec_curve(
        curve
    )

    constants = IEC_CURVES[
        canonical_curve
    ]

    return {
        "k": constants["k"],
        "alpha": constants["alpha"],
    }


# ================================================================
# MULTIPLIER OF PICKUP
# ================================================================

def current_multiplier(
    current: float,
    pickup: float,
) -> float:
    """
    Calculate the current multiple M.

        M = I / Pickup

    Parameters
    ----------
    current:
        Measured fault/current magnitude.

    pickup:
        Relay pickup current.

    Returns
    -------
    float
        Current multiple.

    Raises
    ------
    ValueError
        If pickup is not positive.
    """

    pickup = float(
        pickup
    )

    if pickup <= 0.0:
        raise ValueError(
            "Pickup current must be positive."
        )

    return abs(
        float(current)
    ) / pickup


# ================================================================
# IEC OPERATING TIME
# ================================================================

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

                 k × TMS
        t = -------------------
             M^alpha - 1

        M = I / Pickup

    Parameters
    ----------
    current:
        Measured current magnitude.

    pickup:
        Relay pickup current.

    curve:
        IEC curve identifier.

        Supported:

            SI
            VI
            EI
            NORMAL_INVERSE
            VERY_INVERSE
            EXTREMELY_INVERSE

    TMS:
        Time Multiplier Setting.

    Returns
    -------
    float
        Operating time in seconds.

        Returns:

            math.inf

        when current is at or below pickup.

    Raises
    ------
    ValueError
        If pickup <= 0.
        If TMS < 0.
        If current is not finite.
    """

    current = float(
        current
    )

    pickup = float(
        pickup
    )

    TMS = float(
        TMS
    )

    if not math.isfinite(
        current
    ):
        raise ValueError(
            "Current must be finite."
        )

    if pickup <= 0.0:
        raise ValueError(
            "Pickup current must be positive."
        )

    if TMS < 0.0:
        raise ValueError(
            "TMS must be >= 0."
        )

    canonical_curve = normalize_iec_curve(
        curve
    )

    constants = IEC_CURVES[
        canonical_curve
    ]

    k = constants[
        "k"
    ]

    alpha = constants[
        "alpha"
    ]

    M = abs(
        current
    ) / pickup

    # ------------------------------------------------------------
    # Below or exactly at pickup
    # ------------------------------------------------------------

    if M <= 1.0:
        return math.inf

    # ------------------------------------------------------------
    # IEC inverse-time characteristic
    # ------------------------------------------------------------

    denominator = (
        M ** alpha
        - 1.0
    )

    # Defensive protection against numerical singularity.
    if denominator <= 0.0:
        return math.inf

    return (
        TMS
        * k
        / denominator
    )


# ================================================================
# PICKUP CHECK
# ================================================================

def iec_pickup(
    current: float,
    pickup: float,
) -> bool:
    """
    Determine whether current exceeds the IEC relay pickup.

    Parameters
    ----------
    current:
        Measured current magnitude.

    pickup:
        Relay pickup current.

    Returns
    -------
    bool
        True when current is strictly above pickup.

    Notes
    -----
    This function deliberately uses:

        I > Pickup

    rather than:

        I >= Pickup

    because the operating-time characteristic is infinite at
    exactly M = 1.
    """

    pickup = float(
        pickup
    )

    if pickup <= 0.0:
        raise ValueError(
            "Pickup current must be positive."
        )

    return (
        abs(float(current))
        > pickup
    )


# ================================================================
# CURVE DATA
# ================================================================

def generate_iec_curve(
    pickup: float,
    curve: str = "SI",
    TMS: float = 1.0,
    multipliers=None,
) -> list[dict]:
    """
    Generate IEC time-current characteristic data.

    Parameters
    ----------
    pickup:
        Relay pickup current.

    curve:
        IEC curve identifier.

    TMS:
        Time Multiplier Setting.

    multipliers:
        Iterable of current multiples.

        If omitted:

            1, 2, ..., 20

    Returns
    -------
    list of dict
        Each item contains:

            {
                "multiple": M,
                "current": I,
                "time": t
            }

    Notes
    -----
    At M = 1, operating time is infinity.
    """

    pickup = float(
        pickup
    )

    if pickup <= 0.0:
        raise ValueError(
            "Pickup current must be positive."
        )

    if multipliers is None:
        multipliers = range(
            1,
            21,
        )

    curve_data = []

    for multiplier in multipliers:

        multiplier = float(
            multiplier
        )

        if multiplier <= 0.0:
            raise ValueError(
                "Current multipliers must be positive."
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

        curve_data.append(
            {
                "multiple": multiplier,
                "current": current,
                "time": time,
            }
        )

    return curve_data


# ================================================================
# PUBLIC API
# ================================================================

__all__ = [
    "IEC_CURVES",
    "IEC_CURVE_ALIASES",
    "normalize_iec_curve",
    "iec_curve_constants",
    "current_multiplier",
    "iec_time",
    "iec_pickup",
    "generate_iec_curve",
]
```
