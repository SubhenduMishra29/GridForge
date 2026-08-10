"""
GridForge Generator Model
=========================

File:
    core/model/generator.py

Defines the Generator model.

A Generator represents a controllable electrical power
injection connected to a Bus.

Supports
--------
- Active power injection
- Reactive power injection
- Voltage setpoint
- Reactive power limits

The Generator implements the Injection interface.

Sign Convention
---------------
Generator power is represented as network injection:

    +P -> active power injected into network
    +Q -> reactive power injected into network

Responsibilities
----------------
This class:

- Stores generator electrical data.
- Maintains its Bus connection.
- Implements the Injection interface.
- Stores voltage-control setpoint.
- Stores reactive-power operating limits.
- Provides Q-limit status information.

This class does NOT:

- Perform Newton-Raphson iterations.
- Decide PV/PQ bus classification.
- Modify Bus type automatically.
- Build Ybus.
- Perform load-flow calculations.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic simulation.

The power-flow solver and Q-limit handler operate on this
model through its public interface.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Tuple

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Generator(ElectricalObject, Injection):
    """
    Controllable generator model.
    """

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
    ) ->

        super().__init__(
            id=id,
            name=name,
        )

        # =====================================================
        # ELECTRICAL CONNECTION
        # =====================================================

        self.terminal = Terminal(bus)

        # =====================================================
        # GENERATOR POWER
        #
        # Positive P/Q = injection into network.
        # =====================================================

        self.p = float(p)
        self.q = float(q)

        # =====================================================
        # VOLTAGE CONTROL
        # =====================================================

        self.V_setpoint = float(V_setpoint)

        # =====================================================
        # REACTIVE POWER LIMITS
        # =====================================================

        try:
            if len(q_limits) != 2:
                raise ValueError(
                    "q_limits must contain exactly "
                    "(Qmin, Qmax)"
                )

            self.q_min = float(q_limits[0])
            self.q_max = float(q_limits[1])

        except TypeError as exc:
            raise TypeError(
                "q_limits must be a two-value sequence "
                "(Qmin, Qmax)"
            ) from exc

        self._validate()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate(self) -> None:
        """
        Validate generator parameters.
        """

        if self.V_setpoint <= 0.0:
            raise ValueError(
                "Generator voltage setpoint "
                "must be greater than zero."
            )

        if not math.isfinite(self.V_setpoint):
            raise ValueError(
                "Generator voltage setpoint must be finite."
            )

        if self.q_min > self.q_max:
            raise ValueError(
                "Generator Qmin cannot exceed Qmax."
            )

        if math.isnan(self.p):
            raise ValueError(
                "Generator active power cannot be NaN."
            )

        if math.isnan(self.q):
            raise ValueError(
                "Generator reactive power cannot be NaN."
            )

        if math.isnan(self.q_min):
            raise ValueError(
                "Generator Qmin cannot be NaN."
            )

        if math.isnan(self.q_max):
            raise ValueError(
                "Generator Qmax cannot be NaN."
            )

    # =========================================================
    # INJECTION INTERFACE
    # =========================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return generator network injection.

        Returns
        -------
        tuple[float, float]
            (P, Q)

        Positive values represent injection into the network.
        """

        return self.p, self.q

    # =========================================================
    # CONNECTION
    # =========================================================

    @property
    def bus(self):
        """
        Return the Bus connected to this generator.
        """

        return self.terminal.bus

    # =========================================================
    # POWER CONTROL
    # =========================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set generator active and reactive power.
        """

        p = float(p)
        q = float(q)

        if math.isnan(p):
            raise ValueError(
                "Generator active power cannot be NaN."
            )

        if math.isnan(q):
            raise ValueError(
                "Generator reactive power cannot be NaN."
            )

        self.p = p
        self.q = q

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """
        Set generator active power.
        """

        p = float(p)

        if math.isnan(p):
            raise ValueError(
                "Generator active power cannot be NaN."
            )

        self.p = p

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """
        Set generator reactive power.

        This method does not automatically clamp Q.

        Q-limit enforcement belongs to the power-flow
        control layer.
        """

        q = float(q)

        if math.isnan(q):
            raise ValueError(
                "Generator reactive power cannot be NaN."
            )

        self.q = q

    # =========================================================
    # VOLTAGE CONTROL
    # =========================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float,
    ) -> None:
        """
        Set the generator voltage-control target.

        Parameters
        ----------
        V_setpoint:
            Voltage magnitude in per-unit.
        """

        V_setpoint = float(V_setpoint)

        if V_setpoint <= 0.0:
            raise ValueError(
                "Voltage setpoint must be "
                "greater than zero."
            )

        if not math.isfinite(V_setpoint):
            raise ValueError(
                "Voltage setpoint must be finite."
            )

        self.V_setpoint = V_setpoint

    # =========================================================
    # REACTIVE POWER LIMITS
    # =========================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """
        Return reactive power limits.

        Returns
        -------
        tuple
            (Qmin, Qmax)
        """

        return self.q_min, self.q_max

    def set_q_limits(
        self,
        q_min: float,
        q_max: float,
    ) -> None:
        """
        Update generator reactive power limits.
        """

        q_min = float(q_min)
        q_max = float(q_max)

        if math.isnan(q_min) or math.isnan(q_max):
            raise ValueError(
                "Reactive power limits cannot be NaN."
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
        Determine current reactive-power limit status.

        Returns
        -------
        str
            "LOW", "HIGH", or "NORMAL".
        """

        tolerance = float(tolerance)

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
        Clamp reactive power to its physical limits.

        Returns
        -------
        bool
            True if Q was modified.

        Notes
        -----
        This method only clamps generator Q.

        It does NOT change the associated Bus type.

        PV -> PQ switching belongs to the QLimitHandler.
        """

        original_q = self.q

        if self.q < self.q_min:
            self.q = self.q_min

        elif self.q > self.q_max:
            self.q = self.q_max

        return self.q != original_q

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return generator diagnostic information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "bus": self.bus.id,
            "P": self.p,
            "Q": self.q,
            "V_setpoint": self.V_setpoint,
            "Qmin": self.q_min,
            "Qmax": self.q_max,
            "Q_status": self.q_limit_status(),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        return (
            f"<Generator "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}, "
            f"Vset={self.V_setpoint:.6f}, "
            f"Qmin={self.q_min:.6f}, "
            f"Qmax={self.q_max:.6f}>"
        )
