# core/model/load.py

"""
GridForge Constant-Power Load Model
===================================

GridForge Model Layer V2

Defines the GridForge constant-power Load model.

Architecture
------------

A Load is a single-terminal electrical injection device.

    Load
      │
    Terminal
      │
      └──── network topology ──── Bus

The Load owns its physical Terminal.

The Terminal represents the Load's local physical electrical
connection point. The network layer is responsible for determining
and maintaining global electrical topology.

A Load may therefore exist in a disconnected state before network
assembly:

    Load
      │
    Terminal
      │
    endpoint = None

or may initially reference a local electrical endpoint:

    Load
      │
    Terminal
      │
    endpoint

The endpoint is not assumed by this model to be a concrete Bus.

Sign Convention
---------------

Internally, load demand is stored as positive consumption:

    p > 0
        Active-power consumption.

    q > 0
        Reactive-power consumption.

Through the Injection interface, the Load exposes network
injection:

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

- Stores constant active-power demand.
- Stores constant reactive-power demand.
- Owns one physical Terminal.
- Provides the local electrical endpoint.
- Provides compatibility access to a connected Bus.
- Implements the Injection interface.
- Provides network power injection.
- Validates load demand.
- Provides diagnostic information.

The Load model does NOT:

- Build global network topology.
- Register itself with the network.
- Modify Bus state.
- Build Y-bus.
- Perform power-flow calculations.
- Perform load-flow iterations.
- Calculate losses.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic simulation.
- Manage GUI objects.

Those responsibilities belong to the appropriate
network/solver/analysis/protection/simulation layers.

Terminal and Topology
---------------------

The Load owns one physical Terminal:

    self.terminal

The authoritative local physical connection is:

    self.terminal.endpoint

The endpoint may be:

- a Bus-like object;
- another Terminal;
- another network-supported endpoint.

For example:

    Bus ── Load

or:

    Bus ── Breaker ── Load

The Load does not need to know whether switching equipment exists
between the Load and the network.

The ``bus`` property is therefore only a compatibility/convenience
accessor derived from the Terminal.

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

The Load uses the generalized Terminal architecture and does not
assume that its local endpoint is necessarily a Bus.

Changes require evidence of a genuinely fundamental load-model
requirement that cannot be satisfied through the Injection, Terminal,
Shunt, or higher-level network/solver layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


# =====================================================================
# LOAD MODEL
# =====================================================================

class Load(ElectricalObject, Injection):
    """
    GridForge constant-power electrical load.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    bus : object, optional
        Initial electrical connection endpoint.

        This parameter name is retained for compatibility with the
        existing GridForge model/network interfaces.

        The value is passed to the Load's Terminal as its local
        endpoint. It is not required to be a concrete Bus.

        ``None`` creates a disconnected Load.

    p : float
        Active-power demand in per-unit.

        Stored internally as a positive consumption value.

    q : float
        Reactive-power demand in per-unit.

        Stored internally as a positive consumption value.

    name : str, optional
        Human-readable load name.

    Notes
    -----
    The Load owns its physical Terminal.

    The authoritative local connection is:

        self.terminal.endpoint

    The ``bus`` property is derived from the Terminal and exists for
    compatibility with existing GridForge interfaces.

    The Load does not directly modify global network topology.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        bus: Any = None,
        p: float = 0.0,
        q: float = 0.0,
        name: str = "",
    ) -> None:
        """
        Initialize a constant-power Load.

        The Load may be created without an electrical endpoint.
        Network assembly may establish the connection later.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # PHYSICAL TERMINAL
        # -------------------------------------------------------------
        #
        # The Load owns its Terminal.
        #
        # owner=self establishes local model ownership only.
        # It does not register the Terminal with the network.
        #
        self.terminal = Terminal(
            endpoint=bus,
            owner=self,
        )

        # -------------------------------------------------------------
        # LOAD DEMAND
        # -------------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        # -------------------------------------------------------------
        # VALIDATION
        # -------------------------------------------------------------

        self._validate_power()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_power(self) -> None:
        """
        Validate active and reactive load demand.

        Loads represent consumption, therefore both active and
        reactive demand are stored as finite, non-negative values.

        Reactive compensation is represented by Shunt models and is
        not encoded as negative load demand.
        """

        if not isfinite(self.p):
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be finite."
            )

        if self.p < 0.0:
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be >= 0."
            )

        if not isfinite(self.q):
            raise ValueError(
                f"Load '{self.id}': "
                "reactive power demand must be finite."
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
        Return the Load's network power injection.

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
        Return the Bus associated with this Load when available.

        Returns
        -------
        object or None
            Bus-like endpoint associated with the Load.

        Notes
        -----
        The authoritative local physical connection is:

            self.terminal.endpoint

        This property exists as a compatibility accessor.

        If the terminal is connected to another Terminal, the
        Terminal implementation resolves its Bus when possible.

        Global topology remains the responsibility of ``core/network``.
        """

        return self.terminal.bus

    # =================================================================
    # ENDPOINT ACCESS
    # =================================================================

    @property
    def endpoint(self):
        """
        Return the authoritative local electrical endpoint.

        Returns
        -------
        object or None
            The object referenced by ``terminal.endpoint``.
        """

        return self.terminal.endpoint

    @property
    def endpoint_id(self) -> str | None:
        """
        Return the identifier of the local endpoint.

        Returns
        -------
        str or None
            Endpoint identifier when connected.
        """

        return self.terminal.endpoint_id

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Load's Terminal has a local endpoint.
        """

        return self.terminal.is_connected

    # =================================================================
    # TERMINAL CONNECTION
    # =================================================================

    def connect(self, endpoint: Any) -> None:
        """
        Connect the Load's physical Terminal to an endpoint.

        This changes only the local Terminal reference.

        It does not:

        - register the Load with the network;
        - modify the network graph;
        - rebuild Y-bus;
        - perform a study.
        """

        self.terminal.connect(endpoint)

    def disconnect(self) -> None:
        """
        Disconnect the Load's physical Terminal locally.

        Global network topology is not modified by this operation.
        """

        self.terminal.disconnect()

    # =================================================================
    # POWER UPDATE
    # =================================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Update active and reactive load demand.

        Parameters
        ----------
        p : float
            Active-power demand in per-unit.

        q : float
            Reactive-power demand in per-unit.

        Notes
        -----
        Values use the Load's internal consumption-positive
        convention.

        Candidate values are fully validated before model state is
        modified.
        """

        p = float(p)
        q = float(q)

        # -------------------------------------------------------------
        # Validate candidate state before committing it.
        # -------------------------------------------------------------

        if not isfinite(p):
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be finite."
            )

        if p < 0.0:
            raise ValueError(
                f"Load '{self.id}': "
                "active power demand must be >= 0."
            )

        if not isfinite(q):
            raise ValueError(
                f"Load '{self.id}': "
                "reactive power demand must be finite."
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
        Return active-power demand in per-unit.
        """

        return self.p

    @property
    def reactive_power(self) -> float:
        """
        Return reactive-power demand in per-unit.
        """

        return self.q

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Load information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "load",

            "endpoint": self.endpoint_id,

            "bus": (
                self.bus.id
                if self.bus is not None
                else None
            ),

            "connected": self.is_connected,

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

        endpoint_id = self.endpoint_id

        return (
            f"<Load "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"p={self.p:.6f}, "
            f"q={self.q:.6f}>"
        )
