"""
GridForge TCC Curve Engine
==========================

File:
    core/protection/coordination/tcc_curve.py

Purpose
-------
Pure IEC inverse-time Time-Current Characteristic (TCC)
calculation engine for protection coordination.

Supported IEC 60255 inverse-time characteristics:

    NORMAL_INVERSE
    VERY_INVERSE
    EXTREMELY_INVERSE

Responsibilities
----------------
- Provide IEC inverse-time curve constants.
- Calculate relay operating time.
- Generate TCC curve points.
- Expose characteristic information.

This module MUST remain a pure calculation layer.

It does NOT:
- Store relay state.
- Store relay measurements.
- Operate relays.
- Operate circuit breakers.
- Modify the network model.
- Perform fault calculations.
- Coordinate multiple relays.
- Execute protection trips.

Relay coordination is implemented by:

    core/protection/coordination/relay_coordination.py

IEC relay protection uses the shared IEC calculation layer:

    core/protection/relay_functions.py

Architecture
------------

    IEC relay
        |
        v
    relay_functions.py
        |
        +----------------+
        |                |
        v                v
    Protection       TCCCurve
                         |
                         v
                 RelayCoordination

The mathematical definition of the IEC curves is kept
consistent across the protection stack.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

import math
from typing import Iterable


class TCCCurve:
    """
    IEC inverse-time TCC calculation engine.

    Parameters
    ----------
    curve_type:
        IEC inverse-time curve name.

    Supported curves
    ----------------
    NORMAL_INVERSE
        IEC Standard/Normal Inverse.

    VERY_INVERSE
        IEC Very Inverse.

    EXTREMELY_INVERSE
        IEC Extremely Inverse.
    """

    # =========================================================
    # IEC CURVE DEFINITIONS
    # =========================================================

    IEC_CURVES = {
        "NORMAL_INVERSE": {
            "k": 0.14,
            "alpha": 0.02,
        },
        "VERY_INVERSE": {
            "k": 13.5,
            "alpha": 1.0,
        },
        "EXTREMELY_INVERSE": {
            "k": 80.0,
            "alpha": 2.0,
        },
    }

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        curve_type: str = "NORMAL_INVERSE",
    ) -> None:
        """
        Initialize the TCC calculation engine.
        """

        curve_type = str(
            curve_type
        ).upper()

        if curve_type not in self.IEC_CURVES:
            raise ValueError(
                f"Unsupported IEC curve: "
                f"{curve_type}. Supported curves: "
                f"{sorted(self.IEC_CURVES)}"
            )

        self.curve_type = curve_type

        characteristics = (
            self.IEC_CURVES[
                curve_type
            ]
        )

        self.k = float(
            characteristics["k"]
        )

        self.alpha = float(
            characteristics["alpha"]
        )

    # =========================================================
    # OPERATING TIME
    # =========================================================

    def calculate_time(
        self,
        fault_current: float,
        pickup_current: float,
        TMS: float = 1.0,
    ) -> float:
        """
        Calculate IEC inverse-time operating time.

        Equation
        --------

            t = TMS * k / (M^alpha - 1)

        where:

            M = |I| / Ip

        Parameters
        ----------
        fault_current:
            Fault current magnitude.

        pickup_current:
            Relay pickup current.

        TMS:
            IEC Time Multiplier Setting.

        Returns
        -------
        float
            Operating time in seconds.

            infinity:
                Current is at or below pickup.
        """

        pickup_current = float(
            pickup_current
        )

        TMS = float(
            TMS
        )

        if not math.isfinite(
            pickup_current
        ):
            raise ValueError(
                "Pickup current must be finite."
            )

        if pickup_current <= 0.0:
            raise ValueError(
                "Pickup current must be > 0."
            )

        if not math.isfinite(
            TMS
        ):
            raise ValueError(
                "TMS must be finite."
            )

        if TMS < 0.0:
            raise ValueError(
                "TMS must be >= 0."
            )

        current = abs(
            float(fault_current)
        )

        if not math.isfinite(
            current
        ):
            raise ValueError(
                "Fault current must be finite."
            )

        M = (
            current
            /
            pickup_current
        )

        # -----------------------------------------------------
        # Below or exactly at pickup
        # -----------------------------------------------------

        if M <= 1.0:
            return float("inf")

        denominator = (
            M ** self.alpha
            - 1.0
        )

        if denominator <= 0.0:
            return float("inf")

        return (
            TMS
            *
            self.k
            /
            denominator
        )

    # =========================================================
    # CURVE DATA GENERATION
    # =========================================================

    def generate_curve(
        self,
        pickup_current: float,
        TMS: float = 1.0,
        multiplier_range: Iterable[float] | None = None,
    ) -> list[dict]:
        """
        Generate TCC curve points.

        Parameters
        ----------
        pickup_current:
            Relay pickup current.

        TMS:
            IEC Time Multiplier Setting.

        multiplier_range:
            Iterable containing current multiples relative
            to pickup.

            Example:

                range(1, 21)

            produces:

                1x, 2x, ... 20x pickup.

        Returns
        -------
        list[dict]
            Curve points containing:

                current
                multiple
                time
        """

        pickup_current = float(
            pickup_current
        )

        if not math.isfinite(
            pickup_current
        ):
            raise ValueError(
                "Pickup current must be finite."
            )

        if pickup_current <= 0.0:
            raise ValueError(
                "Pickup current must be > 0."
            )

        if multiplier_range is None:
            multiplier_range = range(
                1,
                21,
            )

        curve = []

        for multiplier in (
            multiplier_range
        ):

            multiplier = float(
                multiplier
            )

            if not math.isfinite(
                multiplier
            ):
                raise ValueError(
                    "Current multiplier must be finite."
                )

            if multiplier <= 0.0:
                raise ValueError(
                    "Current multiplier must "
                    "be > 0."
                )

            current = (
                pickup_current
                *
                multiplier
            )

            operating_time = (
                self.calculate_time(
                    fault_current=current,
                    pickup_current=pickup_current,
                    TMS=TMS,
                )
            )

            curve.append(
                {
                    "current": current,
                    "multiple": multiplier,
                    "time": operating_time,
                }
            )

        return curve

    # =========================================================
    # CHARACTERISTIC INFORMATION
    # =========================================================

    def characteristic(
        self,
    ) -> dict:
        """
        Return the IEC characteristic constants.
        """

        return {
            "curve_type": self.curve_type,
            "k": self.k,
            "alpha": self.alpha,
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<TCCCurve "
            f"curve={self.curve_type}, "
            f"k={self.k}, "
            f"alpha={self.alpha}>"
        )


__all__ = [
    "TCCCurve",
]
