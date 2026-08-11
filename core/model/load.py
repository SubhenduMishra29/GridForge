```python
# core/model/load.py

"""
GridForge Constant-Power Load Model
===================================

GridForge Model Layer V2

Defines the GridForge constant-power Load model.

Architecture
------------
Load is an electrical injection device connected to a Bus through
a Terminal.

The Load model represents constant active and reactive power demand.

Sign Convention
---------------
Internally, load demand is stored as positive consumption:

    p > 0
        Active-power consumption.

    q > 0
        Reactive-power consumption.

Through the Injection interface, the load exposes network injection:

    get_power() -> (-P, -Q)

Therefore:

    positive network injection
        = power supplied to the network

    negative network injection
        = power consumed from the network

For a Load:

    P_injection = -p
    Q_injection = -q

Responsibilities
----------------
The Load model:

- Stores load electrical data.
- Maintains its Bus connection through Terminal.
- Implements the Injection interface.
- Provides network power injection.
- Provides load-demand properties.
- Validates load demand.
- Provides diagnostic information.

The Load model does NOT:

- Modify Bus voltage state.
- Build Y-bus.
- Perform power-flow calculations.
- Perform load-flow iterations.
- Calculate losses.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic simulation.
- Manage GUI objects.

Those responsibilities belong to the appropriate
network/solver/analysis/simulation layers.

Modeling Boundary
-----------------
A Load represents electrical demand.

Reactive compensation devices, including capacitive or inductive
shunts, belong to the Shunt model rather than being represented as
negative load demand.

Therefore this model intentionally requires:

    p >= 0
    q >= 0

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental load-model
requirement that cannot be satisfied through the Injection,
Terminal, Shunt, or higher-level network/solver layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


# =====================================================================
# LOAD MODEL
# =====================================================================

class Load(ElectricalObject, Injection):
    """
    Constant-power electrical load.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    bus :
        GridForge Bus to which the load is connected.

    p : float
        Active-power demand.

        Stored internally as a positive consumption value.

    q : float
        Reactive-power demand.

        Stored internally as a positive consumption value.

    name : str, optional
        Human-readable load name.

    Notes
    -----
    The Load does not directly modify its connected Bus.

    Its electrical contribution is obtained through the Injection
    interface and consumed by the appropriate network/solver layer.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        bus,
        p: float,
        q: float,
        name: str = "",
    ) -> None:
        """
        Initialize a constant-power load.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Electrical connection
        # -------------------------------------------------------------

        self.terminal = Terminal(bus)

        # -------------------------------------------------------------
        # Load demand
        # -------------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        # -------------------------------------------------------------
        # Validate complete load state
        # -------------------------------------------------------------

        self._validate_power()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_power(self) -> None:
        """
        Validate load demand.

        Loads represent consumption, therefore active and reactive
        demand must be finite and non-negative.

        Negative reactive demand is deliberately not accepted here.
        Capacitive/inductive compensation belongs to the Shunt model.
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

    # =================================================================
    # INJECTION INTERFACE
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return the load's network power injection.

        Returns
        -------
        tuple[float, float]
            ``(-P, -Q)`` in per-unit.

        Sign convention
        ----------------
        Positive values represent injection into the network.

        Negative values represent consumption from the network.

        Therefore a positive load demand is returned as a negative
        network injection.
        """

        return (
            -self.p,
            -self.q,
        )

    # =================================================================
    # CONNECTION
    # =================================================================

    @property
    def bus(self):
        """
        Return the Bus connected to this load.
        """

        return self.terminal.bus

    # =================================================================
    # POWER UPDATE
    # =================================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Update load active and reactive power demand.

        Parameters
        ----------
        p : float
            Active-power demand.

        q : float
            Reactive-power demand.

        Notes
        -----
        Both values use the load's internal
        consumption-positive convention.
        """

        p = float(p)
        q = float(q)

        # -------------------------------------------------------------
        # Validate candidate values before modifying model state.
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Commit validated state.
        # -------------------------------------------------------------

        self.p = p
        self.q = q

    # =================================================================
    # POWER PROPERTIES
    # =================================================================

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

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured load information.
        """

        P_injection, Q_injection = self.get_power()

        return {
            "id": self.id,
            "name": self.name,
            "type": "load",
            "bus": self.bus.id,
            "P_demand": self.p,
            "Q_demand": self.q,
            "P_injection": P_injection,
            "Q_injection": Q_injection,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Load "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}>"
        )
```
