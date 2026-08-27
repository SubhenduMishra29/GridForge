# core/numerical/state.py
"""
GridForge V2 Numerical State Models
===================================

File:
    core/model/state.py

Author:
    Subhendu Mishra

Purpose
-------
Defines numerical state containers used by GridForge analysis,
solver, and dynamic-simulation layers.

Architecture
------------

Static electrical model:

    core/model/

Numerical analysis:

    core/analysis/

Numerical solvers:

    core/solver/

Dynamic models:

    core/model/
    core/simulation/

Dynamic solver:

    core/solver/
    core/simulation/

State objects contain numerical state only.

They do NOT contain:

    - network topology
    - electrical equipment definitions
    - Y-bus construction
    - solver algorithms
    - protection logic
    - GUI state
    - SLD state
    - equipment ownership
    - dynamic differential equations

This separation allows the same electrical model to support:

    - Power Flow
    - State Estimation
    - Short Circuit
    - Dynamic Simulation
    - EMT / DAE Simulation
    - Contingency Analysis

The dynamic state container is deliberately generic.

A generator, AVR, governor, PSS, exciter, turbine, or future
dynamic component may contribute states to the numerical vector,
but DynamicState itself does not know what those states mean.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


# =====================================================================
# NUMERICAL VALIDATION HELPERS
# =====================================================================


def _finite_float(
    value: Any,
    field_name: str,
) -> float:
    """
    Convert a value to float and require it to be finite.
    """

    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be numeric."
        ) from exc

    if not isfinite(value):
        raise ValueError(
            f"{field_name} must be finite."
        )

    return value


def _validate_state_values(
    values: Any,
) -> None:
    """
    Validate a dynamic state vector when it can be inspected
    without introducing a mandatory NumPy dependency.

    The state container intentionally accepts generic vector-like
    objects so that the numerical backend can choose its own
    representation.

    Supported validation cases:

        - None
        - scalar numeric values
        - iterable/vector-like numeric values

    Objects that expose neither numeric nor iterable semantics are
    rejected.
    """

    if values is None:
        return

    # -------------------------------------------------------------
    # Scalar numerical state
    # -------------------------------------------------------------

    if isinstance(
        values,
        (int, float),
    ):
        _finite_float(
            values,
            "DynamicState.values",
        )
        return

    # -------------------------------------------------------------
    # Vector-like state
    # -------------------------------------------------------------

    try:
        iterator = iter(values)
    except TypeError:
        raise TypeError(
            "DynamicState.values must be None, a numeric value, "
            "or an iterable numerical state vector."
        )

    for index, value in enumerate(iterator):
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "DynamicState.values contains a "
                f"non-numeric value at index {index}."
            ) from exc

        if not isfinite(numeric_value):
            raise ValueError(
                "DynamicState.values contains a "
                f"non-finite value at index {index}."
            )


# =====================================================================
# BUS STATE
# =====================================================================


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
    BusState does not know which physical devices produced P and Q.

    It therefore remains suitable for:

        - load flow
        - state estimation
        - contingency studies
        - numerical iterations
        - solver rollback
    """

    vm: float = 1.0
    va: float = 0.0

    p: float = 0.0
    q: float = 0.0

    def __post_init__(self) -> None:
        """
        Normalize and validate numerical values.
        """

        self.vm = _finite_float(
            self.vm,
            "BusState.vm",
        )

        self.va = _finite_float(
            self.va,
            "BusState.va",
        )

        self.p = _finite_float(
            self.p,
            "BusState.p",
        )

        self.q = _finite_float(
            self.q,
            "BusState.q",
        )

        self.validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate(self) -> bool:
        """
        Validate the complete bus numerical state.

        Voltage magnitude must be finite and strictly positive.
        """

        self.vm = _finite_float(
            self.vm,
            "BusState.vm",
        )

        self.va = _finite_float(
            self.va,
            "BusState.va",
        )

        self.p = _finite_float(
            self.p,
            "BusState.p",
        )

        self.q = _finite_float(
            self.q,
            "BusState.q",
        )

        if self.vm <= 0.0:
            raise ValueError(
                "Bus-state voltage magnitude must be "
                "greater than zero."
            )

        return True

    # =================================================================
    # VOLTAGE
    # =================================================================

    def set_voltage(
        self,
        vm: float,
        va: float,
    ) -> None:
        """
        Update voltage magnitude and angle.
        """

        vm = _finite_float(
            vm,
            "BusState.vm",
        )

        va = _finite_float(
            va,
            "BusState.va",
        )

        if vm <= 0.0:
            raise ValueError(
                "Bus-state voltage magnitude must be "
                "greater than zero."
            )

        self.vm = vm
        self.va = va

    # =================================================================
    # POWER
    # =================================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Update calculated/net active and reactive power.
        """

        self.p = _finite_float(
            p,
            "BusState.p",
        )

        self.q = _finite_float(
            q,
            "BusState.q",
        )

    # =================================================================
    # COPY
    # =================================================================

    def copy(self) -> "BusState":
        """
        Return an independent copy of the bus state.

        Useful for:

            - Newton iterations
            - predictor/corrector methods
            - state rollback
            - contingency studies
            - numerical experimentation
        """

        return BusState(
            vm=self.vm,
            va=self.va,
            p=self.p,
            q=self.q,
        )

    # =================================================================
    # VECTOR REPRESENTATION
    # =================================================================

    def as_voltage_vector(self) -> tuple[float, float]:
        """
        Return voltage state as:

            (Vm, Va)
        """

        return (
            self.vm,
            self.va,
        )

    def as_power_vector(self) -> tuple[float, float]:
        """
        Return power state as:

            (P, Q)
        """

        return (
            self.p,
            self.q,
        )

    # =================================================================
    # RESET
    # =================================================================

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

        self.vm = _finite_float(
            vm,
            "BusState.vm",
        )

        self.va = _finite_float(
            va,
            "BusState.va",
        )

        self.p = _finite_float(
            p,
            "BusState.p",
        )

        self.q = _finite_float(
            q,
            "BusState.q",
        )

        self.validate()

    # =================================================================
    # DEBUG
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise numerical-state representation.
        """

        return (
            f"<BusState "
            f"Vm={self.vm:.6f}, "
            f"Va={self.va:.6f}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}>"
        )


