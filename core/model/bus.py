# core/model/bus.py

"""
GridForge Bus Model
===================

GridForge Model Layer V2

Defines the electrical Bus model and the BusType classification used
throughout the GridForge power-system domain model.

The Bus is the central electrical node of the GridForge network model
and is referenced by:

- Network topology
- Load-flow studies
- Short-circuit studies
- Contingency analysis
- Protection
- Dynamic simulation
- GUI / SLD representation

The Bus stores the current steady-state electrical voltage state:

    V
    theta

Numerical solver layers may read and update this state during a study.

Responsibilities
----------------
This module is responsible for:

- Representing an electrical bus.
- Storing bus classification.
- Storing current voltage state.
- Storing specified active/reactive power.
- Storing voltage-control setpoint.
- Storing reactive-power limits.
- Providing controlled state manipulation.
- Providing local state validation.
- Providing diagnostic information.

This module does NOT:

- Build Y-bus matrices.
- Perform Newton-Raphson iterations.
- Solve power flow.
- Perform short-circuit calculations.
- Perform contingency analysis.
- Perform protection calculations.
- Perform dynamic integration.
- Manage network topology.
- Manage GUI objects.

Those responsibilities belong to the appropriate GridForge layers.

Power Sign Convention
---------------------
For specified network power:

    +P, +Q
        Injection into the network.

    -P, -Q
        Consumption from the network.

Units
-----
- Voltage magnitude: per-unit
- Voltage angle: radians
- Active power: per-unit
- Reactive power: per-unit

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2
baseline.

Changes to this module require evidence of a genuinely fundamental
model requirement that cannot be satisfied by the network, solver,
analysis, protection, simulation, or plugin layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite, isnan

from .base import ElectricalObject


# =====================================================================
# BUS TYPE
# =====================================================================

class BusType(Enum):
    """
    AC power-flow bus classification.

    PQ
        Load bus.

        Active and reactive power are specified. Voltage magnitude
        and voltage angle are solved by the power-flow solver.

    PV
        Generator / voltage-controlled bus.

        Active power and voltage magnitude are specified. Reactive
        power is solved subject to the applicable reactive-power
        limits.

    SLACK
        Reference bus.

        Voltage magnitude and voltage angle are specified. Active
        and reactive power balance is determined by the solver.
    """

    PQ = 1
    PV = 2
    SLACK = 3


# =====================================================================
# BUS MODEL
# =====================================================================

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

    V_setpoint : float or None, optional
        Voltage-control target in per-unit.

        If omitted, the initial voltage magnitude ``V`` is used.

    Q_min : float, optional
        Minimum reactive-power injection in per-unit.

        Infinite values are permitted and represent an unlimited
        reactive-power range.

    Q_max : float, optional
        Maximum reactive-power injection in per-unit.

        Infinite values are permitted and represent an unlimited
        reactive-power range.

    Notes
    -----
    The Bus stores the current steady-state voltage state directly.

    This is intentional and forms part of the GridForge Model Layer
    contract used by the frozen load-flow and analysis architecture.

    ``V`` and ``V_setpoint`` have different meanings:

        V
            Current solved voltage magnitude.

        V_setpoint
            Desired voltage magnitude for voltage-controlled buses.

    Reactive-power limits are storage properties only. The Bus does
    not enforce Q limits or perform PV/PQ switching. Those decisions
    belong to the appropriate power-flow/control layer.
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
        V_setpoint: float | None = None,
        Q_min: float = float("-inf"),
        Q_max: float = float("inf"),
    ):
        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Electrical classification
        # -------------------------------------------------------------

        if not isinstance(type, BusType):
            raise TypeError(
                "Bus type must be a BusType enum value."
            )

        self.type = type

        # -------------------------------------------------------------
        # Voltage state
        # -------------------------------------------------------------

        self.V = float(V)
        self.theta = float(theta)

        # -------------------------------------------------------------
        # Voltage-control setpoint
        # -------------------------------------------------------------

        if V_setpoint is None:
            V_setpoint = self.V

        self.V_setpoint = float(V_setpoint)

        # -------------------------------------------------------------
        # Specified network power
        # -------------------------------------------------------------

        self.P_spec = float(P_spec)
        self.Q_spec = float(Q_spec)

        # -------------------------------------------------------------
        # Reactive-power limits
        #
        # These values are storage only.
        #
        # They may be populated from attached Generator objects and
        # consumed by the appropriate power-flow Q-limit handler.
        #
        # The Bus itself does not:
        # - enforce Q limits
        # - clamp Q_spec
        # - switch PV/PQ
        #
        # Infinite limits represent an unlimited range.
        # -------------------------------------------------------------

        self.Q_min = float(Q_min)
        self.Q_max = float(Q_max)

        # -------------------------------------------------------------
        # Validate initial state
        # -------------------------------------------------------------

        self._validate_state()

    # =================================================================
    # BUS TYPE HELPERS
    # =================================================================

    def is_pq(self) -> bool:
        """
        Return True when this is a PQ bus.
        """
        return self.type is BusType.PQ

    def is_pv(self) -> bool:
        """
        Return True when this is a PV bus.
        """
        return self.type is BusType.PV

    def is_slack(self) -> bool:
        """
        Return True when this is the reference/slack bus.
        """
        return self.type is BusType.SLACK

    # =================================================================
    # BUS TYPE CONTROL
    # =================================================================

    def set_type(
        self,
        bus_type: BusType,
    ) -> None:
        """
        Change the electrical bus classification.

        This method changes classification only.

        It does not:
        - perform PV/PQ switching logic
        - enforce reactive-power limits
        - modify Q_spec
        - perform numerical calculations
        """

        if not isinstance(bus_type, BusType):
            raise TypeError(
                "bus_type must be a BusType enum value."
            )

        self.type = bus_type

    def set_pq(self) -> None:
        """
        Convert the bus to PQ classification.

        This is a convenience wrapper around:

            set_type(BusType.PQ)

        The method only changes the classification.
        """

        self.set_type(BusType.PQ)

    # =================================================================
    # REACTIVE-POWER LIMITS
    # =================================================================

    def set_q_limits(
        self,
        Q_min: float,
        Q_max: float,
    ) -> None:
        """
        Update reactive-power limits.

        Parameters
        ----------
        Q_min : float
            Minimum reactive-power injection in per-unit.

        Q_max : float
            Maximum reactive-power injection in per-unit.

        Notes
        -----
        Infinite values are permitted and represent an unlimited
        reactive-power range.

        This method only stores the limits. It does not enforce them
        or change the bus classification.
        """

        Q_min = float(Q_min)
        Q_max = float(Q_max)

        if isnan(Q_min) or isnan(Q_max):
            raise ValueError(
                "Bus reactive-power limits cannot be NaN."
            )

        if Q_min > Q_max:
            raise ValueError(
                "Bus Q_min cannot be greater than Q_max."
            )

        self.Q_min = Q_min
        self.Q_max = Q_max

    # =================================================================
    # VOLTAGE STATE
    # =================================================================

    def set_voltage(
        self,
        V: float,
        theta: float | None = None,
    ) -> None:
        """
        Update the current voltage state.

        Parameters
        ----------
        V : float
            Voltage magnitude in per-unit.

        theta : float or None, optional
            Voltage angle in radians.

            If omitted, the existing angle is retained.
        """

        V = float(V)

        if not isfinite(V) or V <= 0.0:
            raise ValueError(
                "Voltage magnitude must be finite and greater than zero."
            )

        self.V = V

        if theta is not None:
            theta = float(theta)

            if not isfinite(theta):
                raise ValueError(
                    "Voltage angle must be finite."
                )

            self.theta = theta

    # =================================================================
    # VOLTAGE SETPOINT
    # =================================================================

    def set_voltage_setpoint(
        self,
        V_setpoint: float,
    ) -> None:
        """
        Set the voltage-control target in per-unit.

        This value is primarily used by PV and SLACK buses.
        """

        V_setpoint = float(V_setpoint)

        if not isfinite(V_setpoint) or V_setpoint <= 0.0:
            raise ValueError(
                "Voltage setpoint must be finite and greater than zero."
            )

        self.V_setpoint = V_setpoint

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_state(self) -> None:
        """
        Validate the complete local electrical state.

        This method performs local object validation only.

        System-wide validation, such as:
        - number of slack buses
        - network connectivity
        - generator/bus consistency
        - topology validity

        belongs to higher-level validation/network layers.
        """

        # -------------------------------------------------------------
        # Voltage magnitude
        # -------------------------------------------------------------

        if not isfinite(self.V) or self.V <= 0.0:
            raise ValueError(
                "Bus voltage magnitude must be finite and greater "
                "than zero."
            )

        # -------------------------------------------------------------
        # Voltage angle
        # -------------------------------------------------------------

        if not isfinite(self.theta):
            raise ValueError(
                "Bus voltage angle must be finite."
            )

        # -------------------------------------------------------------
        # Voltage setpoint
        # -------------------------------------------------------------

        if (
            not isfinite(self.V_setpoint)
            or self.V_setpoint <= 0.0
        ):
            raise ValueError(
                "Bus voltage setpoint must be finite and greater "
                "than zero."
            )

        # -------------------------------------------------------------
        # Specified active power
        # -------------------------------------------------------------

        if not isfinite(self.P_spec):
            raise ValueError(
                "Bus P_spec must be finite."
            )

        # -------------------------------------------------------------
        # Specified reactive power
        # -------------------------------------------------------------

        if not isfinite(self.Q_spec):
            raise ValueError(
                "Bus Q_spec must be finite."
            )

        # -------------------------------------------------------------
        # Reactive-power limits
        #
        # Infinite values are valid and represent an unlimited range.
        # Therefore we reject NaN and invalid ordering rather than
        # requiring finite values.
        # -------------------------------------------------------------

        if isnan(self.Q_min) or isnan(self.Q_max):
            raise ValueError(
                "Bus reactive-power limits cannot be NaN."
            )

        if self.Q_min > self.Q_max:
            raise ValueError(
                "Bus Q_min cannot be greater than Q_max."
            )

    # =================================================================
    # STATE RESET
    # =================================================================

    def reset_voltage(
        self,
        V: float | None = None,
        theta: float = 0.0,
    ) -> None:
        """
        Reset the current voltage state.

        Parameters
        ----------
        V : float or None, optional
            Voltage magnitude in per-unit.

            If omitted, ``V_setpoint`` is used.

        theta : float, optional
            Voltage angle in radians.
        """

        if V is None:
            V = self.V_setpoint

        self.set_voltage(
            V=V,
            theta=theta,
        )

    # =================================================================
    # POWER SPECIFICATION
    # =================================================================

    def set_power(
        self,
        P_spec: float | None = None,
        Q_spec: float | None = None,
    ) -> None:
        """
        Update specified active and/or reactive power injection.

        Only values explicitly supplied are changed.
        """

        if P_spec is not None:
            P_spec = float(P_spec)

            if not isfinite(P_spec):
                raise ValueError(
                    "P_spec must be finite."
                )

            self.P_spec = P_spec

        if Q_spec is not None:
            Q_spec = float(Q_spec)

            if not isfinite(Q_spec):
                raise ValueError(
                    "Q_spec must be finite."
                )

            self.Q_spec = Q_spec

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return a compact electrical summary.

        Returns
        -------
        dict
            Common identity information and the current Bus state.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "V": self.V,
            "theta": self.theta,
            "V_setpoint": self.V_setpoint,
            "P_spec": self.P_spec,
            "Q_spec": self.Q_spec,
            "Q_min": self.Q_min,
            "Q_max": self.Q_max,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Bus "
            f"id={self.id}, "
            f"type={self.type.name}, "
            f"V={self.V:.6f}, "
            f"theta={self.theta:.6f}, "
            f"Vset={self.V_setpoint:.6f}>"
        )
