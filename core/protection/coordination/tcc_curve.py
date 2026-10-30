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
from types import MappingProxyType

from core.protection.relay_functions import (
    iec_curve_definition,
    iec_time,
    normalize_iec_curve,
    pickup_exceeded,
    IEC_CURVES as CANONICAL_IEC_CURVES,
)


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
    # IEC CURVE DEFINITIONS / INITIALIZATION
    # =========================================================

    _LEGACY_NAMES = {
        "SI": "NORMAL_INVERSE",
        "VI": "VERY_INVERSE",
        "EI": "EXTREMELY_INVERSE",
    }
    IEC_CURVES = MappingProxyType({
        "NORMAL_INVERSE": MappingProxyType({
            "k": CANONICAL_IEC_CURVES["SI"].k,
            "alpha": CANONICAL_IEC_CURVES["SI"].alpha,
        }),
        "VERY_INVERSE": MappingProxyType({
            "k": CANONICAL_IEC_CURVES["VI"].k,
            "alpha": CANONICAL_IEC_CURVES["VI"].alpha,
        }),
        "EXTREMELY_INVERSE": MappingProxyType({
            "k": CANONICAL_IEC_CURVES["EI"].k,
            "alpha": CANONICAL_IEC_CURVES["EI"].alpha,
        }),
    })

    def __init__(self, curve_type: str = "NORMAL_INVERSE") -> None:
        """Initialize a compatibility adapter over the canonical IEC engine."""
        canonical = normalize_iec_curve(curve_type)
        self._curve_code = canonical
        self.curve_type = self._LEGACY_NAMES[canonical]
        definition = iec_curve_definition(canonical)
        self.k = definition.k
        self.alpha = definition.alpha

    # =========================================================
    # OPERATING TIME
    # =========================================================

    def calculate_time(
        self,
        fault_current: float,
        pickup_current: float,
        TMS: float = 1.0,
    ) -> float:
        """Calculate operating time through the canonical IEC equation."""
        if isinstance(TMS, bool):
            raise TypeError("TMS must be numeric, not boolean.")
        try:
            multiplier = float(TMS)
        except (TypeError, ValueError) as exc:
            raise ValueError("TMS must be numeric.") from exc
        if not math.isfinite(multiplier) or multiplier < 0.0:
            raise ValueError("TMS must be finite and non-negative.")
        # Preserve the historical TMS=0 compatibility behaviour while
        # requiring all positive-TMS calculations to use the canonical
        # numerically-stable IEC equation.
        if multiplier == 0.0:
            return 0.0 if pickup_exceeded(fault_current, pickup_current) else float("inf")
        return iec_time(
            current=fault_current,
            pickup=pickup_current,
            curve=self._curve_code,
            TMS=multiplier,
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
        """Generate numerical TCC points using the canonical time equation."""
        if isinstance(pickup_current, bool):
            raise TypeError("pickup_current must be numeric, not boolean.")
        try:
            pickup = float(pickup_current)
        except (TypeError, ValueError) as exc:
            raise ValueError("pickup_current must be numeric.") from exc
        if not math.isfinite(pickup) or pickup <= 0.0:
            raise ValueError("pickup_current must be finite and positive.")
        if multiplier_range is None:
            multiplier_range = range(1, 21)
        result: list[dict[str, float]] = []
        for raw_multiplier in multiplier_range:
            if isinstance(raw_multiplier, bool):
                raise TypeError("Current multiplier must be numeric, not boolean.")
            try:
                multiplier = float(raw_multiplier)
            except (TypeError, ValueError) as exc:
                raise ValueError("Current multiplier must be numeric.") from exc
            if not math.isfinite(multiplier) or multiplier <= 0.0:
                raise ValueError("Current multiplier must be finite and positive.")
            current = pickup * multiplier
            operating_time = self.calculate_time(
                fault_current=current,
                pickup_current=pickup,
                TMS=TMS,
            )
            result.append({
                "current": current,
                "multiple": multiplier,
                "time": operating_time,
            })
        return result

    # =========================================================
    # CHARACTERISTIC INFORMATION
    # =========================================================

    def characteristic(self) -> dict:
        """Return legacy curve identifier and canonical IEC constants."""
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
