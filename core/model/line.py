```python
"""
GridForge Transmission Line Model
=================================

File:
    core/model/line.py

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

Line-specific meaning:
    - Standard transmission-line π-equivalent
    - Series R + jX
    - Total shunt susceptance B

The Line model does NOT:
    - Build Ybus.
    - Calculate branch power flow.
    - Calculate losses.
    - Perform load flow.
    - Perform short-circuit calculations.
    - Perform contingency analysis.
    - Store GUI geometry.

Numerical calculations belong to the network/solver/analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .branch import Branch


class Line(Branch):
    """
    GridForge transmission-line model.

    The line uses the standard π-equivalent representation.

    Parameters
    ----------
    id:
        Unique line identifier.

    bus_from:
        From-side Bus object.

    bus_to:
        To-side Bus object.

    r:
        Series resistance in per-unit.

    x:
        Series reactance in per-unit.

    b:
        Total shunt susceptance in per-unit.

        The Ybus builder is responsible for applying:

            jB / 2

        at each end of the line.

    name:
        Human-readable line name.

    rate_mva:
        Thermal/equipment rating in MVA.

    Notes
    -----
    ``Line`` deliberately does not calculate power flow itself.

    Power-flow calculations belong to the solver layer so that
    all electrical elements use a consistent numerical convention.
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
        Initialize a transmission line.
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

    # =============================================================
    # LINE-SPECIFIC PROPERTIES
    # =============================================================

    @property
    def r_pu(self) -> float:
        """
        Compatibility alias for series resistance.

        Returns
        -------
        float
            Series resistance in per-unit.
        """

        return self.r

    @property
    def x_pu(self) -> float:
        """
        Compatibility alias for series reactance.

        Returns
        -------
        float
            Series reactance in per-unit.
        """

        return self.x

    @property
    def b_pu(self) -> float:
        """
        Compatibility alias for total shunt susceptance.

        Returns
        -------
        float
            Total line shunt susceptance in per-unit.
        """

        return self.b

    # =============================================================
    # LINE MODEL
    # =============================================================

    @property
    def is_pi_model(self) -> bool:
        """
        Identify the line as a standard π-equivalent element.
        """

        return True

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured line information.
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

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
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
