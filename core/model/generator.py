```python
"""
GridForge Generator Model
=========================

File:
    core/model/generator.py

Defines the Generator model.

A Generator represents a controllable electrical power
injection connected to a Bus.

Supports:

    - Active power injection
    - Reactive power injection
    - Voltage setpoint
    - Reactive power limits

The Generator implements the Injection interface.

Sign convention
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

This class does NOT:

    - Perform Newton-Raphson iterations.
    - Decide PV/PQ bus classification.
    - Modify Bus type automatically.
    - Build Ybus.
    - Perform load-flow calculations.
    - Perform contingency analysis.
    - Perform protection calculations.

The power-flow solver and Q-limit handler operate on this
model through its public interface.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Generator(ElectricalObject, Injection):
    """
    Controllable generator model.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    bus : Bus
        Bus to which the generator is connected.

    p : float
        Active power injection.

    q : float
        Current reactive power injection.

    V_setpoint : float
        Voltage magnitude target in per-unit.

    q_limits : tuple[float, float]
        Reactive power limits:

            (Qmin, Qmax)

    name : str
        Human-readable generator name.
    """

    def __init__(
        self,
        id: str,
        bus,
        p: float = 0.0,
        q: float = 0.0,
        V_setpoint: float = 1.0,
        q_limits: tuple[float, float] = (
            -float("inf"),
            float("inf")
        ),
        name: str = ""
    ):
        super().__init__(
            id=id,
            name=name
        )

        # ---------------------------------------------------------
        # Electrical connection
        # ---------------------------------------------------------

        self.terminal = Terminal(bus)

        # ---------------------------------------------------------
        # Generator power
        #
        # Positive P/Q means injection into the network.
        # ---------------------------------------------------------

        self.p = float(p)
        self.q = float(q)

        # ---------------------------------------------------------
        # Voltage control
        # ---------------------------------------------------------

        self.V_setpoint = float(
            V_setpoint
        )

        # ---------------------------------------------------------
        # Reactive power limits
        # ---------------------------------------------------------

        if len(q_limits) != 2:
            raise ValueError(
                "q_limits must contain exactly "
                "(Qmin, Qmax)"
            )

        self.q_min = float(
            q_limits[0]
        )

        self.q_max = float(
            q_limits[1]
        )

        self._validate()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate(self):
        """
        Validate generator parameters.
        """

        if self.V_setpoint <= 0.0:
            raise ValueError(
                "Generator voltage setpoint "
                "must be greater than zero"
            )

        if self.q_min > self.q_max:
            raise ValueError(
                "Generator Qmin cannot exceed Qmax"
            )

        if not self._is_finite_or_infinite(
            self.p
        ):
            raise ValueError(
                "Generator active power must be finite"
            )

        if not self._is_finite_or_infinite(
            self.q
        ):
            raise ValueError(
                "Generator reactive power must be finite"
            )

    @staticmethod
    def _is_finite_or_infinite(value):
        """
        Validate a scalar numeric value.

        Kept as a separate method so future model extensions
        can introduce more detailed numerical validation.
        """

        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    # =============================================================
    # INJECTION INTERFACE
    # =============================================================

    def get_power(self):
        """
        Return generator network injection.

        Returns
        -------
        tuple[float, float]
            (P, Q)

        Positive values represent injection into the network.
        """

        return self.p, self.q

    # =============================================================
    # CONNECTION
    # =============================================================

    @property
    def bus(self):
        """
        Return the Bus connected to this generator.
        """

        return self.terminal.bus

    # =============================================================
    # POWER CONTROL
    # =============================================================

    def set_power(
        self,
        p: float,
        q: float
    ):
        """
        Set generator active and reactive power.
        """

        self.p = float(p)
        self.q = float(q)

    def set_active_power(
        self,
        p: float
    ):
        """
        Set generator active power.
        """

        self.p = float(p)

    def set_reactive_power(
        self,
        q: float
    ):
        """
        Set generator reactive power.

        This method does not automatically clamp the value.
        Q-limit enforcement belongs to the power-flow control
        layer.
        """

        self.q = float(q)

    # =============================================================
    # VOLTAGE CONTROL
    # =============================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float
    ):
        """
        Set the generator voltage-control target.

        Parameters
        ----------
        V_setpoint:
            Voltage magnitude in per-unit.
        """

        V_setpoint = float(
            V_setpoint
        )

        if V_setpoint <= 0.0:
            raise ValueError(
                "Voltage setpoint must be "
                "greater than zero"
            )

        self.V_setpoint = V_setpoint

    # =============================================================
    # REACTIVE POWER LIMITS
    # =============================================================

    @property
    def q_limits(self):
        """
        Return generator reactive power limits.

        Returns
        -------
        tuple
            (Qmin, Qmax)
        """

        return self.q_min, self.q_max

    def set_q_limits(
        self,
        q_min: float,
        q_max: float
    ):
        """
        Update generator reactive power limits.
        """

        q_min = float(q_min)
        q_max = float(q_max)

        if q_min > q_max:
            raise ValueError(
                "Qmin cannot exceed Qmax"
            )

        self.q_min = q_min
        self.q_max = q_max

    def q_limit_status(
        self,
        tolerance: float = 1e-6
    ):
        """
        Determine the current reactive-power limit status.

        Returns
        -------
        str
            One of:

                "LOW"
                "HIGH"
                "NORMAL"
        """

        if self.q < self.q_min - tolerance:
            return "LOW"

        if self.q > self.q_max + tolerance:
            return "HIGH"

        return "NORMAL"

    def enforce_q_limits(self):
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

        PV → PQ switching is controlled by the
        QLimitHandler in the power-flow solver.
        """

        original_q = self.q

        if self.q < self.q_min:
            self.q = self.q_min

        elif self.q > self.q_max:
            self.q = self.q_max

        return self.q != original_q

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self):
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
            "Q_status": self.q_limit_status()
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self):
        return (
            f"<Generator "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.4f}, "
            f"Q={self.q:.4f}, "
            f"Vset={self.V_setpoint:.4f}, "
            f"Qmin={self.q_min:.4f}, "
            f"Qmax={self.q_max:.4f}>"
        )
```
