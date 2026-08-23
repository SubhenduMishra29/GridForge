# core/model/generator.py
"""
GridForge V2 Generator Model
============================

Author:
    Subhendu Mishra

A Generator is an electrical power-injection element.

Architecture
------------

    ElectricalObject
          +
      Injection
          |
          v
      Generator
          |
          v
       Terminal
          |
          v
    Terminal.endpoint

The Generator owns:

    - generator identity
    - active/reactive power state
    - voltage setpoint
    - reactive-power limits
    - one authoritative Terminal
    - operational state
    - optional plugin references

The Generator does NOT own:

    - Network registration
    - global topology
    - Bus state
    - Y-Bus construction
    - power-flow solving
    - fault analysis
    - protection
    - dynamics
    - UI/SLD state

The ``endpoint`` property is derived from Terminal state.

The ``bus`` property is retained only as a compatibility accessor.
It is never authoritative.

Power convention
----------------

Generator injection into the electrical network is:

    P > 0  -> active power injection
    Q > 0  -> reactive power injection

Therefore:

    get_power() -> (P, Q)

Reactive-power limits
---------------------

The Generator may locally enforce:

    Qmin <= Q <= Qmax

PV/PQ operating-mode decisions belong to the analysis/control layer,
not to this model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Generator(ElectricalObject, Injection):
    """
    Controllable electrical generator model.

    A Generator may exist before being connected to a network.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint:
        Initial electrical endpoint. May be None.

    p:
        Active power injection.

    q:
        Reactive power injection.

    V_setpoint:
        Generator voltage setpoint in per-unit.

    q_limits:
        Tuple ``(Qmin, Qmax)``.

    name:
        Human-readable generator name.

    bus:
        Backward-compatible alias for endpoint.

    in_service:
        Initial operational state.
    """

    TYPE = "GENERATOR"

    def __init__(
        self,
        id: str,
        endpoint: Any = None,
        p: float = 0.0,
        q: float = 0.0,
        V_setpoint: float = 1.0,
        q_limits: tuple[float, float] = (
            -float("inf"),
            float("inf"),
        ),
        name: str = "",
        *,
        bus: Any = None,
        in_service: bool = True,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Endpoint / compatibility handling
        # -------------------------------------------------------------

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Generator '{self.id}' received both "
                "'endpoint' and 'bus' with different values."
            )

        if endpoint is None:
            endpoint = bus

        # -------------------------------------------------------------
        # Electrical state
        # -------------------------------------------------------------

        self.p = self._validate_finite(
            p,
            "p",
        )

        self.q = self._validate_finite(
            q,
            "q",
        )

        self.V_setpoint = self._validate_positive(
            V_setpoint,
            "V_setpoint",
        )

        self.q_min, self.q_max = self._validate_q_limits(
            q_limits
        )

        # -------------------------------------------------------------
        # Authoritative physical connection
        # -------------------------------------------------------------

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # -------------------------------------------------------------
        # Operational state
        # -------------------------------------------------------------

        self.in_service = bool(
            in_service
        )

        # -------------------------------------------------------------
        # Optional plugin references
        # -------------------------------------------------------------

        self._plugins: dict[str, Any] = {}

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
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return all Generator terminals.

        Generator has exactly one electrical terminal.
        """

        return (
            self.terminal,
        )

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def endpoint(self) -> Any:
        """
        Return the authoritative physical endpoint.

        Terminal.endpoint is the source of truth.
        """

        return self.terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor for the terminal bus.

        This is derived state and is not authoritative.
        """

        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return True when the Generator terminal is connected."""

        return self.terminal.is_connected

    def connect(
        self,
        endpoint: Any,
    ) -> None:
        """Connect the Generator terminal to an endpoint."""

        if endpoint is None:
            raise ValueError(
                f"Generator '{self.id}' endpoint cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect(self) -> None:
        """Disconnect the Generator terminal."""

        self.terminal.disconnect()

    # =================================================================
    # INJECTION CONTRACT
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network power injection.

        Positive values represent injection into the network.
        """

        if not self.in_service:
            return 0.0, 0.0

        return (
            self.p,
            self.q,
        )

    # =================================================================
    # POWER CONTROL
    # =================================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """Set active and reactive power."""

        self.p = self._validate_finite(
            p,
            "p",
        )

        self.q = self._validate_finite(
            q,
            "q",
        )

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """Set active power injection."""

        self.p = self._validate_finite(
            p,
            "p",
        )

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """Set reactive power injection."""

        self.q = self._validate_finite(
            q,
            "q",
        )

    @property
    def active_power(self) -> float:
        """Return active power injection."""

        return self.p

    @property
    def reactive_power(self) -> float:
        """Return reactive power injection."""

        return self.q

    # =================================================================
    # VOLTAGE CONTROL
    # =================================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float,
    ) -> None:
        """Set generator voltage setpoint."""

        self.V_setpoint = self._validate_positive(
            V_setpoint,
            "V_setpoint",
        )

    # =================================================================
    # REACTIVE POWER LIMITS
    # =================================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """Return ``(Qmin, Qmax)``."""

        return (
            self.q_min,
            self.q_max,
        )

    def set_q_limits(
        self,
        q_min: float,
        q_max: float,
    ) -> None:
        """Set generator reactive-power limits."""

        self.q_min, self.q_max = self._validate_q_limits(
            (
                q_min,
                q_max,
            )
        )

    def q_limit_status(
        self,
        tolerance: float = 1e-6,
    ) -> str:
        """
        Return current reactive-power limit status.

        Returns
        -------
        str
            ``LOW``, ``HIGH`` or ``NORMAL``.
        """

        tolerance = self._validate_non_negative(
            tolerance,
            "tolerance",
        )

        if self.q < self.q_min - tolerance:
            return "LOW"

        if self.q > self.q_max + tolerance:
            return "HIGH"

        return "NORMAL"

    def enforce_q_limits(self) -> bool:
        """
        Clamp reactive power to the local Generator limits.

        Returns True if Q was changed.

        This method does not alter PV/PQ operating mode.
        """

        old_q = self.q

        self.q = min(
            max(
                self.q,
                self.q_min,
            ),
            self.q_max,
        )

        return self.q != old_q

    # =================================================================
    # OPERATIONAL STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return True when the Generator is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return True when the Generator is out of service."""

        return not self.in_service

    def put_in_service(self) -> None:
        """Place Generator in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Remove Generator from service."""

        self.in_service = False

    def close(self) -> None:
        """Compatibility alias for putting Generator in service."""

        self.put_in_service()

    def trip(self) -> None:
        """Compatibility alias for taking Generator out of service."""

        self.take_out_of_service()

    # =================================================================
    # PLUGIN REFERENCES
    # =================================================================

    def attach_plugin(
        self,
        key: str,
        plugin: Any,
    ) -> None:
        """Attach a plugin reference."""

        if not isinstance(
            key,
            str,
        ) or not key.strip():
            raise ValueError(
                "Generator plugin key must be a non-empty string."
            )

        if plugin is None:
            raise ValueError(
                "Generator plugin cannot be None."
            )

        self._plugins[key] = plugin

    def get_plugin(
        self,
        key: str,
    ) -> Any | None:
        """Return a plugin reference if present."""

        return self._plugins.get(
            key
        )

    def has_plugin(
        self,
        key: str,
    ) -> bool:
        """Return True when the plugin exists."""

        return key in self._plugins

    def detach_plugin(
        self,
        key: str,
    ) -> Any | None:
        """Remove and return a plugin reference."""

        return self._plugins.pop(
            key,
            None,
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Generator-local invariants.

        Topological connectivity is deliberately not required.
        """

        self.p = self._validate_finite(
            self.p,
            "p",
        )

        self.q = self._validate_finite(
            self.q,
            "q",
        )

        self.V_setpoint = self._validate_positive(
            self.V_setpoint,
            "V_setpoint",
        )

        self.q_min, self.q_max = self._validate_q_limits(
            (
                self.q_min,
                self.q_max,
            )
        )

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise ValueError(
                f"Generator '{self.id}' in_service "
                "must be boolean."
            )

        if self.terminal.owner is not self:
            raise ValueError(
                f"Generator '{self.id}' terminal ownership "
                "is invalid."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Generator model.
        """

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured Generator diagnostics."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self.terminal.id,

            "endpoint": (
                self.endpoint.id
                if self.endpoint is not None
                and hasattr(self.endpoint, "id")
                else self.endpoint
            ),

            "bus": (
                self.bus.id
                if self.bus is not None
                and hasattr(self.bus, "id")
                else self.bus
            ),

            "p": self.p,
            "q": self.q,
            "V_setpoint": self.V_setpoint,

            "q_min": self.q_min,
            "q_max": self.q_max,
            "q_limit_status":
                self.q_limit_status(),

            "is_connected":
                self.is_connected,

            "in_service":
                self.in_service,

            "injection":
                self.get_power(),

            "plugin_count":
                len(self._plugins),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        endpoint_id = (
            self.endpoint.id
            if self.endpoint is not None
            and hasattr(self.endpoint, "id")
            else self.endpoint
        )

        return (
            f"<Generator "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"V={self.V_setpoint:.6f}, "
            f"Qlim=({self.q_min}, {self.q_max}), "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Return a finite floating-point value."""

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite value greater than zero."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite value greater than or equal to zero."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value

    @classmethod
    def _validate_q_limits(
        cls,
        q_limits: tuple[float, float],
    ) -> tuple[float, float]:
        """Validate and normalize Qmin/Qmax."""

        try:
            if len(q_limits) != 2:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "q_limits must contain exactly "
                "(Qmin, Qmax)."
            ) from exc

        q_min = float(q_limits[0])
        q_max = float(q_limits[1])

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                "Q limits cannot be NaN."
            )

        # +/- infinity are intentionally permitted because the
        # default Generator capability may be unbounded.

        if q_min > q_max:
            raise ValueError(
                "Qmin cannot exceed Qmax."
            )

        return (
            q_min,
            q_max,
        )


__all__ = [
    "Generator",
]
