```python
# core/model/line.py

"""
GridForge Transmission Line Model
=================================

GridForge Model Layer V2

Defines the GridForge transmission-line model.

Architecture
------------
Line is a specialized Branch.

Common Branch responsibilities:
    - Two-terminal connectivity
    - Series impedance
    - Shunt susceptance
    - Equipment rating
    - In-service state
    - Common electrical interface

Line-specific representation:
    - Standard transmission-line π-equivalent
    - Series resistance R
    - Series reactance X
    - Total shunt susceptance B

For a standard π-equivalent line:

    Z_series = R + jX

    Y_shunt,total = jB

The numerical network/solver layer is responsible for applying:

    jB / 2

at each terminal when constructing the network admittance model.

The Line model does NOT:
    - Build Y-bus.
    - Stamp admittance matrices.
    - Calculate branch power flow.
    - Calculate losses.
    - Perform load flow.
    - Perform short-circuit calculations.
    - Perform contingency analysis.
    - Perform protection calculations.
    - Perform dynamic simulation.
    - Store GUI geometry.

Numerical calculations belong to the appropriate
network/solver/analysis layers.

Units
-----
    r       : per-unit
    x       : per-unit
    b       : per-unit
    rate    : MVA

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental model requirement
that cannot be satisfied by the Branch base class or higher layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .branch import Branch


# =====================================================================
# TRANSMISSION LINE
# =====================================================================

class Line(Branch):
    """
    GridForge transmission-line model.

    The Line uses the standard two-terminal π-equivalent
    representation.

    Parameters
    ----------
    id : str
        Unique GridForge line identifier.

    bus_from :
        From-side GridForge Bus.

    bus_to :
        To-side GridForge Bus.

    r : float
        Series resistance in per-unit.

    x : float
        Series reactance in per-unit.

    b : float, optional
        Total line shunt susceptance in per-unit.

        The numerical Y-bus/network layer is responsible for applying
        jB/2 at each end of the line.

    name : str, optional
        Human-readable line name.

    rate_mva : float, optional
        Thermal/equipment rating in MVA.

    Notes
    -----
    ``Line`` inherits:

    - terminal connectivity
    - impedance
    - admittance
    - shunt-admittance representation
    - equipment rating
    - in-service state
    - common diagnostics

    from ``Branch``.

    A transmission line does not have a transformer tap or phase-shift
    parameter. Therefore the inherited Branch values are fixed to:

        tap = 1.0
        shift = 0.0
    """

    def __init__(
        self,
        id: str,
        bus_from,
        bus_to,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
    ):
        """
        Initialize a GridForge transmission line.
        """

        super().__init__(
            id=id,
            bus_from=bus_from,
            bus_to=bus_to,
            r=r,
            x=x,
            b=b,
            name=name,
            rate_mva=rate_mva,
            tap=1.0,
            shift=0.0,
        )

    # =================================================================
    # LINE-SPECIFIC PROPERTIES
    # =================================================================

    @property
    def r_pu(self) -> float:
        """
        Return the line series resistance in per-unit.

        This is a compatibility alias for the inherited ``r`` field.
        """

        return self.r

    @property
    def x_pu(self) -> float:
        """
        Return the line series reactance in per-unit.

        This is a compatibility alias for the inherited ``x`` field.
        """

        return self.x

    @property
    def b_pu(self) -> float:
        """
        Return the total line shunt susceptance in per-unit.

        This is a compatibility alias for the inherited ``b`` field.

        The value represents the TOTAL line shunt susceptance, not the
        susceptance of one terminal.
        """

        return self.b

    # =================================================================
    # LINE MODEL
    # =================================================================

    @property
    def is_pi_model(self) -> bool:
        """
        Return True because the Line uses the standard π-equivalent.
        """

        return True

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured transmission-line information.
        """

        data = super().summary()

        data.update(
            {
                "type": "line",
                "r_pu": self.r,
                "x_pu": self.x,
                "b_pu": self.b,
                "model": "pi",
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
            f"<Line "
            f"id={self.id}, "
            f"{self.from_bus.id} -> {self.to_bus.id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"b={self.b:.6f}, "
            f"rate={self.rate_mva:.2f} MVA, "
            f"in_service={self.in_service}>"
        )
```
