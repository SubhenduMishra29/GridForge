```python
# core/model/transformer.py

"""
GridForge Two-Winding Transformer Model
=======================================

GridForge Model Layer V2

Defines the GridForge two-winding transformer model.

Architecture
------------
Transformer is a specialized Branch.

Common Branch responsibilities:
    - Two-terminal connectivity
    - Series impedance
    - Equipment rating
    - In-service state
    - Common electrical interface

Transformer-specific responsibilities:
    - Off-nominal tap ratio
    - Phase-shifting angle
    - Complex transformer ratio

The Transformer model does NOT:
    - Build Y-bus.
    - Perform power-flow calculations.
    - Perform fault calculations.
    - Perform voltage regulation.
    - Perform numerical optimization.
    - Calculate loading.
    - Store GUI geometry.

Those responsibilities belong to the appropriate
network/solver/analysis layers.

Transformer Representation
--------------------------
The transformer uses the standard complex off-nominal ratio:

    a = t * exp(jθ)

where:

    t = tap magnitude
    θ = phase-shift angle in radians

The public ``phase_shift_deg`` interface uses degrees because this
is the conventional engineering/user-facing representation.

The inherited ``Branch.shift`` value is maintained in radians for
compatibility with the common branch/numerical interface.

State Ownership
---------------
The transformer model stores physical equipment parameters.

Calculated quantities such as transformer loading, losses, terminal
power, currents, and voltage regulation are NOT stored as persistent
model state. They belong to study/result objects or analysis layers.

This prevents stale numerical results from becoming part of the
authoritative electrical model.

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental transformer
model requirement that cannot be satisfied by a higher-level
network/solver/analysis layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite, radians
import cmath

from .branch import Branch


# =====================================================================
# TWO-WINDING TRANSFORMER
# =====================================================================

class Transformer(Branch):
    """
    GridForge two-winding transformer.

    Parameters
    ----------
    id : str
        Unique GridForge transformer identifier.

    bus_from :
        From-side GridForge Bus.

    bus_to :
        To-side GridForge Bus.

    r : float
        Series resistance in per-unit.

    x : float
        Series reactance in per-unit.

    tap_ratio : float, optional
        Off-nominal transformer tap magnitude.

        Default: 1.0

    phase_shift_deg : float, optional
        Phase-shifting angle in degrees.

        Default: 0.0

    name : str, optional
        Human-readable transformer name.

    rate_mva : float, optional
        Transformer continuous/equipment rating in MVA.

    Notes
    -----
    Transformer shunt susceptance is not represented by the common
    Branch ``b`` parameter in this model. The transformer therefore
    passes:

        b = 0.0

    to the Branch base class.

    Any transformer magnetizing branch, core-loss representation,
    grounding representation, winding connection, or more detailed
    transformer equivalent must be introduced explicitly as part of
    a future transformer model extension rather than being silently
    inferred here.
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
        # =============================================================
        # TRANSFORMER-SPECIFIC VALIDATION
        # =============================================================

        tap_ratio = float(tap_ratio)
        phase_shift_deg = float(phase_shift_deg)

        if not isfinite(tap_ratio):
            raise ValueError(
                "Transformer tap ratio must be finite."
            )

        if tap_ratio <= 0.0:
            raise ValueError(
                "Transformer tap ratio must be greater than zero."
            )

        if not isfinite(phase_shift_deg):
            raise ValueError(
                "Transformer phase shift must be finite."
            )

        # =============================================================
        # COMMON BRANCH INITIALIZATION
        # =============================================================

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
            shift=radians(phase_shift_deg),
        )

        # =============================================================
        # TRANSFORMER PARAMETERS
        # =============================================================

        # These are the authoritative transformer-specific values.
        self.tap_ratio = tap_ratio
        self.phase_shift_deg = phase_shift_deg

        # The inherited Branch fields ``tap`` and ``shift`` are kept
        # synchronized whenever the transformer control methods are
        # used. They provide the common numerical interface expected
        # by the network/solver layers.

    # =================================================================
    # TAP CONTROL
    # =================================================================

    def set_tap(
        self,
        tap_ratio: float,
    ) -> None:
        """
        Set the transformer off-nominal tap ratio.

        Parameters
        ----------
        tap_ratio : float
            Positive finite transformer tap magnitude.

        Notes
        -----
        The transformer-specific ``tap_ratio`` is authoritative.

        The inherited ``Branch.tap`` value is updated simultaneously
        to preserve the common Branch interface.
        """

        tap_ratio = float(tap_ratio)

        if not isfinite(tap_ratio):
            raise ValueError(
                "Transformer tap ratio must be finite."
            )

        if tap_ratio <= 0.0:
            raise ValueError(
                "Transformer tap ratio must be greater than zero."
            )

        self.tap_ratio = tap_ratio

        # Synchronize common Branch representation.
        self.tap = tap_ratio

    # =================================================================
    # PHASE-SHIFT CONTROL
    # =================================================================

    def set_phase_shift(
        self,
        phase_shift_deg: float,
    ) -> None:
        """
        Set transformer phase shift in degrees.

        Parameters
        ----------
        phase_shift_deg : float
            Finite phase-shifting angle in degrees.

        Notes
        -----
        ``phase_shift_deg`` is the engineering/user-facing value.

        The inherited ``Branch.shift`` value is maintained in radians
        for the common numerical interface.
        """

        phase_shift_deg = float(phase_shift_deg)

        if not isfinite(phase_shift_deg):
            raise ValueError(
                "Transformer phase shift must be finite."
            )

        self.phase_shift_deg = phase_shift_deg

        # Synchronize common Branch representation.
        self.shift = radians(phase_shift_deg)

    # =================================================================
    # COMPLEX TRANSFORMER RATIO
    # =================================================================

    @property
    def complex_tap(self) -> complex:
        """
        Return the complex transformer ratio.

        The standard representation is:

            a = t * exp(jθ)

        where:

            t = tap magnitude
            θ = phase shift in radians

        Returns
        -------
        complex
            Complex off-nominal transformer ratio.

        Notes
        -----
        This property provides data for the network/solver layer.

        It does not perform Y-bus stamping itself.
        """

        return (
            self.tap_ratio
            * cmath.exp(1j * self.shift)
        )

    # =================================================================
    # TRANSFORMER STATUS
    # =================================================================

    @property
    def has_phase_shift(self) -> bool:
        """
        Return True when the transformer has a non-zero phase shift.
        """

        return self.phase_shift_deg != 0.0

    @property
    def is_off_nominal(self) -> bool:
        """
        Return True when the transformer tap differs from unity.
        """

        return self.tap_ratio != 1.0

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

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
            }
        )

        return data

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

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
```
