```python
"""
GridForge Constant-Power Load Model
===================================

GridForge Model Layer V2

Defines the GridForge constant-power Load model.

Architecture
------------
Load is an electrical injection device with a physical Terminal.

The Load owns its Terminal:

    Load
      │
    Terminal
      │
      └──── network topology ──── Bus

The Terminal represents the Load's physical connection point.

The network layer is responsible for determining how that terminal is
connected within the global electrical topology.

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
- Owns its physical Terminal.
- Provides access to its connected Bus when available.
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
- Manage network topology.
- Manage GUI objects.

Those responsibilities belong to the appropriate
network/solver/analysis/protection/simulation layers.

Terminal and Topology
---------------------
The Load owns one physical Terminal:

    self.terminal

The Terminal may be connected directly to a Bus or participate in a
network topology containing switching equipment.

For example:

    Bus ── Load

or:

    Bus ── Breaker ── Load

The Load itself does not need to know whether a breaker or other
switching element exists between the Load and the Bus.

The ``bus`` property is therefore a compatibility/convenience
interface derived from the Terminal.

Modeling Boundary
-----------------
A Load represents electrical demand.

Reactive compensation devices, including capacitive or inductive
shunts, belong to the Shunt model rather than being represented as
negative load demand.

Therefore this model intentionally requires:

    p >= 0
    q >= 0

Units
-----
    p : per-unit
    q : per-unit

GridForge V2 Status
-------------------
This module is part of the GridForge Model Layer V2 baseline.

The Terminal ownership update is required by the generalized physical
connection architecture.

Changes require evidence of a genuinely fundamental load-model
requirement that cannot be satisfied through the Injection, Terminal,
Shunt, or higher-level network/solver layers.

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
        Initial GridForge electrical connection endpoint.

        Normally this is a Bus. The network layer may subsequently
        establish topology involving switching equipment.

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
    The Load owns its physical Terminal.

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
        #
        # The Load owns the physical Terminal.
        #
        # ``owner=self`` establishes the local equipment ownership
        # relationship without registering anything with the network.
        #
        self.terminal = Terminal(
            endpoint=bus,
            owner=self,
        )

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
        Return the Bus associated with this Load.

        This is a compatibility/convenience property derived from the
        Load's Terminal.

        Returns
        -------
        object or None
            Connected Bus-like endpoint when available.

        Notes
        -----
        The authoritative local physical connection is:

            self.terminal

        Global topology remains owned by ``core/network``.
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

        Candidate values are validated before model state is modified.
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

        return {
            "id": self.id,
            "name": self.name,
            "type": "load",
            "bus": (
                self.bus.id
                if self.bus is not None
                else None
            ),
            "terminal": self.terminal.summary(),
            "p": self.p,
            "q": self.q,
            "p_injection": -self.p,
            "q_injection": -self.q,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        bus_id = (
            self.bus.id
            if self.bus is not None
            else None
        )

        return (
            f"<Load "
            f"id={self.id}, "
            f"bus={bus_id}, "
            f"p={self.p:.6f}, "
            f"q={self.q:.6f}>"
        )
```

This preserves the existing `Load` electrical semantics while changing only the connection ownership required by the new Terminal architecture. The original model already used `Terminal`, `load.bus`, `set_power()`, and the `(-P,-Q)` injection contract, so those interfaces remain intact.
**Status after this revision:**

* `bus.py` — **FROZEN**
* `load.py` — **FINAL CANDIDATE**
* `terminal.py` — **FINAL CANDIDATE**
* `branch.py` / `line.py` / `transformer.py` — need compatibility verification
* `breaker.py` — revise against the finalized Terminal contract
