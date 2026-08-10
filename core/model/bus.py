"""
GridForge Bus Model
===================

File:
    core/model/bus.py

Defines the electrical Bus model and BusType classification.

The Bus is the central electrical node of the GridForge network
model and is shared by:

    - Network topology
    - Load Flow
    - Short Circuit
    - Contingency Analysis
    - Protection
    - Dynamic Simulation
    - GUI / SLD representation

The current steady-state electrical voltage state is stored
directly on the Bus:

    V
    theta

Numerical solvers may update this state during solution.

Responsibilities
----------------
This class:

    - Represents an electrical bus.
    - Stores bus classification.
    - Stores current voltage state.
    - Stores specified power-flow quantities.
    - Stores voltage-control setpoint.
    - Provides basic state manipulation and validation.

This class does NOT:

    - Build Ybus.
    - Perform Newton-Raphson iterations.
    - Solve power flow.
    - Perform short-circuit calculations.
    - Perform contingency analysis.
    - Perform protection calculations.
    - Perform dynamic integration.
    - Manage GUI objects.

Those responsibilities belong to the appropriate
network/solver/analysis/simulation layers.

Sign Convention
---------------

For specified network power:

    +P, +Q
        Injection into the network.

    -P, -Q
        Consumption from the network.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite

from .base import ElectricalObject


# =============================================================
# BUS TYPE
# =============================================================

class BusType(Enum):
    """
    AC power-flow bus classification.

    PQ
        Load bus. Voltage magnitude and angle are solved.

    PV
        Generator / voltage-controlled bus. Active power and
        voltage magnitude are specified; reactive power is solved
        subject to generator limits.

    SLACK
        Reference bus. Voltage magnitude and angle are specified;
        active/reactive power balance is determined by the solver.
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
    id : str
        Unique GridForge object identifier.

    name : str, optional
        Human-readable bus name.

    type : BusType, optional
        Electrical bus classification.

    V : float, optional
        Current voltage magnitude in per-unit.

    theta : float, optional
        Current voltage angle in radians.

    P_spec : float, optional
        Specified active-power injection in per-unit.

    Q_spec : float, optional
        Specified reactive-power injection in per-unit.

    V_setpoint : float, optional
        Voltage-control target in per-unit.

        If omitted, the initial ``V`` value is used.

    Notes
    -----
    The Bus stores the current steady-state voltage state directly.

    This is intentional because the frozen GridForge Load Flow
    architecture operates on the Bus electrical state.

    ``V_setpoint`` is separate from ``V``:

        V
            Current solved voltage magnitude.

        V_setpoint
            Desired voltage magnitude for voltage-controlled buses.
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
            id=id,
            name=name
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
        # ---------------------------------------------------------

        self.V = float(V)
        self.theta = float(theta)

        # ---------------------------------------------------------
        # Voltage-control setpoint
        # ---------------------------------------------------------

        if V_setpoint is None:
            V_setpoint = self.V

        self.V_setpoint = float(V_setpoint)

        # ---------------------------------------------------------
        # Specified power injection
        # ---------------------------------------------------------

        self.P_spec = float(P_spec)
        self.Q_spec = float(Q_spec)

        self._validate_state()

    # =============================================================
    # BUS TYPE HELPERS
    # =============================================================

    def is_pq(self) -> bool:
        """Return True when this is a PQ bus."""

        return self.type is BusType.PQ

    def is_pv(self) -> bool:
        """Return True when this is a PV bus."""

        return self.type is BusType.PV

    def is_slack(self) -> bool:
        """Return True when this is the reference/slack bus."""

        return self.type is BusType.SLACK

    # =============================================================
    # BUS TYPE CONTROL
    # =============================================================

    def set_type(
        self,
        bus_type: BusType
    ) -> None:
        """
        Change the electrical bus classification.

        This method only changes the classification.

        It does not perform PV/PQ switching logic or Q-limit
        handling. Those decisions belong to the power-flow
        control layer.
        """

        if not isinstance(
            bus_type,
            BusType
        ):
            raise TypeError(
                "bus_type must be a BusType enum value"
            )

        self.type = bus_type

    # =============================================================
    # VOLTAGE STATE
    # =============================================================

    def set_voltage(
        self,
        V: float,
        theta: float | None = None
    ) -> None:
        """
        Update the current voltage state.

        Parameters
        ----------
        V:
            Voltage magnitude in per-unit.

        theta:
            Voltage angle in radians.

            If omitted, the existing angle is retained.
        """

        V = float(V)

        if not isfinite(V) or V <= 0.0:
            raise ValueError(
                "Voltage magnitude must be finite and greater "
                "than zero"
            )

        self.V = V

        if theta is not None:
            theta = float(theta)

            if not isfinite(theta):
                raise ValueError(
                    "Voltage angle must be finite"
                )

            self.theta = theta

    # =============================================================
    # VOLTAGE SETPOINT
    # =============================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float
    ) -> None:
        """
        Set the voltage-control target in per-unit.

        This is primarily used by PV and SLACK buses.
        """

        V_setpoint = float(V_setpoint)

        if (
            not isfinite(V_setpoint)
            or V_setpoint <= 0.0
        ):
            raise ValueError(
                "Voltage setpoint must be finite and greater "
                "than zero"
            )

        self.V_setpoint = V_setpoint

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_state(self) -> None:
        """
        Validate the complete electrical state.
        """

        # ---------------------------------------------------------
        # Voltage
        # ---------------------------------------------------------

        if not isfinite(self.V) or self.V <= 0.0:
            raise ValueError(
                "Bus voltage magnitude must be finite and "
                "greater than zero"
            )

        if not isfinite(self.theta):
            raise ValueError(
                "Bus voltage angle must be finite"
            )

        # ---------------------------------------------------------
        # Voltage setpoint
        # ---------------------------------------------------------

        if (
            not isfinite(self.V_setpoint)
            or self.V_setpoint <= 0.0
        ):
            raise ValueError(
                "Bus voltage setpoint must be finite and "
                "greater than zero"
            )

        # ---------------------------------------------------------
        # Specified power
        # ---------------------------------------------------------

        if not isfinite(self.P_spec):
            raise ValueError(
                "Bus P_spec must be finite"
            )

        if not isfinite(self.Q_spec):
            raise ValueError(
                "Bus Q_spec must be finite"
            )

    # =============================================================
    # STATE RESET
    # =============================================================

    def reset_voltage(
        self,
        V: float | None = None,
        theta: float = 0.0
    ) -> None:
        """
        Reset the current voltage state.

        Parameters
        ----------
        V:
            Voltage magnitude in per-unit.

            If omitted, ``V_setpoint`` is used.

        theta:
            Voltage angle in radians.
        """

        if V is None:
            V = self.V_setpoint

        self.set_voltage(
            V=V,
            theta=theta
        )

    # =============================================================
    # POWER SPECIFICATION
    # =============================================================

    def set_power(
        self,
        P_spec: float | None = None,
        Q_spec: float | None = None
    ) -> None:
        """
        Update specified active/reactive power injection.

        Only supplied values are changed.
        """

        if P_spec is not None:
            P_spec = float(P_spec)

            if not isfinite(P_spec):
                raise ValueError(
                    "P_spec must be finite"
                )

            self.P_spec = P_spec

        if Q_spec is not None:
            Q_spec = float(Q_spec)

            if not isfinite(Q_spec):
                raise ValueError(
                    "Q_spec must be finite"
                )

            self.Q_spec = Q_spec

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
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

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<Bus "
            f"id={self.id}, "
            f"type={self.type.name}, "
            f"V={self.V:.6f}, "
            f"theta={self.theta:.6f}, "
            f"Vset={self.V_setpoint:.6f}>"
        )
