"""
GridForge Branch Model
======================

File:
    core/model/branch.py

Defines the common two-terminal electrical branch model.

A Branch represents a generic two-terminal network element.

Examples:
    - Transmission line
    - Transformer
    - Future FACTS / series compensation elements

Responsibilities
----------------
- Electrical connectivity.
- Branch electrical parameters.
- In-service state.
- Common impedance/admittance interface.

The Branch model does NOT:
- Build Ybus.
- Perform load flow.
- Calculate Newton-Raphson corrections.
- Perform short-circuit analysis.
- Store GUI geometry.

Numerical calculations belong to the solver/analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject
from .terminal import Terminal


class Branch(ElectricalObject):
    """
    Generic two-terminal electrical branch.

    Parameters
    ----------
    id:
        Unique branch identifier.

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

    name:
        Human-readable branch name.

    rate_mva:
        Continuous/nominal thermal rating in MVA.

    tap:
        Transformer tap ratio.

        For an ordinary transmission line this remains 1.0.

    shift:
        Phase-shifting angle in radians.

        For an ordinary transmission line this remains 0.0.
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
        tap: float = 1.0,
        shift: float = 0.0,
    ):

        super().__init__(
            id,
            name
        )

        # =========================================================
        # CONNECTIVITY
        # =========================================================

        if bus_from is None:
            raise ValueError(
                "Branch from-bus cannot be None"
            )

        if bus_to is None:
            raise ValueError(
                "Branch to-bus cannot be None"
            )

        if bus_from is bus_to:
            raise ValueError(
                "Branch cannot connect a bus to itself"
            )

        self.from_terminal = Terminal(
            bus_from
        )

        self.to_terminal = Terminal(
            bus_to
        )

        # =========================================================
        # ELECTRICAL PARAMETERS
        # =========================================================

        self.r = float(r)
        self.x = float(x)
        self.b = float(b)

        # =========================================================
        # TRANSFORMER-COMPATIBLE PARAMETERS
        # =========================================================

        self.tap = float(tap)
        self.shift = float(shift)

        # =========================================================
        # EQUIPMENT DATA
        # =========================================================

        self.rate_mva = float(
            rate_mva
        )

        # =========================================================
        # OPERATIONAL STATE
        # =========================================================

        self.in_service = True

        # =========================================================
        # VALIDATION
        # =========================================================

        self._validate_parameters()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_parameters(self):
        """
        Validate branch electrical parameters.
        """

        if self.r == 0.0 and self.x == 0.0:

            raise ValueError(
                f"Branch '{self.id}' "
                "cannot have zero series impedance"
            )

        if self.tap == 0.0:

            raise ValueError(
                f"Branch '{self.id}' "
                "tap ratio cannot be zero"
            )

        if self.rate_mva < 0.0:

            raise ValueError(
                f"Branch '{self.id}' "
                "rate_mva cannot be negative"
            )

    # =============================================================
    # CONNECTIVITY
    # =============================================================

    @property
    def from_bus(self):
        """
        Return the from-side Bus.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the to-side Bus.
        """

        return self.to_terminal.bus

    def buses(self):
        """
        Return the branch endpoints.

        Returns
        -------
        tuple
            (from_bus, to_bus)
        """

        return (
            self.from_bus,
            self.to_bus
        )

    # =============================================================
    # ELECTRICAL PROPERTIES
    # =============================================================

    @property
    def impedance(self) -> complex:
        """
        Series impedance:

            Z = R + jX
        """

        return complex(
            self.r,
            self.x
        )

    @property
    def admittance(self) -> complex:
        """
        Series admittance:

            Y = 1 / Z
        """

        z = self.impedance

        if z == 0:

            raise ZeroDivisionError(
                f"Branch '{self.id}' "
                "has zero impedance"
            )

        return 1.0 / z

    @property
    def shunt_admittance(self) -> complex:
        """
        Total shunt admittance.

            Y_shunt = jB
        """

        return complex(
            0.0,
            self.b
        )

    # =============================================================
    # OPERATIONAL STATE
    # =============================================================

    def trip(self):
        """
        Remove the branch from service.
        """

        self.in_service = False

    def close(self):
        """
        Return the branch to service.
        """

        self.in_service = True

    # =============================================================
    # STATUS
    # =============================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True if the branch is operational.
        """

        return self.in_service

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured branch information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "from_bus": self.from_bus.id,
            "to_bus": self.to_bus.id,
            "r": self.r,
            "x": self.x,
            "b": self.b,
            "tap": self.tap,
            "shift": self.shift,
            "rate_mva": self.rate_mva,
            "in_service": self.in_service,
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<Branch "
            f"id={self.id}, "
            f"{self.from_bus.id} -> {self.to_bus.id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"b={self.b:.6f}, "
            f"in_service={self.in_service}>"
        )
