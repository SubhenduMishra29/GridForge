# core/model/load.py
"""
GridForge V2 Load Model
=======================

Author:
    Subhendu Mishra

A Load is a single-terminal electrical injection model.

Architecture
------------

    ElectricalObject
          +
      Injection
          |
          v
         Load
          |
          v
       Terminal
          |
          v
       Endpoint

The Load owns:

    - demand P/Q
    - one authoritative Terminal
    - operational state

The Load does NOT own:

    - Bus collections
    - network topology
    - SLD geometry
    - solver state
    - Y-bus construction
    - GUI state

Power convention
----------------

Load demand is stored internally as positive consumption:

    p > 0  -> active demand
    q > 0  -> reactive demand

The network injection convention is:

    P_injection = -p
    Q_injection = -q

Therefore:

    get_power() -> (-p, -q)

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Load(ElectricalObject, Injection):
    """
    Single-terminal electrical load.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    terminal:
        Optional existing Terminal.

    bus:
        Compatibility alias for assigning the terminal's endpoint/bus.

        This is deliberately not authoritative. The Terminal remains
        the authoritative connection interface.

    p:
        Active power demand in MW.

    q:
        Reactive power demand in MVAr.

    name:
        Human-readable load name.

    in_service:
        Operational state.
    """

    TYPE = "LOAD"

    def __init__(
        self,
        id: str,
        *,
        terminal: Terminal | None = None,
        bus: Any = None,
        p: float = 0.0,
        q: float = 0.0,
        name: str = "",
        in_service: bool = True,
    ) -> None:

        ElectricalObject.__init__(
            self,
            id=id,
            name=name,
        )

        self._terminal = (
            terminal
            if terminal is not None
            else Terminal(
                id=f"{id}:T1",
                owner=self,
                name=f"{name or id}:T1",
            )
        )

        if self._terminal.owner is None:
            self._terminal.owner = self

        elif self._terminal.owner is not self:
            raise ValueError(
                f"Terminal '{self._terminal.id}' is already "
                "owned by another object."
            )

        self._p = self._validate_power(
            p,
            "p",
        )

        self._q = self._validate_power(
            q,
            "q",
        )

        self._in_service = bool(
            in_service
        )

        # Compatibility construction path only.
        #
        # Terminal remains authoritative; Load never stores a
        # separate bus/topology state.
        if bus is not None:
            self.connect_terminal(bus)

        self.validate()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # TERMINAL
    # =================================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative Load terminal.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return all Load terminals.

        A Load has exactly one terminal.
        """

        return (self._terminal,)

    # =================================================================
    # COMPATIBILITY BUS ACCESS
    # =================================================================

    @property
    def bus(self) -> Any:
        """
        Return the terminal's connected bus/endpoint.

        This is a derived compatibility accessor.

        Load does not own bus state.
        """

        return self._terminal.bus

    @bus.setter
    def bus(self, value: Any) -> None:
        """
        Compatibility setter.

        The supplied value is routed through the terminal rather than
        being stored independently by Load.
        """

        self.connect_terminal(value)

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def is_connected(self) -> bool:
        """Return whether the Load terminal is connected."""

        return self._terminal.is_connected

    def connect_terminal(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the Load terminal to an endpoint.

        Terminal owns the actual connection state.
        """

        if endpoint is None:
            raise ValueError(
                "Load terminal endpoint cannot be None."
            )

        self._terminal.connect(endpoint)

    def disconnect_terminal(self) -> None:
        """
        Disconnect the Load terminal.

        The Load remains a valid disconnected model object.
        """

        self._terminal.disconnect()

    # =================================================================
    # POWER
    # =================================================================

    @property
    def p(self) -> float:
        """
        Return active power demand in MW.

        Positive means consumption.
        """

        return self._p

    @p.setter
    def p(self, value: float) -> None:
        self._p = self._validate_power(
            value,
            "p",
        )

    @property
    def q(self) -> float:
        """
        Return reactive power demand in MVAr.

        Positive means reactive consumption.
        """

        return self._q

    @q.setter
    def q(self, value: float) -> None:
        self._q = self._validate_power(
            value,
            "q",
        )

    @property
    def active_power_mw(self) -> float:
        """Return active demand in MW."""

        return self._p

    @property
    def reactive_power_mvar(self) -> float:
        """Return reactive demand in MVAr."""

        return self._q

    # =================================================================
    # INJECTION CONTRACT
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network injection (P, Q).

        Loads consume power, therefore their network injection is
        negative.

            P = -p
            Q = -q
        """

        return (
            -self._p,
            -self._q,
        )

    # =================================================================
    # OPERATIONAL STATE
    # =================================================================

    @property
    def in_service(self) -> bool:
        """Return operational state."""

        return self._in_service

    @in_service.setter
    def in_service(self, value: bool) -> None:
        self._in_service = bool(value)

    @property
    def is_in_service(self) -> bool:
        """Compatibility alias for in_service."""

        return self._in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return True when the Load is out of service."""

        return not self._in_service

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """Set operational state."""

        self._in_service = bool(value)

    def close(self) -> None:
        """Place the Load in service."""

        self._in_service = True

    def trip(self) -> None:
        """Remove the Load from service."""

        self._in_service = False

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Load-local parameters.

        Topology is deliberately not required for model validity.
        A Load may exist in a disconnected state.
        """

        self._p = self._validate_power(
            self._p,
            "p",
        )

        self._q = self._validate_power(
            self._q,
            "q",
        )

        if not isinstance(
            self._in_service,
            bool,
        ):
            raise ValueError(
                "in_service must be boolean."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Load model.
        """

        ElectricalObject.validate(
            self
        )

        if self._terminal is None:
            raise ValueError(
                f"Load '{self.id}' must have a terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Load '{self.id}' terminal ownership is invalid."
            )

        return True

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Load diagnostics.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal.id,

            "endpoint": (
                self._terminal.endpoint.id
                if self._terminal.endpoint is not None
                else None
            ),

            "bus": (
                self._terminal.bus.id
                if self._terminal.bus is not None
                else None
            ),

            "connected": self.is_connected,

            "p_mw": self._p,
            "q_mvar": self._q,

            "injection_p_mw": -self._p,
            "injection_q_mvar": -self._q,

            "in_service": self._in_service,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        endpoint_id = (
            self._terminal.endpoint.id
            if self._terminal.endpoint is not None
            else None
        )

        return (
            f"<Load "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"P={self._p:.6f} MW, "
            f"Q={self._q:.6f} MVAr, "
            f"in_service={self._in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_power(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a power quantity.

        Load demand is represented as a magnitude and therefore
        cannot be negative.
        """

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative for a Load."
            )

        return value


__all__ = [
    "Load",
]
