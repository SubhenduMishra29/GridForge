# core/model/generator.py
"""
GridForge Generator Model V2
============================

Author: Subhendu Mishra

A Generator is an electrical power-injection element.

Architectural boundary
----------------------

Generator owns:

    - generator identity
    - active/reactive power state
    - voltage setpoint
    - reactive-power limits
    - one electrical Terminal
    - optional plugin references

Generator does NOT own:

    - Network registration
    - global topology
    - Bus state
    - Y-Bus construction
    - power-flow solving
    - fault analysis
    - protection
    - dynamics
    - UI/SLD state

Physical connectivity is represented by:

    Generator
        |
        v
    Terminal
        |
        v
    Terminal.endpoint

The Network/Topology layer resolves the endpoint to the assembled
electrical Bus.

The ``bus`` property is retained only as a convenience/compatibility
accessor. It is NOT part of the Injection interface.

Power convention
----------------

    (+P, +Q) -> injection into the electrical network
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

    A Generator may be created before it is connected to a network.
    Therefore ``endpoint`` is allowed to be ``None``.

    Parameters
    ----------
    id:
        Stable object identifier.

    endpoint:
        Initial electrical endpoint. May be ``None``.

    p:
        Active power injection.

    q:
        Reactive power injection.

    V_setpoint:
        Generator voltage setpoint.

    q_limits:
        Tuple ``(Qmin, Qmax)``.

    name:
        Human-readable name.

    bus:
        Backward-compatible keyword alias for ``endpoint``.
        New code should use ``endpoint``.
    """

    def __init__(
        self,
        id: str,
        endpoint=None,
        p: float = 0.0,
        q: float = 0.0,
        V_setpoint: float = 1.0,
        q_limits: tuple[float, float] = (
            -float("inf"),
            float("inf"),
        ),
        name: str = "",
        *,
        bus=None,
    ) -> None:

        super().__init__(id=id, name=name)

        # ---------------------------------------------------------
        # Backward-compatible endpoint/bus handling
        # ---------------------------------------------------------

        if endpoint is not None and bus is not None and endpoint is not bus:
            raise ValueError(
                f"Generator '{self.id}' received both "
                "'endpoint' and 'bus' with different values."
            )

        if endpoint is None:
            endpoint = bus

        # ---------------------------------------------------------
        # Electrical state
        # ---------------------------------------------------------

        self.p = float(p)
        self.q = float(q)
        self.V_setpoint = float(V_setpoint)

        try:
            if len(q_limits) != 2:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Generator '{self.id}' q_limits must contain "
                "(Qmin, Qmax)."
            ) from exc

        self.q_min = float(q_limits[0])
        self.q_max = float(q_limits[1])

        # ---------------------------------------------------------
        # Physical electrical connection
        # ---------------------------------------------------------

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # ---------------------------------------------------------
        # Optional plugin references
        # ---------------------------------------------------------

        self._plugins: dict[str, Any] = {}

        self._validate()

    # =============================================================
    # Validation
    # =============================================================

    def _validate(self) -> None:
        """Validate local Generator invariants only."""

        if not math.isfinite(self.p):
            raise ValueError(
                f"Generator '{self.id}' active power must be finite."
            )

        if not math.isfinite(self.q):
            raise ValueError(
                f"Generator '{self.id}' reactive power must be finite."
            )

        if (
            not math.isfinite(self.V_setpoint)
            or self.V_setpoint <= 0.0
        ):
            raise ValueError(
                f"Generator '{self.id}' voltage setpoint "
                "must be finite and greater than zero."
            )

        if math.isnan(self.q_min) or math.isnan(self.q_max):
            raise ValueError(
                f"Generator '{self.id}' Q limits cannot be NaN."
            )

        if self.q_min > self.q_max:
            raise ValueError(
                f"Generator '{self.id}' Qmin cannot exceed Qmax."
            )

    # =============================================================
    # Connectivity
    # =============================================================

    @property
    def endpoint(self):
        """
        Return the authoritative physical endpoint.

        Terminal.endpoint is the source of truth.
        """
        return self.terminal.endpoint

    @property
    def bus(self):
        """
        Compatibility accessor.

        This is derived from Terminal and is NOT authoritative.
        """
        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return True when the Generator terminal is connected."""
        return self.terminal.is_connected

    def connect(self, endpoint) -> None:
        """Connect the Generator terminal to an endpoint."""
        self.terminal.connect(endpoint)

    def disconnect(self) -> None:
        """Disconnect the Generator terminal."""
        self.terminal.disconnect()

    # =============================================================
    # Injection contract
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network power injection.

        Returns
        -------
        tuple[float, float]
            ``(P, Q)``.

        Positive values represent injection into the network.
        """
        return self.p, self.q

    # =============================================================
    # Power control
    # =============================================================

    def set_power(self, p: float, q: float) -> None:
        """Set active and reactive power."""
        p = float(p)
        q = float(q)

        if not math.isfinite(p):
            raise ValueError(
                f"Generator '{self.id}' active power must be finite."
            )

        if not math.isfinite(q):
            raise ValueError(
                f"Generator '{self.id}' reactive power must be finite."
            )

        self.p = p
        self.q = q

    def set_active_power(self, p: float) -> None:
        """Set active power injection."""
        p = float(p)

        if not math.isfinite(p):
            raise ValueError(
                f"Generator '{self.id}' active power must be finite."
            )

        self.p = p

    def set_reactive_power(self, q: float) -> None:
        """Set reactive power injection."""
        q = float(q)

        if not math.isfinite(q):
            raise ValueError(
                f"Generator '{self.id}' reactive power must be finite."
            )

        self.q = q

    @property
    def active_power(self) -> float:
        """Return active power injection."""
        return self.p

    @property
    def reactive_power(self) -> float:
        """Return reactive power injection."""
        return self.q

    # =============================================================
    # Voltage control
    # =============================================================

    def set_voltage_setpoint(self, V_setpoint: float) -> None:
        """Set generator voltage setpoint."""
        V_setpoint = float(V_setpoint)

        if (
            not math.isfinite(V_setpoint)
            or V_setpoint <= 0.0
        ):
            raise ValueError(
                f"Generator '{self.id}' voltage setpoint "
                "must be finite and greater than zero."
            )

        self.V_setpoint = V_setpoint

    # =============================================================
    # Reactive-power limits
    # =============================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """Return ``(Qmin, Qmax)``."""
        return self.q_min, self.q_max

    def set_q_limits(
        self,
        q_min: float,
        q_max: float,
    ) -> None:
        """Set generator reactive-power limits."""

        q_min = float(q_min)
        q_max = float(q_max)

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                f"Generator '{self.id}' Q limits cannot be NaN."
            )

        if q_min > q_max:
            raise ValueError(
                f"Generator '{self.id}' Qmin cannot exceed Qmax."
            )

        self.q_min = q_min
        self.q_max = q_max

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

        tolerance = float(tolerance)

        if (
            not math.isfinite(tolerance)
            or tolerance < 0.0
        ):
            raise ValueError(
                "Q-limit tolerance must be finite "
                "and non-negative."
            )

        if self.q < self.q_min - tolerance:
            return "LOW"

        if self.q > self.q_max + tolerance:
            return "HIGH"

        return "NORMAL"

    def enforce_q_limits(self) -> bool:
        """
        Clamp reactive power to the Generator's physical limits.

        Returns
        -------
        bool
            True if Q was changed.

        Architectural note
        -------------------
        This operation only enforces the Generator's local Q
        capability.

        It does NOT change a Bus from PV to PQ.

        PV/PQ mode handling belongs to the power-flow/control layer.
        """

        old_q = self.q

        self.q = min(
            max(self.q, self.q_min),
            self.q_max,
        )

        return self.q != old_q

    # =============================================================
    # Plugin references
    # =============================================================

    def attach_plugin(
        self,
        key: str,
        plugin: Any,
    ) -> None:
        """Attach a plugin reference to this Generator."""

        if not isinstance(key, str) or not key.strip():
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
        """Return a plugin reference, if present."""
        return self._plugins.get(key)

    def has_plugin(
        self,
        key: str,
    ) -> bool:
        """Return True if the plugin exists."""
        return key in self._plugins

    def detach_plugin(
        self,
        key: str,
    ) -> Any | None:
        """Remove and return a plugin reference."""
        return self._plugins.pop(key, None)

    # =============================================================
    # Diagnostics
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return a diagnostic summary of the Generator."""

        return {
            "id": self.id,
            "name": self.name,
            "type": "Generator",
            "p": self.p,
            "q": self.q,
            "V_setpoint": self.V_setpoint,
            "q_min": self.q_min,
            "q_max": self.q_max,
            "is_connected": self.is_connected,
            "endpoint": self.endpoint,
            "plugin_count": len(self._plugins),
        }
