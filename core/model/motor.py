```python
"""
GridForge Motor Model
=====================

GridForge Model Layer V2

Defines the GridForge core Motor equipment model.

Architecture
------------
A Motor is a physical electrical load/injection device connected to
the network through a physical Terminal.

    Motor
       |
    Terminal
       |
    network topology
       |
      Bus

The Motor model represents the stable electrical identity of a motor
without embedding a particular motor dynamic model.

The core model supports:

    - Active-power demand
    - Reactive-power demand
    - Rated apparent power
    - Rated voltage
    - Operating state
    - Physical terminal
    - Generic plugin/extension references
    - Local validation
    - Diagnostics

Detailed motor behavior is intentionally delegated to plugins.

Possible plugins include:

    dynamics.induction_motor
    dynamics.synchronous_motor
    dynamics.motor_starting
    dynamics.mechanical_load
    drive.vfd
    control.motor_controller
    protection.motor_protection
    thermal.motor

The Motor does NOT:

    - Build Y-bus.
    - Perform load flow.
    - Perform motor-starting studies.
    - Perform transient motor simulation.
    - Perform dynamic integration.
    - Calculate short-circuit currents.
    - Perform protection calculations.
    - Control a VFD.
    - Determine network topology.
    - Own simulation history.
    - Store GUI state.

Those responsibilities belong to the appropriate
network, solver, analysis, protection, simulation, control,
or plugin layers.

Electrical Sign Convention
--------------------------
Motor demand is stored internally as positive consumption:

    p > 0
        Active-power consumption.

    q > 0
        Reactive-power consumption.

Through the Injection interface the Motor exposes:

    get_power() -> (-P, -Q)

Therefore:

    positive network injection
        = power supplied to the network

    negative network injection
        = power consumed from the network

The core Motor therefore behaves as a load at the steady-state
network-injection interface.

Dynamic motor plugins may provide a different electrical model to
dynamic or transient studies without changing the core Motor
identity.

Operating State
---------------
The Motor owns only its current physical operating state:

    in_service
    running

These are not simulation histories.

Simulation/event layers may record events such as:

    time
    motor
    start
    stop
    trip

without making that event history part of the authoritative Motor
model.

Plugin Boundary
---------------
The Motor itself is NOT a plugin.

It is a fundamental physical equipment object and therefore belongs
in:

    core/model/motor.py

Specialized behavior belongs in:

    core/plugins/

The generic plugin registry stores references only. The Motor does
not import, execute, or interpret plugin implementations.

This preserves the architecture:

    core/model
        stable physical equipment contract

    core/plugins
        specialized engineering behavior

    core/network
        topology and connectivity

    core/solver
        numerical computation

    core/analysis
        public study interfaces

    core/protection
        protection engineering

    core/simulation
        event and dynamic simulation

GridForge V2 Status
-------------------
This module is part of the GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental motor-model
requirement that cannot be satisfied through the existing Motor
interface, plugin architecture, or higher-level layers.

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
# MOTOR MODEL
# =====================================================================

class Motor(ElectricalObject, Injection):
    """
    GridForge core motor equipment model.

    The Motor is a physical electrical demand connected through one
    authoritative Terminal.

    Parameters
    ----------
    id : str
        Unique GridForge motor identifier.

    bus :
        Initial electrical connection endpoint.

        Normally this is a Bus. The network layer determines the
        complete topology.

    p : float, optional
        Active-power demand in per-unit.

        Positive values represent consumption.

    q : float, optional
        Reactive-power demand in per-unit.

        Positive values represent consumption.

    rated_mva : float, optional
        Motor rated apparent power in MVA.

    rated_voltage_kv : float, optional
        Motor rated voltage in kV.

    name : str, optional
        Human-readable motor name.

    Notes
    -----
    The Motor intentionally does not assume that every motor is an
    induction motor.

    Induction-motor, synchronous-motor, VFD-fed, starting, mechanical,
    thermal, and dynamic behavior can be attached through plugins.
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
        rated_mva: float | None = None,
        rated_voltage_kv: float | None = None,
        name: str = "",
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Physical electrical connection
        # -------------------------------------------------------------

        self.terminal = Terminal(
            endpoint=bus,
            owner=self,
        )

        # -------------------------------------------------------------
        # Steady-state electrical demand
        #
        # Positive P/Q = consumption.
        # -------------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        # -------------------------------------------------------------
        # Equipment ratings
        #
        # Ratings are optional because some network-level models may
        # initially operate only from P/Q values.
        # -------------------------------------------------------------

        self.rated_mva = (
            None
            if rated_mva is None
            else float(rated_mva)
        )

        self.rated_voltage_kv = (
            None
            if rated_voltage_kv is None
            else float(rated_voltage_kv)
        )

        # -------------------------------------------------------------
        # Physical operating state
        # -------------------------------------------------------------

        self.in_service = True
        self.running = True

        # -------------------------------------------------------------
        # Generic plugin registry
        #
        # The Motor stores references only.
        # It does not execute or interpret plugins.
        # -------------------------------------------------------------

        self._plugins: dict[str, Any] = {}

        # -------------------------------------------------------------
        # Validation
        # -------------------------------------------------------------

        self._validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate(self) -> None:
        """
        Validate the core Motor state.

        P and Q are consumption quantities and therefore must be
        finite and non-negative.

        Ratings, when supplied, must be finite and positive.
        """

        if not math.isfinite(self.p):
            raise ValueError(
                f"Motor '{self.id}': "
                "active power demand must be finite."
            )

        if not math.isfinite(self.q):
            raise ValueError(
                f"Motor '{self.id}': "
                "reactive power demand must be finite."
            )

        if self.p < 0.0:
            raise ValueError(
                f"Motor '{self.id}': "
                "active power demand must be >= 0."
            )

        if self.q < 0.0:
            raise ValueError(
                f"Motor '{self.id}': "
                "reactive power demand must be >= 0."
            )

        if self.rated_mva is not None:
            if not math.isfinite(self.rated_mva):
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated MVA must be finite."
                )

            if self.rated_mva <= 0.0:
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated MVA must be greater than zero."
                )

        if self.rated_voltage_kv is not None:
            if not math.isfinite(self.rated_voltage_kv):
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated voltage must be finite."
                )

            if self.rated_voltage_kv <= 0.0:
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated voltage must be greater than zero."
                )

    # =================================================================
    # CONNECTION
    # =================================================================

    @property
    def bus(self):
        """
        Return the endpoint currently associated with the Motor
        Terminal.

        The authoritative local connection is ``self.terminal``.

        Global topology belongs to the network/topology layer.
        """

        return self.terminal.bus

    # =================================================================
    # INJECTION INTERFACE
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return the Motor's network power injection.

        Returns
        -------
        tuple[float, float]
            ``(-P, -Q)`` in per-unit.

        Positive P/Q internally represent motor consumption.
        """

        if not self.in_service or not self.running:
            return (0.0, 0.0)

        return (
            -self.p,
            -self.q,
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
        Set steady-state motor active and reactive demand.

        Candidate values are validated before modifying model state.
        """

        p = float(p)
        q = float(q)

        if not math.isfinite(p):
            raise ValueError(
                f"Motor '{self.id}': "
                "active power demand must be finite."
            )

        if not math.isfinite(q):
            raise ValueError(
                f"Motor '{self.id}': "
                "reactive power demand must be finite."
            )

        if p < 0.0:
            raise ValueError(
                f"Motor '{self.id}': "
                "active power demand must be >= 0."
            )

        if q < 0.0:
            raise ValueError(
                f"Motor '{self.id}': "
                "reactive power demand must be >= 0."
            )

        self.p = p
        self.q = q

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """
        Set motor active-power demand.
        """

        p = float(p)

        if not math.isfinite(p):
            raise ValueError(
                f"Motor '{self.id}': "
                "active power demand must be finite."
            )

        if p < 0.0:
            raise ValueError(
                f"Motor '{self.id}': "
                "active power demand must be >= 0."
            )

        self.p = p

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set motor reactive-power demand.
        """

        q = float(q)

        if not math.isfinite(q):
            raise ValueError(
                f"Motor '{self.id}': "
                "reactive power demand must be finite."
            )

        if q < 0.0:
            raise ValueError(
                f"Motor '{self.id}': "
                "reactive power demand must be >= 0."
            )

        self.q = q

    # =================================================================
    # RATING
    # =================================================================

    def set_ratings(
        self,
        rated_mva: float | None = None,
        rated_voltage_kv: float | None = None,
    ) -> None:
        """
        Update motor equipment ratings.

        ``None`` means that the corresponding rating is not specified.
        """

        new_mva = (
            None
            if rated_mva is None
            else float(rated_mva)
        )

        new_voltage = (
            None
            if rated_voltage_kv is None
            else float(rated_voltage_kv)
        )

        if new_mva is not None:
            if not math.isfinite(new_mva):
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated MVA must be finite."
                )

            if new_mva <= 0.0:
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated MVA must be greater than zero."
                )

        if new_voltage is not None:
            if not math.isfinite(new_voltage):
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated voltage must be finite."
                )

            if new_voltage <= 0.0:
                raise ValueError(
                    f"Motor '{self.id}': "
                    "rated voltage must be greater than zero."
                )

        self.rated_mva = new_mva
        self.rated_voltage_kv = new_voltage

    # =================================================================
    # OPERATING STATE
    # =================================================================

    def start(self) -> None:
        """
        Set the physical motor operating state to running.

        Starting dynamics, acceleration, inrush current, and starting
        time belong to the appropriate motor/simulation plugin.
        """

        self.running = True

    def stop(self) -> None:
        """
        Set the physical motor operating state to stopped.

        The method does not model mechanical deceleration.
        """

        self.running = False

    def trip(self) -> None:
        """
        Remove the motor from service.

        Protection logic belongs to the protection layer.
        """

        self.in_service = False
        self.running = False

    def close(self) -> None:
        """
        Return the motor to service.

        This does not automatically start the motor.
        """

        self.in_service = True

    # =================================================================
    # STATUS
    # =================================================================

    @property
    def is_running(self) -> bool:
        """
        Return True when the motor is physically running.
        """

        return self.running

    @property
    def is_stopped(self) -> bool:
        """
        Return True when the motor is physically stopped.
        """

        return not self.running

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
        Attach a specialized Motor plugin.

        Examples
        --------
        ``dynamics.induction_motor``
        ``dynamics.synchronous_motor``
        ``dynamics.motor_starting``
        ``drive.vfd``
        ``thermal.motor``
        ``protection.motor_protection``

        The Motor stores the reference but does not execute the
        plugin.
        """

        if not isinstance(key, str):
            raise TypeError(
                "Motor plugin key must be a string."
            )

        key = key.strip()

        if not key:
            raise ValueError(
                "Motor plugin key cannot be empty."
            )

        if plugin is None:
            raise ValueError(
                "Motor plugin cannot be None."
            )

        if key in self._plugins and not replace:
            raise ValueError(
                f"Motor plugin '{key}' is already attached."
            )

        self._plugins[key] = plugin

    def detach_plugin(
        self,
        key: str,
    ) -> Any | None:
        """
        Detach a Motor plugin.
        """

        if not isinstance(key, str):
            raise TypeError(
                "Motor plugin key must be a string."
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
        Return an attached Motor plugin by key.
        """

        if not isinstance(key, str):
            raise TypeError(
                "Motor plugin key must be a string."
            )

        return self._plugins.get(
            key.strip()
        )

    def has_plugin(
        self,
        key: str,
    ) -> bool:
        """
        Return True when a Motor plugin exists.
        """

        if not isinstance(key, str):
            raise TypeError(
                "Motor plugin key must be a string."
            )

        return key.strip() in self._plugins

    def plugin_keys(self) -> tuple[str, ...]:
        """
        Return registered Motor plugin identifiers.
        """

        return tuple(self._plugins.keys())

    def plugins(self) -> dict[str, Any]:
        """
        Return a shallow copy of the Motor plugin registry.
        """

        return dict(self._plugins)

    def clear_plugins(self) -> None:
        """
        Remove all Motor plugin references.
        """

        self._plugins.clear()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return structured Motor diagnostic information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "motor",
            "bus": (
                self.bus.id
                if self.bus is not None
                else None
            ),
            "terminal": self.terminal.summary(),
            "p": self.p,
            "q": self.q,
            "p_injection": (
                -self.p
                if self.in_service and self.running
                else 0.0
            ),
            "q_injection": (
                -self.q
                if self.in_service and self.running
                else 0.0
            ),
            "rated_mva": self.rated_mva,
            "rated_voltage_kv": self.rated_voltage_kv,
            "in_service": self.in_service,
            "running": self.running,
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
            f"<Motor "
            f"id={self.id}, "
            f"bus={bus_id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"rated={self.rated_mva}, "
            f"running={self.running}, "
            f"in_service={self.in_service}, "
            f"plugins={len(self._plugins)}>"
        )
```
