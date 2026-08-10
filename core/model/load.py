"""
GridForge Load Model
====================

File:
    core/model/load.py

Defines the constant-power Load model.

Sign Convention
---------------

Internally, load demand is stored as positive consumption:

    p > 0
        Active power consumption.

    q > 0
        Reactive power consumption.

Through the Injection interface:

    get_power() -> (-P, -Q)

because negative network injection represents consumption.

Responsibilities
----------------
This class:

    - Stores load electrical data.
    - Maintains its Bus connection through Terminal.
    - Implements the Injection interface.
    - Provides load power information.
    - Validates load demand.

This class does NOT:

    - Modify Bus state.
    - Build Ybus.
    - Perform power-flow calculations.
    - Perform load-flow iteration.
    - Handle contingencies.
    - Perform protection calculations.
    - Perform dynamic simulation.

Those responsibilities belong to the appropriate
network/solver/analysis/simulation layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Load(ElectricalObject, Injection):
    """
    Constant-power electrical load.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    bus :
        Bus to which the load is connected.

    p : float
        Active-power demand.

        Stored internally as a positive consumption value.

    q : float
        Reactive-power demand.

        Stored internally as a positive consumption value.

    name : str, optional
        Human-readable load name.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        id: str,
        bus,
        p: float,
        q: float,
        name: str = "",
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Electrical connection
        # ---------------------------------------------------------

        self.terminal = Terminal(bus)

        # ---------------------------------------------------------
        # Load demand
        # ---------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        self._validate_power()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_power(self) -> None:
        """
        Validate load demand.

        Loads represent consumption, therefore negative or
        non-finite demand values are rejected at the model level.
        """

        if not isfinite(self.p):
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be finite."
            )

        if not isfinite(self.q):
            raise ValueError(
                f"Load '{self.id}': "
                "reactive power demand must be finite."
            )

        if self.p < 0.0:
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be >= 0."
            )

        if self.q < 0.0:
            raise ValueError(
                f"Load '{self.id}': "
                "reactive power demand must be >= 0."
            )

    # =============================================================
    # INJECTION INTERFACE
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return the load's network injection.

        Returns
        -------
        tuple[float, float]
            ``(-P, -Q)``

        Sign convention
        ----------------
        +P, +Q -> injection into network

        -P, -Q -> consumption from network
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
        q: float,
    ) -> None:
        """
        Update load demand.

        Parameters
        ----------
        p : float
            Active-power demand.

        q : float
            Reactive-power demand.
        """

        p = float(p)
        q = float(q)

        if not isfinite(p):
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be finite."
            )

        if not isfinite(q):
            raise ValueError(
                f"Load '{self.id}': "
                "reactive power demand must be finite."
            )

        if p < 0.0:
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be >= 0."
            )

        if q < 0.0:
            raise ValueError(
                f"Load '{self.id}': "
                "reactive power demand must be >= 0."
            )

        self.p = p
        self.q = q

    # =============================================================
    # POWER PROPERTIES
    # =============================================================

    @property
    def active_power(self) -> float:
        """
        Return active-power demand.
        """

        return self.p

    @property
    def reactive_power(self) -> float:
        """
        Return reactive-power demand.
        """

        return self.q

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured diagnostic information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "bus": self.bus.id,
            "P_demand": self.p,
            "Q_demand": self.q,
            "P_injection": -self.p,
            "Q_injection": -self.q,
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<Load "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}>"
        )
