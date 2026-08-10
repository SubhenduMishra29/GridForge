"""
GridForge Dynamic and Solver State Models
=========================================

File:
    core/model/state.py

Purpose
-------
Defines numerical state containers used by GridForge solvers.

Design Principles
-----------------
State objects contain numerical values only.

They do NOT contain:

    - Network topology
    - Electrical component definitions
    - Ybus construction
    - Solver algorithms
    - GUI state
    - Protection logic

The static electrical model remains in:

    core/model/

The numerical engines remain in:

    core/solver/
    core/analysis/

This separation allows the same electrical model to support:

    - Power Flow
    - State Estimation
    - Short Circuit
    - Dynamic Simulation
    - EMT / DAE simulation
    - Contingency analysis

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from dataclasses import dataclass


# =============================================================
# BUS STATE
# =============================================================

@dataclass
class BusState:
    """
    Numerical state associated with an electrical bus.

    Parameters
    ----------
    vm:
        Voltage magnitude in per-unit.

    va:
        Voltage angle in radians.

    p:
        Calculated/net active-power injection in per-unit.

    q:
        Calculated/net reactive-power injection in per-unit.

    Notes
    -----
    This class does not know which physical devices produced
    P and Q.

    It is therefore suitable for solver-side numerical state.
    """

    vm: float = 1.0
    va: float = 0.0

    p: float = 0.0
    q: float = 0.0

    def __post_init__(self) -> None:
        """Normalize numerical values and validate state."""

        self.vm = float(self.vm)
        self.va = float(self.va)

        self.p = float(self.p)
        self.q = float(self.q)

        self.validate()

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self) -> None:
        """
        Validate the numerical bus state.
        """

        if self.vm <= 0.0:
            raise ValueError(
                "Bus-state voltage magnitude must be greater than zero."
            )

    # =========================================================
    # VOLTAGE
    # =========================================================

    def set_voltage(
        self,
        vm: float,
        va: float,
    ) -> None:
        """
        Update voltage magnitude and angle.
        """

        vm = float(vm)

        if vm <= 0.0:
            raise ValueError(
                "Bus-state voltage magnitude must be greater than zero."
            )

        self.vm = vm
        self.va = float(va)

    # =========================================================
    # POWER
    # =========================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Update calculated/net power injection.
        """

        self.p = float(p)
        self.q = float(q)

    # =========================================================
    # COPY
    # =========================================================

    def copy(self) -> "BusState":
        """
        Return an independent copy of the bus state.

        Useful for:

            - Newton iterations
            - Predictor/corrector methods
            - State rollback
            - Contingency studies
            - Time-domain integration
        """

        return BusState(
            vm=self.vm,
            va=self.va,
            p=self.p,
            q=self.q,
        )

    # =========================================================
    # ARRAY REPRESENTATION
    # =========================================================

    def as_voltage_vector(self):
        """
        Return voltage state as:

            [Vm, Va]

        Useful for numerical solver interfaces.
        """

        return (
            self.vm,
            self.va,
        )

    def as_power_vector(self):
        """
        Return power state as:

            [P, Q]
        """

        return (
            self.p,
            self.q,
        )

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        vm: float = 1.0,
        va: float = 0.0,
        p: float = 0.0,
        q: float = 0.0,
    ) -> None:
        """
        Reset the complete bus numerical state.
        """

        self.vm = float(vm)
        self.va = float(va)

        self.p = float(p)
        self.q = float(q)

        self.validate()

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        return (
            f"<BusState "
            f"Vm={self.vm:.6f}, "
            f"Va={self.va:.6f}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}>"
        )


# =============================================================
# DYNAMIC STATE
# =============================================================

@dataclass
class DynamicState:
    """
    Generic dynamic-simulation state container.

    This is intentionally solver-oriented.

    The vector may contain states belonging to:

        - Generators
        - AVR
        - Governor
        - PSS
        - Exciters
        - Turbines
        - Future dynamic models

    Parameters
    ----------
    values:
        Numerical state vector.

    time:
        Simulation time in seconds.

    Notes
    -----
    The model classes define differential equations.

    The dynamic solver owns:

        - integration
        - time stepping
        - state-vector assembly
        - state-vector indexing
    """

    values: object = None
    time: float = 0.0

    def __post_init__(self) -> None:
        self.time = float(self.time)

    # =========================================================
    # TIME
    # =========================================================

    def set_time(
        self,
        time: float,
    ) -> None:
        """Set simulation time."""

        self.time = float(time)

    # =========================================================
    # STATE VECTOR
    # =========================================================

    def set_values(
        self,
        values,
    ) -> None:
        """Replace the numerical dynamic state vector."""

        self.values = values

    # =========================================================
    # COPY
    # =========================================================

    def copy(self) -> "DynamicState":
        """
        Return an independent dynamic-state copy.

        NumPy arrays are copied when supplied.
        """

        if hasattr(self.values, "copy"):
            values = self.values.copy()
        else:
            values = self.values

        return DynamicState(
            values=values,
            time=self.time,
        )

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        values=None,
        time: float = 0.0,
    ) -> None:
        """Reset the dynamic state."""

        self.values = values
        self.time = float(time)

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        size = (
            len(self.values)
            if self.values is not None
            and hasattr(self.values, "__len__")
            else 0
        )

        return (
            f"<DynamicState "
            f"time={self.time:.6f}, "
            f"size={size}>"
        )
