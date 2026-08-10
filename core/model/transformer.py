"""
GridForge Transformer Model
===========================

File:
    core/model/transformer.py

Defines the GridForge two-winding transformer model.

Architecture
------------
Transformer is a specialized Branch.

Common Branch responsibilities:
    - Two-terminal connectivity
    - Series impedance
    - In-service state
    - Equipment rating
    - Common electrical interface

Transformer-specific responsibilities:
    - Off-nominal tap ratio
    - Phase-shifting angle
    - Complex transformer ratio

The Transformer model does NOT:
    - Build Ybus.
    - Perform power flow.
    - Perform fault calculations.
    - Perform voltage regulation.
    - Perform numerical optimization.

Those responsibilities belong to the solver/analysis layers.

Ybus construction may consume the transformer parameters exposed
by this model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import numpy as np

from .branch import Branch


class Transformer(Branch):
    """
    Two-winding transformer.

    Parameters
    ----------
    id:
        Unique transformer identifier.

    bus_from:
        From-side Bus object.

    bus_to:
        To-side Bus object.

    r:
        Series resistance in per-unit.

    x:
        Series reactance in per-unit.

    tap_ratio:
        Off-nominal tap ratio.

        Default:
            1.0

    phase_shift_deg:
        Phase-shifting angle in degrees.

        Default:
            0.0

    name:
        Human-readable transformer name.

    rate_mva:
        Transformer rating in MVA.

    Notes
    -----
    The transformer is represented using the standard complex
    off-nominal ratio:

        a = tap * exp(jθ)

    where θ is converted from degrees to radians internally.
    """

    def __init__(
        self,
        id: str,
        bus_from,
        bus_to,
        r: float,
        x: float,
        tap_ratio: float = 1.0,
        phase_shift_deg: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
    ):

        # =========================================================
        # TRANSFORMER-SPECIFIC VALIDATION
        # =========================================================

        if tap_ratio <= 0.0:
            raise ValueError(
                "Transformer tap ratio must be positive"
            )

        # =========================================================
        # COMMON BRANCH INITIALIZATION
        # =========================================================

        super().__init__(
            id=id,
            bus_from=bus_from,
            bus_to=bus_to,
            r=r,
            x=x,
            b=0.0,
            name=name,
            rate_mva=rate_mva,
            tap=tap_ratio,
            shift=np.deg2rad(
                phase_shift_deg
            ),
        )

        # =========================================================
        # TRANSFORMER PARAMETERS
        # =========================================================

        self.tap_ratio = float(
            tap_ratio
        )

        self.phase_shift_deg = float(
            phase_shift_deg
        )

        # =========================================================
        # RESULTS
        # =========================================================
        #
        # Numerical solvers may populate these later.
        # The model itself does not calculate them.
        # =========================================================

        self.loading_mva = 0.0

    # =============================================================
    # TAP CONTROL
    # =============================================================

    def set_tap(
        self,
        tap_ratio: float
    ) -> None:
        """
        Set the transformer off-nominal tap ratio.

        Parameters
        ----------
        tap_ratio:
            Positive transformer tap ratio.
        """

        if tap_ratio <= 0.0:
            raise ValueError(
                "Transformer tap ratio must be positive"
            )

        self.tap_ratio = float(
            tap_ratio
        )

        # Keep the common Branch representation synchronized.
        self.tap = self.tap_ratio

    # =============================================================
    # PHASE SHIFT CONTROL
    # =============================================================

    def set_phase_shift(
        self,
        phase_shift_deg: float
    ) -> None:
        """
        Set transformer phase shift in degrees.
        """

        self.phase_shift_deg = float(
            phase_shift_deg
        )

        # Keep the common Branch representation synchronized.
        self.shift = np.deg2rad(
            self.phase_shift_deg
        )

    # =============================================================
    # COMPLEX TRANSFORMER RATIO
    # =============================================================

    @property
    def complex_tap(self) -> complex:
        """
        Return the complex transformer ratio.

        a = tap * exp(jθ)

        where θ is the phase-shift angle in radians.

        This property is intended for Ybus/network stamping.
        """

        return (
            self.tap_ratio
            *
            np.exp(
                1j * self.shift
            )
        )

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured transformer information.
        """

        data = super().summary()

        data.update(
            {
                "type": "transformer",
                "tap_ratio": self.tap_ratio,
                "phase_shift_deg": self.phase_shift_deg,
                "complex_tap": self.complex_tap,
                "loading_mva": self.loading_mva,
            }
        )

        return data

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<Transformer "
            f"id={self.id}, "
            f"{self.from_bus.id} -> {self.to_bus.id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"tap={self.tap_ratio:.6f}, "
            f"shift={self.phase_shift_deg:.3f}°, "
            f"in_service={self.in_service}>"
        )
