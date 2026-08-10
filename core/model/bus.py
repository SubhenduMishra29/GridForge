```python
"""
GridForge Bus Model
===================

File:
    core/model/bus.py

Defines the electrical Bus model and BusType classification.

The Bus model is part of the unified GridForge electrical model
and is shared by:

    - Network topology
    - Load Flow
    - Short Circuit
    - Contingency Analysis
    - Protection
    - Dynamic Simulation
    - GUI / SLD representation

The numerical solvers read the electrical state directly from
this model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum

from .base import ElectricalObject


# =============================================================
# BUS TYPE
# =============================================================

class BusType(Enum):
    """
    AC power-flow bus classification.

    PQ:
        Load bus.

    PV:
        Generator / voltage-controlled bus.

    SLACK:
        Reference bus.
    """

    PQ = 1
    PV = 2
    SLACK = 3


# =============================================================
# BUS MODEL
# =============================================================

class Bus(ElectricalObject):
    """
    GridForge electrical network bus.

    Parameters
    ----------
    id:
        Unique bus identifier.

    name:
        Human-readable bus name.

    type:
        Initial electrical bus classification.

    V:
        Current voltage magnitude in per-unit.

    theta:
        Current voltage angle in radians.

    P_spec:
        Specified active-power injection in per-unit.

    Q_spec:
        Specified reactive-power injection in per-unit.

    V_setpoint:
        Voltage setpoint for voltage-controlled buses.

    Notes
    -----
    The current electrical state is stored directly on the Bus:

        V
        theta

    Newton-Raphson modifies these values during solution.

    P_spec and Q_spec represent the specified power-flow
    equations associated with the current bus classification.

    Positive P/Q:
        Injection into the network.

    Negative P/Q:
        Consumption from the network.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        type: BusType = BusType.PQ,
        V: float = 1.0,
        theta: float = 0.0,
        P_spec: float = 0.0,
        Q_spec: float = 0.0,
        V_setpoint: float | None = None
    ):
        super().__init__(
            id,
            name
        )

        # ---------------------------------------------------------
        # Electrical classification
        # ---------------------------------------------------------

        if not isinstance(type, BusType):
            raise TypeError(
                "Bus type must be a BusType enum value"
            )

        self.type = type

        # ---------------------------------------------------------
        # Voltage state
        #
        # V:
        #     Current voltage magnitude in pu.
        #
        # theta:
        #     Current voltage angle in radians.
        # ---------------------------------------------------------

        self.V = float(V)
        self.theta = float(theta)

        # ---------------------------------------------------------
        # Voltage setpoint
        #
        # Used primarily by PV buses.
        #
        # If no explicit setpoint is supplied, the initial
        # voltage magnitude is used.
        # ---------------------------------------------------------

        if V_setpoint is None:
            V_setpoint = V

        self.V_setpoint = float(V_setpoint)

        # ---------------------------------------------------------
        # Specified power injection
        #
        # Positive:
        #     injection into network
        #
        # Negative:
        #     consumption from network
        # ---------------------------------------------------------

        self.P_spec = float(P_spec)
        self.Q_spec = float(Q_spec)

        self._validate_state()

    # =========================================================
    # BUS TYPE HELPERS
    # =========================================================

    def is_pq(self) -> bool:
        """Return True when this is a PQ bus."""
        return self.type is BusType.PQ

    def is_pv(self) -> bool:
        """Return True when this is a PV bus."""
        return self.type is BusType.PV

    def is_slack(self) -> bool:
        """Return True when this is the slack/reference bus."""
        return self.type is BusType.SLACK

    # =========================================================
    # BUS TYPE CONTROL
    # =========================================================

    def set_type(
        self,
        bus_type: BusType
    ):
        """
        Change the electrical bus classification.
        """

        if not isinstance(
            bus_type,
            BusType
        ):
            raise TypeError(
                "bus_type must be a BusType enum value"
            )

        self.type = bus_type

    # =========================================================
    # VOLTAGE CONTROL
    # =========================================================

    def set_voltage(
        self,
        V: float,
        theta: float | None = None
    ):
        """
        Update the current voltage state.

        Parameters
        ----------
        V:
            Voltage magnitude in pu.

        theta:
            Voltage angle in radians.

            If omitted, the existing angle is retained.

        Notes
        -----
        This represents the current electrical state, not the
        PV voltage setpoint.
        """

        V = float(V)

        if V <= 0.0:
            raise ValueError(
                "Voltage magnitude must be greater than zero"
            )

        self.V = V

        if theta is not None:
            self.theta = float(theta)

    def set_voltage_setpoint(
        self,
        V_setpoint: float
    ):
        """
        Set the voltage-control target.

        This is primarily used by PV and slack buses.
        """

        V_setpoint = float(V_setpoint)

        if V_setpoint <= 0.0:
            raise ValueError(
                "Voltage setpoint must be greater than zero"
            )

        self.V_setpoint = V_setpoint

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_state(self):
        """
        Validate the electrical state.
        """

        if not self.id:
            raise ValueError(
                "Bus ID cannot be empty"
            )

        if self.V <= 0.0:
            raise ValueError(
                "Bus voltage magnitude must be greater than zero"
            )

        if self.V_setpoint <= 0.0:
            raise ValueError(
                "Voltage setpoint must be greater than zero"
            )

        if not (
            float("-inf")
            <
            self.theta
            <
            float("inf")
        ):
            raise ValueError(
                "Bus voltage angle must be finite"
            )

        if not (
            float("-inf")
            <
            self.P_spec
            <
            float("inf")
        ):
            raise ValueError(
                "Bus P_spec must be finite"
            )

        if not (
            float("-inf")
            <
            self.Q_spec
            <
            float("inf")
        ):
            raise ValueError(
                "Bus Q_spec must be finite"
            )

    # =========================================================
    # STATE RESET
    # =========================================================

    def reset_voltage(
        self,
        V: float | None = None,
        theta: float = 0.0
    ):
        """
        Reset the current voltage state.

        Parameters
        ----------
        V:
            Voltage magnitude in pu.

            If omitted, the bus voltage setpoint is used.

        theta:
            Voltage angle in radians.
        """

        if V is None:
            V = self.V_setpoint

        V = float(V)

        if V <= 0.0:
            raise ValueError(
                "Voltage magnitude must be greater than zero"
            )

        self.V = V
        self.theta = float(theta)

    # =========================================================
    # POWER SPECIFICATION
    # =========================================================

    def set_power(
        self,
        P_spec: float | None = None,
        Q_spec: float | None = None
    ):
        """
        Update specified active/reactive power.

        Only supplied values are changed.
        """

        if P_spec is not None:
            self.P_spec = float(P_spec)

        if Q_spec is not None:
            self.Q_spec = float(Q_spec)

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self):
        """
        Return a compact electrical summary.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "V": self.V,
            "theta": self.theta,
            "V_setpoint": self.V_setpoint,
            "P_spec": self.P_spec,
            "Q_spec": self.Q_spec
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self):
        return (
            f"<Bus "
            f"id={self.id}, "
            f"type={self.type.name}, "
            f"V={self.V:.6f}, "
            f"theta={self.theta:.6f}, "
            f"Vset={self.V_setpoint:.6f}>"
        )
```
