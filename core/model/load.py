"""
load.py

Defines the Load model.

A Load represents a constant-power consumption device
connected to a Bus.

Sign convention
---------------
Internally, load demand is stored as positive values:

    p > 0  -> active power consumption
    q > 0  -> reactive power consumption

Through the Injection interface, the load reports:

    -P, -Q

because negative injection represents consumption from
the electrical network.

Responsibilities
----------------
This class:

- Stores load electrical data.
- Maintains its Bus connection through Terminal.
- Implements the Injection interface.
- Provides load power information.

This class does NOT:

- Modify Bus state.
- Perform power-flow calculations.
- Build Ybus.
- Perform load-flow iteration.
- Handle contingencies.
- Perform protection calculations.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Load(ElectricalObject, Injection):
    """
    Constant-power load model.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    bus : Bus
        Bus to which the load is connected.

    p : float
        Active power demand.

        Stored as a positive consumption value.

    q : float
        Reactive power demand.

        Stored as a positive consumption value.

    name : str, optional
        Human-readable name.
    """

    def __init__(
        self,
        id: str,
        bus,
        p: float,
        q: float,
        name: str = ""
    ):
        super().__init__(
            id=id,
            name=name
        )

        # ---------------------------------------------------------
        # Electrical connection
        # ---------------------------------------------------------

        self.terminal = Terminal(bus)

        # ---------------------------------------------------------
        # Load demand
        #
        # Internally:
        #
        #     +P = consumption
        #     +Q = consumption
        #
        # Injection interface converts these to negative values.
        # ---------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        self._validate_power()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_power(self):
        """
        Validate load power values.

        Loads represent consumption, therefore negative demand
        values are rejected at the model level.
        """

        if self.p < 0:
            raise ValueError(
                f"Load {self.id}: active power demand must be >= 0"
            )

        if self.q < 0:
            raise ValueError(
                f"Load {self.id}: reactive power demand must be >= 0"
            )

    # =============================================================
    # INJECTION INTERFACE
    # =============================================================

    def get_power(self):
        """
        Return network injection represented by this load.

        Returns
        -------
        tuple[float, float]
            (-P, -Q)

        Sign convention
        ----------------
        Positive values represent injection into the network.

        Therefore a consuming load produces negative injection.
        """

        return -self.p, -self.q

    # =============================================================
    # CONNECTION
    # =============================================================

    @property
    def bus(self):
        """
        Return the Bus connected to this load.
        """

        return self.terminal.bus

    # =============================================================
    # POWER UPDATE
    # =============================================================

    def set_power(
        self,
        p: float,
        q: float
    ):
        """
        Update the load demand.

        Parameters
        ----------
        p : float
            Active power demand.

        q : float
            Reactive power demand.
        """

        p = float(p)
        q = float(q)

        if p < 0:
            raise ValueError(
                f"Load {self.id}: active power demand must be >= 0"
            )

        if q < 0:
            raise ValueError(
                f"Load {self.id}: reactive power demand must be >= 0"
            )

        self.p = p
        self.q = q

    # =============================================================
    # PROPERTIES
    # =============================================================

    @property
    def active_power(self) -> float:
        """
        Return active power demand.
        """

        return self.p

    @property
    def reactive_power(self) -> float:
        """
        Return reactive power demand.
        """

        return self.q

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self):
        """
        Return diagnostic information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "bus": self.bus.id,
            "P_demand": self.p,
            "Q_demand": self.q,
            "P_injection": -self.p,
            "Q_injection": -self.q
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self):
        return (
            f"<Load "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.4f}, "
            f"Q={self.q:.4f}>"
        )
