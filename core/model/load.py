# core/model/load.py
"""
GridForge V2 Load Model
=======================

Author:
    Subhendu Mishra

A Load is a single-terminal static electrical demand model.

Architecture
------------

    Load
      │
    Terminal
      │
      └── endpoint ── network topology ── Bus / network element

The Load owns exactly one physical Terminal.

The Terminal is the authoritative local connection reference.
Global topology belongs to the Core network/application layer.

Electrical model
----------------

Internally:

    p >= 0
        active-power consumption

    q >= 0
        reactive-power consumption

Through the Injection interface:

    P_injection = -p
    Q_injection = -q

Thus:

    positive Load P/Q
        = consumption

    negative network injection
        = consumption from the network

The Load is a static constant-power model.

This class does NOT:

    - own global topology
    - add itself to a Grid
    - modify Bus state
    - build Y-bus
    - solve load flow
    - calculate losses
    - perform short-circuit studies
    - perform protection studies
    - perform dynamic simulation
    - manage SLD state
    - manage GUI state

Dynamic load models such as ZIP, induction-motor
components, voltage/frequency-dependent models, etc.,
belong to the future dynamic/simulation architecture.

Reactive compensation is represented by Shunt models,
not by negative Load demand.

Units
-----

    p : per-unit
    q : per-unit

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Load(ElectricalObject, Injection):
    """
    Static constant-power electrical load.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint:
        Initial electrical endpoint.

        May be None when the Load is created before network
        connectivity is established.

        The parameter is also accepted as ``bus`` for compatibility
        with existing GridForge callers.

    p:
        Active-power demand in per-unit.

    q:
        Reactive-power demand in per-unit.

    name:
        Human-readable Load name.

    Notes
    -----
    The Load owns one Terminal:

        self.terminal

    The authoritative local connection is:

        self.terminal.endpoint

    The ``bus`` property is derived from the Terminal and is only a
    compatibility accessor.
    """

    TYPE = "LOAD"

    def __init__(
        self,
        id: str,
        endpoint: Any = None,
        *,
        p: float = 0.0,
        q: float = 0.0,
        name: str = "",
        bus: Any = None,
    ) -> None:

        # ---------------------------------------------------------
        # Backward compatibility
        # ---------------------------------------------------------
        #
        # Existing GridForge code may still construct:
        #
        #     Load(..., bus=bus)
        #
        # The new architectural terminology is endpoint.
        #
        if endpoint is not None and bus is not None:
            if endpoint is not bus:
                raise ValueError(
                    f"Load '{id}' received both 'endpoint' and "
                    "'bus' with different objects."
                )

        if endpoint is None:
            endpoint = bus

        # ---------------------------------------------------------
        # Base object
        # ---------------------------------------------------------

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Physical terminal
        # ---------------------------------------------------------
        #
        # Local ownership only.
        #
        # This does NOT register the Load with the network.
        #

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # ---------------------------------------------------------
        # Static demand
        # ---------------------------------------------------------

        self.p = self._validate_power_value(
            p,
            "p",
        )

        self.q = self._validate_power_value(
            q,
            "q",
        )

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return the canonical GridForge element type."""

        return self.TYPE

    # =============================================================
    # VALIDATION
    # =============================================================

    @staticmethod
    def _validate_power_value(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a Load consumption value.

        Load P and Q are internally represented as
        finite non-negative demand values.
        """

        value = float(value)

        if not isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        if value < 0.0:
            raise ValueError(
                f"{name} must be greater than or equal to zero."
            )

        return value

    def validate_parameters(self) -> bool:
        """
        Validate Load-local electrical parameters.

        This validates only the Load model.

        It does not validate global network topology.
        """

        self.p = self._validate_power_value(
            self.p,
            "p",
        )

        self.q = self._validate_power_value(
            self.q,
            "q",
        )

        return True

    def validate(self) -> bool:
        """
        Public local validation entry point.

        Network topology and study validity are handled by
        the appropriate Core layers.
        """

        return self.validate_parameters()

    # Backward-compatible private validation method.
    def _validate_power(self) -> None:
        """
        Compatibility wrapper for existing callers.

        New code should use validate_parameters().
        """

        self.validate_parameters()

    # =============================================================
    # INJECTION
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network power injection.

        Returns
        -------
        tuple[float, float]
            ``(-p, -q)`` in per-unit.

        Example
        -------
        A Load with:

            p = 0.50
            q = 0.20

        produces:

            (-0.50, -0.20)

        as network injection.
        """

        return (
            -self.p,
            -self.q,
        )

    @property
    def p_injection(self) -> float:
        """Return active network injection."""

        return -self.p

    @property
    def q_injection(self) -> float:
        """Return reactive network injection."""

        return -self.q

    # =============================================================
    # POWER PROPERTIES
    # =============================================================

    @property
    def active_power(self) -> float:
        """Return active-power consumption in per-unit."""

        return self.p

    @property
    def reactive_power(self) -> float:
        """Return reactive-power consumption in per-unit."""

        return self.q

    # =============================================================
    # POWER UPDATE
    # =============================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set active and reactive power demand.

        Candidate values are completely validated before
        modifying model state.
        """

        p = self._validate_power_value(
            p,
            "p",
        )

        q = self._validate_power_value(
            q,
            "q",
        )

        self.p = p
        self.q = q

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """Set active-power demand."""

        self.p = self._validate_power_value(
            p,
            "p",
        )

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """Set reactive-power demand."""

        self.q = self._validate_power_value(
            q,
            "q",
        )

    # =============================================================
    # TERMINAL
    # =============================================================

    @property
    def terminals(self) -> tuple[Terminal]:
        """
        Return the Load's authoritative physical terminal.
        """

        return (
            self.terminal,
        )

    @property
    def endpoint(self):
        """
        Return the authoritative local electrical endpoint.
        """

        return self.terminal.endpoint

    @property
    def endpoint_id(self) -> str | None:
        """
        Return the local endpoint identifier when available.
        """

        return self.terminal.endpoint_id

    @property
    def bus(self):
        """
        Return the bus derived from the terminal.

        This is a compatibility accessor.

        The Load does not own a Bus reference independently.
        """

        return self.terminal.bus

    @property
    def bus_id(self) -> str | None:
        """Return the derived Bus identifier when available."""

        bus = self.bus

        if bus is None:
            return None

        return getattr(
            bus,
            "id",
            None,
        )

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Load terminal has an endpoint.
        """

        return self.terminal.is_connected

    # =============================================================
    # TERMINAL CONNECTION
    # =============================================================

    def connect(
        self,
        endpoint: Any,
    ) -> None:
        """
        Assign the Load's physical endpoint.

        This modifies only local Terminal state.

        It does NOT:

            - register the Load with the network
            - alter a Bus
            - modify global topology
            - rebuild Y-bus
            - execute a study
        """

        self.terminal.connect(
            endpoint
        )

    def disconnect(self) -> None:
        """
        Remove the Load's local physical endpoint.

        Global topology remains the responsibility of the
        network/application layer.
        """

        self.terminal.disconnect()

    # Explicit aliases improve readability where callers want
    # to distinguish endpoint operations from future service-state
    # operations.

    def connect_terminal(
        self,
        endpoint: Any,
    ) -> None:
        """Explicit alias for connect()."""

        self.connect(endpoint)

    def disconnect_terminal(self) -> None:
        """Explicit alias for disconnect()."""

        self.disconnect()

    # =============================================================
    # SERVICE STATE
    # =============================================================
    #
    # A Load is not treated as electrically disconnected merely
    # because it is out of service.
    #
    # Terminal connectivity and operational state are separate
    # concepts.
    #

    @property
    def in_service(self) -> bool:
        """
        Return whether the Load is operationally in service.

        A Load created by this model is initially in service.
        """

        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = bool(value)

    @property
    def is_in_service(self) -> bool:
        """Return operational service state."""

        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the Load is out of service."""

        return not self._in_service

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set operational service state.

        This does not modify terminal topology.
        """

        self._in_service = bool(value)

    def trip(self) -> None:
        """Take the Load out of service."""

        self._in_service = False

    def close(self) -> None:
        """Place the Load in service."""

        self._in_service = True

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Load diagnostics.
        """

        bus = self.bus

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "p": self.p,
            "q": self.q,

            "p_injection": self.p_injection,
            "q_injection": self.q_injection,

            "endpoint": self.endpoint_id,

            "bus": (
                getattr(bus, "id", None)
                if bus is not None
                else None
            ),

            "connected": self.is_connected,
            "in_service": self.is_in_service,

            "terminal": self.terminal.summary(),
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<Load "
            f"id={self.id}, "
            f"endpoint={self.endpoint_id}, "
            f"p={self.p:.6f}, "
            f"q={self.q:.6f}, "
            f"in_service={self.is_in_service}>"
        )
