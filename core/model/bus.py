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
        Generator/voltage-controlled bus.

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
        Voltage magnitude in per-unit.

    theta:
        Voltage angle in radians.

    P_spec:
        Specified active-power injection in per-unit.

    Q_spec:
        Specified reactive-power injection in per-unit.

    Notes
    -----
    The voltage state:

        V
        theta

    is intentionally stored on the Bus model.

    Newton-Raphson modifies these values during solution.

    The specified powers:

        P_spec
        Q_spec

    represent the power-flow equations associated with the
    current bus classification.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        type: BusType = BusType.PQ,
        V: float = 1.0,
        theta: float = 0.0,
        P_spec: float = 0.0,
        Q_spec: float = 0.0
    ):
        """
        Initialize a GridForge Bus.
        """

        super().__init__(
            id,
            name
        )

        # -----------------------------------------------------
        # Electrical classification
        # -----------------------------------------------------

        if not isinstance(
            type,
            BusType
        ):
            raise TypeError(
                "Bus type must be a BusType enum value"
            )

        self.type = type

        # -----------------------------------------------------
        # Voltage state
        #
        # V:
        #     per-unit voltage magnitude
        #
        # theta:
        #     radians
        # -----------------------------------------------------

        self.V = float(V)
        self.theta = float(theta)

        # -----------------------------------------------------
        # Specified power injections
        #
        # Positive convention:
        #     generation/injection
        #
        # Negative convention:
        #     load/consumption
        # -----------------------------------------------------

        self.P_spec = float(P_spec)
        self.Q_spec = float(Q_spec)

        self._validate_state()

    # =========================================================
    # BUS TYPE HELPERS
    # =========================================================

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
        Return True when this is the slack/reference bus.
        """

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

        Parameters
        ----------
        bus_type:
            New BusType.

        Notes
        -----
        This method keeps bus-type changes centralized and
        prevents accidental assignment of strings such as
        ``"PQ"`` or ``"PV"``.
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

        if not isinstance(
            self.theta,
            float
        ):
            self.theta = float(
                self.theta
            )

    # =========================================================
    # STATE RESET
    # =========================================================

    def reset_voltage(
        self,
        V: float = 1.0,
        theta: float = 0.0
    ):
        """
        Reset the bus voltage state.

        Useful for starting a new power-flow study.
        """

        if V <= 0.0:
            raise ValueError(
                "Voltage magnitude must be greater than zero"
            )

        self.V = float(V)
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

        Parameters
        ----------
        P_spec:
            Active-power injection in pu.

        Q_spec:
            Reactive-power injection in pu.

        Notes
        -----
        Only supplied values are changed.
        """

        if P_spec is not None:
            self.P_spec = float(
                P_spec
            )

        if Q_spec is not None:
            self.Q_spec = float(
                Q_spec
            )

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
            "P_spec": self.P_spec,
            "Q_spec": self.Q_spec
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self):
        """
        Developer-friendly representation.
        """

        return (
            f"<Bus "
            f"id={self.id}, "
            f"type={self.type.name}, "
            f"V={self.V:.6f}, "
            f"theta={self.theta:.6f}>"
        )
```
