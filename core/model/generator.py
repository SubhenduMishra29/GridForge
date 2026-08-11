```python
# core/model/generator.py

"""
GridForge Generator Model
=========================

GridForge Model Layer V2

Defines the GridForge controllable Generator model.

Architecture
------------
A Generator represents a controllable electrical power injection
connected to a Bus through a Terminal.

The Generator is an electrical model.

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

Plugin implementations belong outside core/model/.

Dynamic / DAE solver responsibilities include:

    - Dynamic state-vector ownership
    - State initialization
    - Algebraic-state management
    - Differential-equation evaluation
    - Time integration
    - Time stepping
    - DAE solution

Generator Electrical Responsibilities
-------------------------------------
The Generator model stores:

    - Active power injection
    - Reactive power injection
    - Voltage-control setpoint
    - Reactive-power limits
    - Reactive-power limit status
    - Bus connectivity
    - Generic plugin/extension references

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
    - Manage GUI objects.
    - Import or depend on specific dynamic plugins.

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
Q limits are stored by the Generator as physical generator limits.

Infinite limits are permitted and represent an unrestricted
generator.

The Generator may report and locally clamp its own Q value through
``enforce_q_limits()``.

It does NOT perform PV -> PQ bus conversion.

PV/PQ switching is a power-flow control-layer responsibility.

Plugin Architecture
-------------------
The Generator exposes a generic plugin registry.

The registry stores references to extension objects but does not
interpret their implementation.

This allows future functionality to be added without modifying
the central Generator model.

Examples of possible plugin identifiers include:

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

Plugin objects must therefore be managed by the appropriate
higher-level/plugin infrastructure.

GridForge V2 Status
-------------------
This module is part of the GridForge Model Layer V2 baseline.

The electrical Generator interface is intentionally kept small,
stable, and independent of optional feature plugins.

Changes require evidence of a genuinely fundamental generator-model
requirement that cannot be implemented through an existing model,
interface, plugin, or higher-level layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any, Tuple

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
        Unique GridForge object identifier.

    bus :
        Bus to which the generator is connected.

    p : float, optional
        Active power injection in per-unit.

        Positive values represent injection into the network.

    q : float, optional
        Reactive power injection in per-unit.

        Positive values represent injection into the network.

    V_setpoint : float, optional
        Voltage magnitude control target in per-unit.

    q_limits : tuple[float, float], optional
        Reactive-power limits as:

            (Qmin, Qmax)

        Infinite limits are permitted.

    name : str, optional
        Human-readable generator name.

    Notes
    -----
    The Generator is intentionally independent of specific dynamic
    model implementations.

    Advanced functionality may be attached through the generic
    plugin registry using:

        attach_plugin()
        get_plugin()
        has_plugin()
        detach_plugin()

    The Generator does not own plugin state or perform plugin
    execution.
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
        q_limits: Tuple[float, float] = (
            -float("inf"),
            float("inf"),
        ),
        name: str = "",
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Electrical connection
        # -------------------------------------------------------------

        self.terminal = Terminal(bus)

        # -------------------------------------------------------------
        # Generator electrical power
        #
        # Positive P/Q = injection into the network.
        # -------------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        # -------------------------------------------------------------
        # Voltage control
        # -------------------------------------------------------------

        self.V_setpoint = float(V_setpoint)

        # -------------------------------------------------------------
        # Reactive-power limits
        # -------------------------------------------------------------

        try:
            if len(q_limits) != 2:
                raise ValueError(
                    "q_limits must contain exactly "
                    "(Qmin, Qmax)."
                )

            self.q_min = float(q_limits[0])
            self.q_max = float(q_limits[1])

        except TypeError as exc:
            raise TypeError(
                "q_limits must be a two-value sequence "
                "(Qmin, Qmax)."
            ) from exc

        # -------------------------------------------------------------
        # Generic plugin registry
        #
        # The Generator stores references only.
        #
        # It does not know what a plugin does, does not execute
        # plugins, and does not own plugin state.
        # -------------------------------------------------------------

        self._plugins: dict[str, Any] = {}

        # -------------------------------------------------------------
        # Validate complete generator state.
        # -------------------------------------------------------------

        self._validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate(self) -> None:
        """
        Validate generator electrical parameters.

        P and Q must be finite.

        Q limits may be infinite, representing unrestricted
        reactive capability, but NaN is never valid.

        Voltage setpoint must be finite and positive.
        """

        # -------------------------------------------------------------
        # Active and reactive power
        # -------------------------------------------------------------

        if not math.isfinite(self.p):
            raise ValueError(
                "Generator active power must be finite."
            )

        if not math.isfinite(self.q):
            raise ValueError(
                "Generator reactive power must be finite."
            )

        # -------------------------------------------------------------
        # Voltage setpoint
        # -------------------------------------------------------------

        if not math.isfinite(self.V_setpoint):
            raise ValueError(
                "Generator voltage setpoint must be finite."
            )

        if self.V_setpoint <= 0.0:
            raise ValueError(
                "Generator voltage setpoint "
                "must be greater than zero."
            )

        # -------------------------------------------------------------
        # Reactive-power limits
        #
        # Infinite limits are valid.
        # NaN limits are not.
        # -------------------------------------------------------------

        if math.isnan(self.q_min):
            raise ValueError(
                "Generator Qmin cannot be NaN."
            )

        if math.isnan(self.q_max):
            raise ValueError(
                "Generator Qmax cannot be NaN."
            )

        if self.q_min > self.q_max:
            raise ValueError(
                "Generator Qmin cannot exceed Qmax."
            )

    # =================================================================
    # INJECTION INTERFACE
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return generator network power injection.

        Returns
        -------
        tuple[float, float]
            ``(P, Q)`` in the GridForge network-injection
            convention.

        Positive values represent injection into the network.
        """

        return (
            self.p,
            self.q,
        )

    # =================================================================
    # CONNECTION
    # =================================================================

    @property
    def bus(self):
        """
        Return the Bus connected to this generator.
        """

        return self.terminal.bus

    # =================================================================
    # POWER CONTROL
    # =================================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set generator active and reactive power.

        Parameters
        ----------
        p : float
            Active power injection in per-unit.

        q : float
            Reactive power injection in per-unit.

        Notes
        -----
        Q-limit enforcement is intentionally not performed here.

        The caller may explicitly use ``enforce_q_limits()`` or the
        appropriate power-flow control layer may manage generator
        reactive limits.
        """

        p = float(p)
        q = float(q)

        if not math.isfinite(p):
            raise ValueError(
                "Generator active power must be finite."
            )

        if not math.isfinite(q):
            raise ValueError(
                "Generator reactive power must be finite."
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
                "Generator active power must be finite."
            )

        self.p = p

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set generator reactive power injection.

        This method does not automatically clamp Q.

        Reactive-power limit handling belongs to the appropriate
        power-flow control workflow.
        """

        q = float(q)

        if not math.isfinite(q):
            raise ValueError(
                "Generator reactive power must be finite."
            )

        self.q = q

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
            Voltage magnitude in per-unit.
        """

        V_setpoint = float(V_setpoint)

        if not math.isfinite(V_setpoint):
            raise ValueError(
                "Generator voltage setpoint must be finite."
            )

        if V_setpoint <= 0.0:
            raise ValueError(
                "Generator voltage setpoint "
                "must be greater than zero."
            )

        self.V_setpoint = V_setpoint

    # =================================================================
    # REACTIVE POWER LIMITS
    # =================================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """
        Return generator reactive-power limits.

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
        Update generator reactive-power limits.

        Parameters
        ----------
        q_min : float
            Minimum reactive-power injection.

        q_max : float
            Maximum reactive-power injection.

        Notes
        -----
        Infinite limits are permitted.

        The limits are stored only. The current generator Q value
        is not automatically changed.
        """

        q_min = float(q_min)
        q_max = float(q_max)

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                "Reactive-power limits cannot be NaN."
            )

        if q_min > q_max:
            raise ValueError(
                "Qmin cannot exceed Qmax."
            )

        self.q_min = q_min
        self.q_max = q_max

    def q_limit_status(
        self,
        tolerance: float = 1e-6,
    ) -> str:
        """
        Determine the current reactive-power limit status.

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

        It does not change generator Q and does not change Bus
        classification.
        """

        tolerance = float(tolerance)

        if not math.isfinite(tolerance):
            raise ValueError(
                "Q-limit tolerance must be finite."
            )

        if tolerance < 0.0:
            raise ValueError(
                "Q-limit tolerance cannot be negative."
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
            True if Q was modified.

        Notes
        -----
        This method changes only the Generator's own reactive-power
        value.

        It does NOT:

        - Change Bus classification.
        - Perform PV -> PQ switching.
        - Modify Bus voltage.
        - Run a power-flow solution.

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
        Attach a generic plugin/extension to the Generator.

        Parameters
        ----------
        key : str
            Unique plugin key.

            Examples:

                "dynamics.machine"
                "dynamics.governor"
                "dynamics.avr"
                "dynamics.pss"

        plugin : object
            Plugin/model instance.

        replace : bool, optional
            If False, attempting to replace an existing plugin
            raises ValueError.

        Notes
        -----
        The Generator does not inspect or execute the plugin.

        Plugin lifecycle, validation, execution, and state
        management belong to the appropriate plugin infrastructure
        and higher-level simulation/control layers.
        """

        if not isinstance(key, str):
            raise TypeError(
                "Generator plugin key must be a string."
            )

        key = key.strip()

        if not key:
            raise ValueError(
                "Generator plugin key cannot be empty."
            )

        if plugin is None:
            raise ValueError(
                "Generator plugin cannot be None."
            )

        if key in self._plugins and not replace:
            raise ValueError(
                f"Generator plugin '{key}' is already attached."
            )

        self._plugins[key] = plugin

    def detach_plugin(
        self,
        key: str,
    ) -> Any | None:
        """
        Detach a plugin from the Generator.

        Parameters
        ----------
        key : str
            Plugin identifier.

        Returns
        -------
        object or None
            Previously attached plugin.
        """

        if not isinstance(key, str):
            raise TypeError(
                "Generator plugin key must be a string."
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
        Return an attached plugin by key.

        Parameters
        ----------
        key : str
            Plugin identifier.

        Returns
        -------
        object or None
            Attached plugin, if present.
        """

        if not isinstance(key, str):
            raise TypeError(
                "Generator plugin key must be a string."
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
                "Generator plugin key must be a string."
            )

        return key.strip() in self._plugins

    def plugin_keys(self) -> tuple[str, ...]:
        """
        Return the registered plugin keys.

        Returns
        -------
        tuple[str, ...]
            Immutable tuple of plugin identifiers.
        """

        return tuple(
            self._plugins.keys()
        )

    def plugins(self) -> dict[str, Any]:
        """
        Return a shallow copy of the plugin registry.

        Returns
        -------
        dict[str, object]
            Mapping of plugin identifiers to plugin references.

        Notes
        -----
        A copy is returned so callers cannot directly replace the
        Generator's internal registry.
        """

        return dict(self._plugins)

    def clear_plugins(self) -> None:
        """
        Detach all plugins from the Generator.

        Notes
        -----
        This only removes references from the Generator.

        It does not destroy plugin objects or modify any external
        solver state.
        """

        self._plugins.clear()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured generator diagnostic information.

        Plugin presence is reported by identifier without exposing
        plugin implementation details or dynamic solver state.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "generator",
            "bus": self.bus.id,
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

        return (
            f"<Generator "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"Vset={self.V_setpoint:.6f}, "
            f"Qmin={self.q_min:.6f}, "
            f"Qmax={self.q_max:.6f}, "
            f"plugins={len(self._plugins)}>"
        )
```
