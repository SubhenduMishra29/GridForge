# core/model/generator.py

"""
GridForge Generator Model
=========================

GridForge Model Layer V2

Defines the GridForge controllable Generator model.

Architecture
------------

A Generator is a controllable electrical power-injection device
connected to the electrical network through one physical Terminal.

    Generator
        │
     Terminal
        │
        └──── network topology ──── Bus

The Generator owns its physical Terminal.

The Terminal is the authoritative local physical connection point.
The network layer is responsible for establishing and interpreting
global topology.

Optional advanced functionality may be attached through the generic
plugin/extension mechanism:

    Generator
        └── plugins
              ├── dynamics.machine
              ├── dynamics.governor
              ├── dynamics.avr
              ├── dynamics.pss
              └── future extensions

The Generator deliberately does NOT know the concrete classes
implementing those extensions.

Plugin implementations belong outside ``core/model/``.

Generator Electrical Responsibilities
-------------------------------------

The Generator stores:

- Active power injection.
- Reactive power injection.
- Voltage-control setpoint.
- Reactive-power limits.
- Reactive-power limit status.
- Physical terminal connectivity.
- Generic plugin/extension references.

The Generator does NOT:

- Decide PV/PQ/SLACK bus classification.
- Build Y-bus.
- Perform Newton-Raphson iterations.
- Perform load-flow calculations.
- Perform short-circuit calculations.
- Perform contingency analysis.
- Perform dynamic integration.
- Perform protection calculations.
- Own the dynamic solver state vector.
- Manage global network topology.
- Manage GUI objects.
- Import or depend on concrete dynamic plugins.

Those responsibilities belong to the appropriate
network/solver/analysis/protection/simulation/plugin layers.

Sign Convention
---------------

Generator electrical power follows the GridForge
network-injection convention:

    +P
        Active power injected into the network.

    +Q
        Reactive power injected into the network.

Therefore:

    get_power() -> (P, Q)

Reactive Power Limits
---------------------

Q limits are stored as physical generator reactive-power limits:

    (Qmin, Qmax)

Infinite limits are permitted and represent unrestricted reactive
capability.

The Generator may locally clamp its own reactive-power value through
``enforce_q_limits()``.

It does NOT perform PV -> PQ bus conversion.

PV/PQ switching is a responsibility of the power-flow control layer.

Plugin Architecture
--------------------

The Generator exposes a generic plugin registry.

The registry stores references to extension objects but does not
interpret, execute, validate, or manage their internal state.

Example plugin identifiers include:

    "dynamics.machine"
    "dynamics.governor"
    "dynamics.avr"
    "dynamics.pss"
    "protection.relay"
    "control.exciter"
    "control.turbine"
    "converter.controller"

The Generator does not import or depend on any of these concrete
implementations.

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The electrical Generator interface is intentionally small, stable,
and independent of optional feature plugins.

The physical connection contract is Terminal-based and follows the
same ownership model used by other finalized V2 equipment/injection
models.

Changes require evidence of a genuinely fundamental generator-model
requirement that cannot be implemented through an existing model,
interface, plugin, or higher-level layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


# =====================================================================
# GENERATOR MODEL
# =====================================================================

class Generator(ElectricalObject, Injection):
    """
    GridForge controllable generator model.

    Parameters
    ----------
    id : str
        Unique GridForge generator identifier.

    bus :
        Initial electrical connection endpoint.

        Normally this is a Bus. The terminal may subsequently
        participate in a larger topology assembled by ``core/network``.

    p : float, optional
        Active power injection in per-unit.

        Positive values represent injection into the network.

    q : float, optional
        Reactive power injection in per-unit.

        Positive values represent injection into the network.

    V_setpoint : float, optional
        Voltage-magnitude control target in per-unit.

    q_limits : tuple[float, float], optional
        Reactive-power limits:

            (Qmin, Qmax)

        Infinite limits are permitted.

    name : str, optional
        Human-readable generator name.

    Notes
    -----
    The Generator owns its physical Terminal.

    The Generator does not directly modify Bus state or global
    network topology.

    Advanced functionality may be attached through the generic
    plugin registry using:

        attach_plugin()
        get_plugin()
        has_plugin()
        detach_plugin()

    The Generator does not own plugin execution state and does not
    invoke plugin behavior.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        bus,
        p: float = 0.0,
        q: float = 0.0,
        V_setpoint: float = 1.0,
        q_limits: tuple[float, float] = (
            -float("inf"),
            float("inf"),
        ),
        name: str = "",
    ) -> None:
        """
        Initialize a GridForge controllable generator.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # PHYSICAL TERMINAL
        # =============================================================
        #
        # The Generator owns the terminal.
        #
        # Explicit ownership is part of the V2 physical connection
        # contract and does not imply registration with core/network.
        #

        self.terminal = Terminal(
            endpoint=bus,
            owner=self,
        )

        # =============================================================
        # ELECTRICAL POWER
        # =============================================================
        #
        # Positive P/Q = injection into the network.
        #

        self.p = float(p)
        self.q = float(q)

        # =============================================================
        # VOLTAGE CONTROL
        # =============================================================

        self.V_setpoint = float(V_setpoint)

        # =============================================================
        # REACTIVE-POWER LIMITS
        # =============================================================

        try:
            if len(q_limits) != 2:
                raise ValueError(
                    f"Generator '{self.id}' q_limits must contain "
                    "exactly (Qmin, Qmax)."
                )

            self.q_min = float(q_limits[0])
            self.q_max = float(q_limits[1])

        except TypeError as exc:
            raise TypeError(
                f"Generator '{self.id}' q_limits must be a "
                "two-value sequence (Qmin, Qmax)."
            ) from exc

        # =============================================================
        # GENERIC PLUGIN REGISTRY
        # =============================================================
        #
        # Only references are stored.
        #
        # The Generator does not interpret or execute plugin objects.
        #

        self._plugins: dict[str, Any] = {}

        # =============================================================
        # LOCAL VALIDATION
        # =============================================================

        self._validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate(self) -> None:
        """
        Validate local generator parameters.

        P and Q must be finite.

        Voltage setpoint must be finite and positive.

        Q limits may be infinite but may never be NaN.

        Qmin must not exceed Qmax.
        """

        # -------------------------------------------------------------
        # Active power
        # -------------------------------------------------------------

        if not math.isfinite(self.p):
            raise ValueError(
                f"Generator '{self.id}' active power must be finite."
            )

        # -------------------------------------------------------------
        # Reactive power
        # -------------------------------------------------------------

        if not math.isfinite(self.q):
            raise ValueError(
                f"Generator '{self.id}' reactive power must be finite."
            )

        # -------------------------------------------------------------
        # Voltage setpoint
        # -------------------------------------------------------------

        if not math.isfinite(self.V_setpoint):
            raise ValueError(
                f"Generator '{self.id}' voltage setpoint "
                "must be finite."
            )

        if self.V_setpoint <= 0.0:
            raise ValueError(
                f"Generator '{self.id}' voltage setpoint "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Reactive-power limits
        #
        # Infinite values are valid.
        # NaN values are invalid.
        # -------------------------------------------------------------

        if math.isnan(self.q_min):
            raise ValueError(
                f"Generator '{self.id}' Qmin cannot be NaN."
            )

        if math.isnan(self.q_max):
            raise ValueError(
                f"Generator '{self.id}' Qmax cannot be NaN."
            )

        if self.q_min > self.q_max:
            raise ValueError(
                f"Generator '{self.id}' Qmin cannot exceed Qmax."
            )

    # =================================================================
    # TERMINAL / CONNECTION
    # =================================================================

    @property
    def bus(self):
        """
        Return the Bus-like endpoint associated with the Generator.

        This is a derived convenience property.

        The authoritative local physical connection is:

            self.terminal
        """

        return self.terminal.bus

    @property
    def endpoint(self):
        """
        Return the authoritative physical terminal endpoint.

        This is a compatibility/convenience accessor.

        Returns
        -------
        object or None
            Current terminal endpoint.
        """

        return self.terminal.endpoint

    @property
    def is_connected(self) -> bool:
        """
        Return True when the Generator terminal has an endpoint.
        """

        return self.terminal.is_connected

    def connect(self, endpoint) -> None:
        """
        Connect the Generator terminal to an electrical endpoint.

        This changes only the local physical terminal reference.

        Global topology remains the responsibility of ``core/network``.
        """

        self.terminal.connect(endpoint)

    def disconnect(self) -> None:
        """
        Disconnect the Generator terminal locally.

        Global network topology is not modified directly.
        """

        self.terminal.disconnect()

    # =================================================================
    # INJECTION INTERFACE
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return Generator network power injection.

        Returns
        -------
        tuple[float, float]
            ``(P, Q)`` in per-unit using the GridForge
            network-injection convention.

        Positive values represent injection into the network.
        """

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
        """
        Set generator active and reactive power injection.

        Q-limit enforcement is intentionally not performed here.

        The caller or the appropriate power-flow control layer may
        explicitly invoke ``enforce_q_limits()`` when required.
        """

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

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """
        Set generator active power injection.
        """

        p = float(p)

        if not math.isfinite(p):
            raise ValueError(
                f"Generator '{self.id}' active power must be finite."
            )

        self.p = p

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set generator reactive power injection.

        This method does not automatically enforce Q limits.
        """

        q = float(q)

        if not math.isfinite(q):
            raise ValueError(
                f"Generator '{self.id}' reactive power must be finite."
            )

        self.q = q

    # =================================================================
    # POWER PROPERTIES
    # =================================================================

    @property
    def active_power(self) -> float:
        """
        Return active power injection in per-unit.
        """

        return self.p

    @property
    def reactive_power(self) -> float:
        """
        Return reactive power injection in per-unit.
        """

        return self.q

    # =================================================================
    # VOLTAGE CONTROL
    # =================================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float,
    ) -> None:
        """
        Set the generator voltage-control target.

        Parameters
        ----------
        V_setpoint : float
            Voltage magnitude target in per-unit.
        """

        V_setpoint = float(V_setpoint)

        if not math.isfinite(V_setpoint):
            raise ValueError(
                f"Generator '{self.id}' voltage setpoint "
                "must be finite."
            )

        if V_setpoint <= 0.0:
            raise ValueError(
                f"Generator '{self.id}' voltage setpoint "
                "must be greater than zero."
            )

        self.V_setpoint = V_setpoint

    # =================================================================
    # REACTIVE-POWER LIMITS
    # =================================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """
        Return reactive-power limits.

        Returns
        -------
        tuple[float, float]
            ``(Qmin, Qmax)``
        """

        return (
            self.q_min,
            self.q_max,
        )

    def set_q_limits(
        self,
        q_min: float,
        q_max: float,
    ) -> None:
        """
        Set generator reactive-power limits.

        Infinite limits are permitted.

        The current generator Q value is not automatically modified.
        """

        q_min = float(q_min)
        q_max = float(q_max)

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                f"Generator '{self.id}' reactive-power limits "
                "cannot be NaN."
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
        Return the current reactive-power limit status.

        Parameters
        ----------
        tolerance : float, optional
            Numerical tolerance in per-unit.

        Returns
        -------
        str
            One of:

                "LOW"
                "HIGH"
                "NORMAL"

        Notes
        -----
        This method is diagnostic only.

        It does not modify Generator Q or Bus classification.
        """

        tolerance = float(tolerance)

        if not math.isfinite(tolerance):
            raise ValueError(
                f"Generator '{self.id}' Q-limit tolerance "
                "must be finite."
            )

        if tolerance < 0.0:
            raise ValueError(
                f"Generator '{self.id}' Q-limit tolerance "
                "cannot be negative."
            )

        if self.q < self.q_min - tolerance:
            return "LOW"

        if self.q > self.q_max + tolerance:
            return "HIGH"

        return "NORMAL"

    def enforce_q_limits(self) -> bool:
        """
        Clamp reactive power to the configured physical limits.

        Returns
        -------
        bool
            True if Q was modified, otherwise False.

        Notes
        -----
        This method changes only Generator-owned Q state.

        It does NOT:

        - change Bus classification,
        - perform PV -> PQ switching,
        - modify Bus voltage,
        - run a power-flow solution.

        PV -> PQ handling belongs to the power-flow control layer.
        """

        original_q = self.q

        if self.q < self.q_min:
            self.q = self.q_min

        elif self.q > self.q_max:
            self.q = self.q_max

        return self.q != original_q

    # =================================================================
    # GENERIC PLUGIN ARCHITECTURE
    # =================================================================

    def attach_plugin(
        self,
        key: str,
        plugin: Any,
        *,
        replace: bool = False,
    ) -> None:
        """
        Attach a generic plugin/extension reference.

        Parameters
        ----------
        key : str
            Unique plugin identifier.

        plugin : object
            Plugin/model reference.

        replace : bool, optional
            If False, replacing an existing plugin raises ValueError.

        Notes
        -----
        The Generator stores the reference only.

        Plugin lifecycle, validation, execution, and dynamic state
        management belong to the appropriate plugin/simulation layer.
        """

        if not isinstance(key, str):
            raise TypeError(
                f"Generator '{self.id}' plugin key must be a string."
            )

        key = key.strip()

        if not key:
            raise ValueError(
                f"Generator '{self.id}' plugin key cannot be empty."
            )

        if plugin is None:
            raise ValueError(
                f"Generator '{self.id}' plugin cannot be None."
            )

        if key in self._plugins and not replace:
            raise ValueError(
                f"Generator '{self.id}' plugin '{key}' "
                "is already attached."
            )

        self._plugins[key] = plugin

    def detach_plugin(
        self,
        key: str,
    ) -> Any | None:
        """
        Detach and return a plugin reference.

        Returns
        -------
        object or None
            Previously attached plugin, if present.
        """

        if not isinstance(key, str):
            raise TypeError(
                f"Generator '{self.id}' plugin key must be a string."
            )

        return self._plugins.pop(
            key.strip(),
            None,
        )

    def get_plugin(
        self,
        key: str,
    ) -> Any | None:
        """
        Return an attached plugin reference by key.
        """

        if not isinstance(key, str):
            raise TypeError(
                f"Generator '{self.id}' plugin key must be a string."
            )

        return self._plugins.get(
            key.strip()
        )

    def has_plugin(
        self,
        key: str,
    ) -> bool:
        """
        Return True when a plugin with the specified key exists.
        """

        if not isinstance(key, str):
            raise TypeError(
                f"Generator '{self.id}' plugin key must be a string."
            )

        return key.strip() in self._plugins

    def plugin_keys(self) -> tuple[str, ...]:
        """
        Return registered plugin identifiers.

        Returns
        -------
        tuple[str, ...]
            Immutable tuple of plugin keys.
        """

        return tuple(
            self._plugins.keys()
        )

    def plugins(self) -> dict[str, Any]:
        """
        Return a shallow copy of the plugin registry.

        The internal registry cannot be directly replaced by the
        caller through this returned dictionary.
        """

        return dict(self._plugins)

    def clear_plugins(self) -> None:
        """
        Detach all plugin references from the Generator.

        This does not destroy plugin objects or modify external
        simulation state.
        """

        self._plugins.clear()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Generator diagnostic information.

        Plugin presence is reported only by identifier.

        Plugin implementation details and dynamic solver state are
        intentionally excluded.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "generator",

            "terminal": self.terminal.summary(),

            "bus": (
                self.bus.id
                if self.bus is not None
                else None
            ),

            "connected": self.is_connected,

            "P": self.p,
            "Q": self.q,

            "V_setpoint": self.V_setpoint,

            "Qmin": self.q_min,
            "Qmax": self.q_max,
            "Q_status": self.q_limit_status(),

            "plugins": tuple(
                self._plugins.keys()
            ),
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
            f"<Generator "
            f"id={self.id}, "
            f"bus={bus_id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"Vset={self.V_setpoint:.6f}, "
            f"Qmin={self.q_min:.6f}, "
            f"Qmax={self.q_max:.6f}, "
            f"plugins={len(self._plugins)}>"
        )
```