# =====================================================================
# DYNAMIC STATE
# =====================================================================


@dataclass
class DynamicState:
    """
    Generic dynamic-simulation numerical state container.

    Parameters
    ----------
    values:
        Numerical state vector.

        The representation is intentionally backend-neutral.
        It may be:

            - None
            - a scalar numerical value
            - a tuple/list
            - a NumPy array
            - another numerical vector-like object

    time:
        Simulation time in seconds.

    Architecture
    ------------
    DynamicState contains numerical state only.

    It does not know whether a state belongs to:

        - generator rotor angle
        - generator speed
        - AVR
        - governor
        - PSS
        - exciter
        - turbine
        - motor
        - inverter
        - battery controller
        - future dynamic component

    The dynamic solver owns:

        - state-vector assembly
        - state indexing
        - integration
        - time stepping
        - convergence
        - event handling
    """

    values: Any = None
    time: float = 0.0

    def __post_init__(self) -> None:
        """
        Normalize and validate dynamic state.
        """

        self.time = _finite_float(
            self.time,
            "DynamicState.time",
        )

        _validate_state_values(
            self.values,
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate(self) -> bool:
        """
        Validate the complete dynamic state.
        """

        self.time = _finite_float(
            self.time,
            "DynamicState.time",
        )

        _validate_state_values(
            self.values,
        )

        return True

    # =================================================================
    # TIME
    # =================================================================

    def set_time(
        self,
        time: float,
    ) -> None:
        """
        Set simulation time in seconds.
        """

        self.time = _finite_float(
            time,
            "DynamicState.time",
        )

    # =================================================================
    # STATE VECTOR
    # =================================================================

    def set_values(
        self,
        values: Any,
    ) -> None:
        """
        Replace the numerical dynamic state vector.
        """

        _validate_state_values(
            values,
        )

        self.values = values

    # =================================================================
    # COPY
    # =================================================================

    def copy(self) -> "DynamicState":
        """
        Return an independent dynamic-state copy.

        If the numerical backend provides a ``copy()`` method,
        that method is used.

        Otherwise immutable/scalar values are reused.
        """

        if hasattr(
            self.values,
            "copy",
        ):
            values = self.values.copy()
        elif isinstance(
            self.values,
            list,
        ):
            values = list(self.values)
        elif isinstance(
            self.values,
            tuple,
        ):
            values = tuple(self.values)
        else:
            values = self.values

        return DynamicState(
            values=values,
            time=self.time,
        )

    # =================================================================
    # RESET
    # =================================================================

    def reset(
        self,
        values: Any = None,
        time: float = 0.0,
    ) -> None:
        """
        Reset the dynamic state.
        """

        time = _finite_float(
            time,
            "DynamicState.time",
        )

        _validate_state_values(
            values,
        )

        self.values = values
        self.time = time

    # =================================================================
    # VECTOR INFORMATION
    # =================================================================

    @property
    def size(self) -> int:
        """
        Return the number of scalar entries when the state vector
        exposes a length.

        Scalars and None return zero.
        """

        if self.values is None:
            return 0

        if isinstance(
            self.values,
            (str, bytes),
        ):
            return 0

        try:
            return len(self.values)
        except TypeError:
            return 1

    # =================================================================
    # DEBUG
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise dynamic-state representation.
        """

        return (
            f"<DynamicState "
            f"time={self.time:.6f}, "
            f"size={self.size}>"
        )


__all__ = [
    "BusState",
    "DynamicState",
]
