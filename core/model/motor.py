# core/model/motor.py
"""
GridForge V2 Motor Model
========================

Author:
    Subhendu Mishra

Motor is a static electrical equipment model representing an
electrical motor load.

Architecture
------------

    Motor
      |
      +-- ElectricalObject
      +-- Injection
      +-- Terminal
      |
      +-- steady-state electrical demand
      +-- equipment ratings
      +-- operating state
      +-- plugin references

Motor is NOT responsible for:

    - Network topology
    - Bus collections
    - Y-bus construction
    - Power-flow solving
    - Motor dynamic simulation
    - Mechanical equations
    - Starting transient calculation
    - VFD control execution
    - Protection calculation
    - SLD state
    - GUI state

Dynamic motor behavior is supplied by the appropriate simulation/
plugin layer.

Power convention
----------------

The Motor stores positive P/Q as electrical consumption.

Therefore:

    p > 0  -> active-power consumption
    q > 0  -> reactive-power consumption

The Injection interface exposes network injection as:

    P_injection = -p
    Q_injection = -q

Units
-----

The existing Core Motor contract uses per-unit P/Q.

Therefore this file intentionally preserves:

    p : pu
    q : pu

Ratings remain in:

    rated_mva       : MVA
    rated_voltage_kv: kV
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Motor(ElectricalObject, Injection):
    """
    Static electrical motor model.

    The Motor owns one authoritative electrical Terminal.

    A Motor may exist without being connected to a network. The
    network/application layer is responsible for establishing global
    topology.
    """

    TYPE = "MOTOR"

    def __init__(
        self,
        id: str,
        bus=None,
        *,
        endpoint=None,
        p: float = 0.0,
        q: float = 0.0,
        rated_mva: float | None = None,
        rated_voltage_kv: float | None = None,
        name: str = "",
        in_service: bool = True,
        running: bool = True,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Endpoint compatibility
        #
        # Existing API:
        #     Motor(id, bus, ...)
        #
        # Preferred V2 API:
        #     Motor(id, endpoint=...)
        #
        # Terminal remains authoritative.
        # ---------------------------------------------------------

        if (
            bus is not None
            and endpoint is not None
            and bus is not endpoint
        ):
            raise ValueError(
                f"Motor '{self.id}' received both 'bus' and "
                "'endpoint' with different values."
            )

        if endpoint is None:
            endpoint = bus

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # ---------------------------------------------------------
        # Steady-state electrical demand
        #
        # Positive P/Q = consumption.
        # ---------------------------------------------------------

        self.p = self._validate_finite(
            p,
            "p",
        )

        self.q = self._validate_finite(
            q,
            "q",
        )

        # ---------------------------------------------------------
        # Equipment ratings
        # ---------------------------------------------------------

        self.rated_mva = (
            None
            if rated_mva is None
            else self._validate_positive(
                rated_mva,
                "rated_mva",
            )
        )

        self.rated_voltage_kv = (
            None
            if rated_voltage_kv is None
            else self._validate_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )
        )

        # ---------------------------------------------------------
        # Operating state
        # ---------------------------------------------------------

        self.in_service = bool(in_service)
        self.running = bool(running)

        # ---------------------------------------------------------
        # Plugin references
        #
        # Core stores references only.
        # It does not execute plugin behavior.
        # ---------------------------------------------------------

        self._plugins: dict[str, Any] = {}

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""
        return self.TYPE

    # =============================================================
    # CONNECTIVITY
    # =============================================================

    @property
    def endpoint(self):
        """
        Return the authoritative electrical endpoint.
        """
        return self.terminal.endpoint

    @property
    def bus(self):
        """
        Compatibility accessor.

        The returned bus/endpoint is derived from the Terminal.
        It is not the authoritative connection state.
        """
        return self.terminal.bus

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Motor's electrical terminal."""
        return (self.terminal,)

    @property
    def is_connected(self) -> bool:
        """Return whether the Motor has an electrical endpoint."""
        return self.terminal.is_connected

    def connect_endpoint(self, endpoint) -> None:
        """
        Connect the Motor terminal.

        Global topology is not modified here.
        """
        self.terminal.connect(endpoint)

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Motor terminal.

        Global topology is not modified here.
        """
        self.terminal.disconnect()

    # =============================================================
    # OPERATING STATE
    # =============================================================

    def connect(self) -> None:
        """Place the Motor in service."""
        self.in_service = True

    def disconnect(self) -> None:
        """Take the Motor out of service."""
        self.in_service = False

    def start(self) -> None:
        """
        Set the Motor operating state to running.

        This does not perform a motor-starting simulation.
        """
        self.running = True

    def stop(self) -> None:
        """
        Set the Motor operating state to stopped.

        This does not perform a dynamic stopping simulation.
        """
        self.running = False

    @property
    def is_available(self) -> bool:
        """Return whether the Motor is electrically in service."""
        return self.in_service

    @property
    def is_running(self) -> bool:
        """Return whether the Motor is running."""
        return self.running

    # =============================================================
    # INJECTION CONTRACT
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return Motor network injection.

        Internal representation:

            +P = consumption
            +Q = consumption

        Network injection:

            -P
            -Q

        If the Motor is out of service or stopped, zero injection
        is returned.
        """

        if not self.in_service or not self.running:
            return 0.0, 0.0

        return (
            -self.p,
            -self.q,
        )

    # =============================================================
    # POWER CONTROL
    # =============================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set steady-state electrical demand.

        P and Q are positive consumption quantities in per-unit.
        """

        p = self._validate_finite(
            p,
            "p",
        )

        q = self._validate_finite(
            q,
            "q",
        )

        if p < 0.0:
            raise ValueError(
                f"Motor '{self.id}' active power demand "
                "cannot be negative."
            )

        if q < 0.0:
            raise ValueError(
                f"Motor '{self.id}' reactive power demand "
                "cannot be negative."
            )

        self.p = p
        self.q = q

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """Set active-power demand in per-unit."""

        p = self._validate_finite(
            p,
            "p",
        )

        if p < 0.0:
            raise ValueError(
                f"Motor '{self.id}' active power demand "
                "cannot be negative."
            )

        self.p = p

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """Set reactive-power demand in per-unit."""

        q = self._validate_finite(
            q,
            "q",
        )

        if q < 0.0:
            raise ValueError(
                f"Motor '{self.id}' reactive power demand "
                "cannot be negative."
            )

        self.q = q

    @property
    def active_power(self) -> float:
        """Return active-power demand in per-unit."""
        return self.p

    @property
    def reactive_power(self) -> float:
        """Return reactive-power demand in per-unit."""
        return self.q

    # =============================================================
    # RATINGS
    # =============================================================

    def set_rating(
        self,
        rated_mva: float | None = None,
        rated_voltage_kv: float | None = None,
    ) -> None:
        """Set optional motor equipment ratings."""

        if rated_mva is not None:
            rated_mva = self._validate_positive(
                rated_mva,
                "rated_mva",
            )

        if rated_voltage_kv is not None:
            rated_voltage_kv = self._validate_positive(
                rated_voltage_kv,
                "rated_voltage_kv",
            )

        self.rated_mva = rated_mva
        self.rated_voltage_kv = rated_voltage_kv

    # =============================================================
    # PLUGIN INTERFACE
    # =============================================================

    def register_plugin(
        self,
        plugin_id: str,
        plugin: Any,
    ) -> None:
        """
        Register a motor-related plugin reference.

        The Core Motor does not execute or interpret the plugin.
        """

        if not isinstance(plugin_id, str):
            raise TypeError(
                "plugin_id must be a string."
            )

        plugin_id = plugin_id.strip()

        if not plugin_id:
            raise ValueError(
                "plugin_id cannot be empty."
            )

        if plugin is None:
            raise ValueError(
                "plugin cannot be None."
            )

        if plugin_id in self._plugins:
            raise ValueError(
                f"Plugin '{plugin_id}' is already registered "
                f"for Motor '{self.id}'."
            )

        self._plugins[plugin_id] = plugin

    def get_plugin(
        self,
        plugin_id: str,
    ) -> Any | None:
        """Return a registered plugin reference."""
        return self._plugins.get(plugin_id)

    def remove_plugin(
        self,
        plugin_id: str,
    ) -> Any | None:
        """Remove and return a plugin reference."""
        return self._plugins.pop(
            plugin_id,
            None,
        )

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        """Return registered plugin identifiers."""
        return tuple(self._plugins.keys())

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Motor-local electrical parameters.

        This method deliberately does not validate global topology.
        """

        self._validate_finite(
            self.p,
            "p",
        )

        self._validate_finite(
            self.q,
            "q",
        )

        if self.p < 0.0:
            raise ValueError(
                f"Motor '{self.id}' active power demand "
                "must be >= 0."
            )

        if self.q < 0.0:
            raise ValueError(
                f"Motor '{self.id}' reactive power demand "
                "must be >= 0."
            )

        if self.rated_mva is not None:
            self._validate_positive(
                self.rated_mva,
                "rated_mva",
            )

        if self.rated_voltage_kv is not None:
            self._validate_positive(
                self.rated_voltage_kv,
                "rated_voltage_kv",
            )

        return True

    # Backward-compatible private validation entry point.
    def _validate(self) -> None:
        """Validate the current Motor state."""
        self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "p_pu": self.p,
            "q_pu": self.q,
            "rated_mva": self.rated_mva,
            "rated_voltage_kv": self.rated_voltage_kv,
            "in_service": self.in_service,
            "running": self.running,
            "endpoint": self.endpoint,
            "is_connected": self.is_connected,
            "plugins": self.plugin_ids,
        }

    # =============================================================
    # VALIDATION HELPERS
    # =============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Return a finite floating-point value."""

        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> float:
        """Return a finite positive floating-point value."""

        value = float(value)

        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{name} must be finite and greater than zero."
            )

        return value
