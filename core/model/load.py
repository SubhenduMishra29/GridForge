# ============================================================
# File: core/model/load.py
# GridForge V2 — Load Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Load Model
=========================

Authoritative single-terminal electrical load model.

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
          |
          v
       Network

The Load owns:

    - identity
    - active-power demand
    - reactive-power demand
    - operational state
    - exactly one authoritative Terminal

The Load does NOT own:

    - Network topology
    - Bus collections
    - Y-bus construction
    - solver state
    - SLD geometry
    - GUI state
    - global network mutation

Terminal Contract
-----------------

The Load owns one authoritative Terminal.

The Terminal owns endpoint state.

Canonical endpoint operations are:

    connect_terminal(endpoint)
        -> Terminal.attach(endpoint)

    disconnect_terminal()
        -> Terminal.detach()

The Load does not maintain a duplicate endpoint or bus state.

Power Convention
----------------

Load demand is stored as positive consumption:

    p > 0  -> active consumption
    q > 0  -> reactive consumption

GridForge network injection convention is:

    P_injection = -p
    Q_injection = -q

Therefore:

    get_power() -> (-p, -q)

Operational State
-----------------

A Load may exist in a disconnected state.

Terminal connectivity and operational service state
are independent concepts.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Load(ElectricalObject, Injection):
    """
    Single-terminal electrical load.

    Positive p and q represent electrical demand.

    Network injection is the negative of stored demand.
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
        """
        Construct a Load.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        terminal:
            Optional pre-created authoritative Terminal.

        bus:
            Compatibility alias for the initial electrical
            endpoint. It is never stored independently.

        p:
            Active power demand in MW.

        q:
            Reactive power demand in MVAr.

        name:
            Human-readable load name.

        in_service:
            Initial operational state.

        Notes
        -----
        If an externally supplied Terminal is used, it must already
        belong to this Load. Terminal ownership is immutable through
        the public Terminal API.
        """

        ElectricalObject.__init__(
            self,
            id=id,
            name=name,
        )

        # ========================================================
        # AUTHORITATIVE TERMINAL
        # ========================================================

        if terminal is None:
            self._terminal = Terminal(
                owner=self,
                role="terminal",
            )
        else:
            if not isinstance(
                terminal,
                Terminal,
            ):
                raise TypeError(
                    "terminal must be a Terminal."
                )

            if terminal.owner is not self:
                raise ValueError(
                    "Terminal must already be owned by this Load."
                )

            if terminal.role != "terminal":
                raise ValueError(
                    "Load terminal role must be 'terminal'."
                )

            self._terminal = terminal

        # ========================================================
        # POWER STATE
        # ========================================================

        self._p = self._validate_power(
            p,
            "p",
        )

        self._q = self._validate_power(
            q,
            "q",
        )

        # ========================================================
        # OPERATIONAL STATE
        # ========================================================

        self._in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        # ========================================================
        # INITIAL ENDPOINT
        # ========================================================

        if bus is not None:
            self.connect_terminal(
                bus
            )

        # ========================================================
        # MODEL VALIDATION
        # ========================================================

        self.validate()

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # ============================================================
    # TERMINAL
    # ============================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the authoritative Load Terminal.

        The returned Terminal is the canonical connection object.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return all Load terminals.

        A Load has exactly one terminal.
        """

        return (
            self._terminal,
        )

    # ============================================================
    # ENDPOINT / BUS COMPATIBILITY
    # ============================================================

    @property
    def endpoint(self) -> Any | None:
        """
        Return the authoritative Terminal endpoint.

        Endpoint state is never duplicated in Load.
        """

        return self._terminal.endpoint

    @property
    def bus(self) -> Any | None:
        """
        Compatibility accessor for the connected endpoint.

        This property is derived exclusively from Terminal.
        """

        return self._terminal.endpoint

    @bus.setter
    def bus(
        self,
        value: Any,
    ) -> None:
        """
        Compatibility setter.

        The value is routed through the canonical Terminal API.
        """

        self.connect_terminal(
            value
        )

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    @property
    def is_connected(self) -> bool:
        """
        Return whether the Load Terminal has an endpoint.
        """

        return self._terminal.is_connected

    def connect_terminal(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach the Load Terminal to an endpoint.

        Terminal owns the actual endpoint state.

        This operation does not modify Network topology.
        """

        if endpoint is None:
            raise ValueError(
                "Load terminal endpoint cannot be None."
            )

        self._terminal.attach(
            endpoint
        )

    def disconnect_terminal(self) -> None:
        """
        Detach the Load Terminal.

        The Load remains a valid disconnected model object.
        """

        self._terminal.detach()

    # ============================================================
    # POWER DEMAND
    # ============================================================

    @property
    def p(self) -> float:
        """
        Return active power demand in MW.

        Positive means consumption.
        """

        return self._p

    @p.setter
    def p(
        self,
        value: float,
    ) -> None:
        self._p = self._validate_power(
            value,
            "p",
        )

    @property
    def q(self) -> float:
        """
        Return reactive power demand in MVAr.

        Positive means consumption.
        """

        return self._q

    @q.setter
    def q(
        self,
        value: float,
    ) -> None:
        self._q = self._validate_power(
            value,
            "q",
        )

    @property
    def active_power_mw(self) -> float:
        """Return active power demand in MW."""

        return self._p

    @property
    def reactive_power_mvar(self) -> float:
        """Return reactive power demand in MVAr."""

        return self._q

    # ============================================================
    # INJECTION CONTRACT
    # ============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network injection (P, Q).

        Load demand is represented internally as positive
        consumption, therefore network injection is negative.

            P_injection = -p
            Q_injection = -q

        The existing Load semantics are intentionally preserved.
        """

        return (
            -self._p,
            -self._q,
        )

    # ============================================================
    # OPERATIONAL STATE
    # ============================================================

    @property
    def in_service(self) -> bool:
        """Return the operational service state."""

        return self._in_service

    @in_service.setter
    def in_service(
        self,
        value: bool,
    ) -> None:
        self._in_service = self._validate_bool(
            value,
            "in_service",
        )

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
        """Set the operational service state."""

        self._in_service = self._validate_bool(
            value,
            "in_service",
        )

    def close(self) -> None:
        """
        Place the Load in service.

        This changes operational state only.
        """

        self._in_service = True

    def trip(self) -> None:
        """
        Take the Load out of service.

        This changes operational state only.
        """

        self._in_service = False

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Load-local engineering parameters.

        A disconnected Load remains a valid model object, so
        endpoint presence is not required here.
        """

        self._p = self._validate_power(
            self._p,
            "p",
        )

        self._q = self._validate_power(
            self._q,
            "q",
        )

        self._in_service = self._validate_bool(
            self._in_service,
            "in_service",
        )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Load model.

        Terminal ownership and Terminal-local invariants are
        validated independently from Network topology.
        """

        ElectricalObject.validate(
            self
        )

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Load terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Load '{self.id}' terminal owner is invalid."
            )

        if self._terminal.role != "terminal":
            raise ValueError(
                "Load terminal role must be 'terminal'."
            )

        self._terminal.validate()

        return True

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Load diagnostics.
        """

        endpoint = self._terminal.endpoint

        endpoint_id = (
            getattr(
                endpoint,
                "id",
                None,
            )
            if endpoint is not None
            else None
        )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal,
            "terminal_role": self._terminal.role,

            "endpoint": endpoint_id,
            "bus": endpoint_id,
            "connected":
                self._terminal.is_connected,

            "p_mw": self._p,
            "q_mvar": self._q,

            "injection_p_mw": -self._p,
            "injection_q_mvar": -self._q,

            "in_service": self._in_service,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        endpoint = self._terminal.endpoint

        endpoint_id = (
            getattr(
                endpoint,
                "id",
                None,
            )
            if endpoint is not None
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

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_power(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a Load demand value.

        Demand is represented as a non-negative magnitude.
        """

        try:
            numeric = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(
            numeric
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        if numeric < 0.0:
            raise ValueError(
                f"{name} cannot be negative for a Load."
            )

        return numeric

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a strict boolean.

        Implicit truth-value coercion is deliberately avoided.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Load",
]
