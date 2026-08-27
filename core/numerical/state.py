"""
GridForge V2
Author: Subhendu Mishra

File:
    core/numerical/state.py

Purpose:
    Generic numerical state containers used by analysis and solver layers.

Architectural Boundary:
    Numerical state is not physical Model state.

    This module:
        - stores numerical values associated with physical model objects
        - remains independent of Network topology
        - remains independent of Study semantics
        - remains independent of solver algorithms
        - remains independent of UI/SLD
        - remains independent of persistence

    Study layers interpret the meaning of these values.
    Numerical/Solver layers operate on them.

Frozen Principle:
    Bus        != BusState
    Equipment  != DynamicState

    Physical Model:
        What physically exists.

    Network:
        How physical objects are connected.

    Study:
        What calculation/formulation is requested.

    Numerical:
        What numerical state is being evaluated.

    Solver:
        How the numerical problem is solved.

    Results:
        What the calculation produced.
"""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
from numbers import Real
from typing import Any


class BusState:
    """
    Numerical state associated with a network bus.

    BusState is deliberately independent of the physical Bus model.

    Stored quantities:
        vm:
            Voltage magnitude.

        va:
            Voltage angle.

        p:
            Net active-power quantity represented by the numerical state.

        q:
            Net reactive-power quantity represented by the numerical state.

    Important:
        BusState does not determine whether a bus is PQ, PV, or Slack.
        That interpretation belongs to the relevant Study formulation.

        BusState does not know which physical equipment produced or
        consumed P and Q.

        BusState does not own topology or solver logic.
    """

    __slots__ = ("_vm", "_va", "_p", "_q")

    def __init__(
        self,
        vm: Real = 1.0,
        va: Real = 0.0,
        p: Real = 0.0,
        q: Real = 0.0,
    ) -> None:
        self.vm = vm
        self.va = va
        self.p = p
        self.q = q

    @staticmethod
    def _validate_finite(value: Real, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a real number.")

        value = float(value)

        if not isfinite(value):
            raise ValueError(f"{name} must be finite.")

        return value

    @property
    def vm(self) -> float:
        return self._vm

    @vm.setter
    def vm(self, value: Real) -> None:
        value = self._validate_finite(value, "vm")

        if value <= 0.0:
            raise ValueError("vm must be greater than zero.")

        self._vm = value

    @property
    def va(self) -> float:
        return self._va

    @va.setter
    def va(self, value: Real) -> None:
        self._va = self._validate_finite(value, "va")

    @property
    def p(self) -> float:
        return self._p

    @p.setter
    def p(self, value: Real) -> None:
        self._p = self._validate_finite(value, "p")

    @property
    def q(self) -> float:
        return self._q

    @q.setter
    def q(self, value: Real) -> None:
        self._q = self._validate_finite(value, "q")

    def copy(self) -> "BusState":
        """Return an independent copy of the numerical state."""
        return BusState(
            vm=self.vm,
            va=self.va,
            p=self.p,
            q=self.q,
        )

    def validate(self) -> None:
        """Validate the complete numerical state."""
        self.vm = self.vm
        self.va = self.va
        self.p = self.p
        self.q = self.q

    def as_dict(self) -> dict[str, float]:
        """Return a backend-neutral representation of the state."""
        return {
            "vm": self.vm,
            "va": self.va,
            "p": self.p,
            "q": self.q,
        }

    def __repr__(self) -> str:
        return (
            "BusState("
            f"vm={self.vm!r}, "
            f"va={self.va!r}, "
            f"p={self.p!r}, "
            f"q={self.q!r}"
            ")"
        )


class DynamicState:
    """
    Generic numerical dynamic state container.

    DynamicState deliberately has no knowledge of the physical equipment
    or equations that generated the state vector.

    Examples of states that may use this container include:

        - synchronous-machine states
        - induction-motor states
        - excitation-system states
        - governor/turbine states
        - PSS states
        - converter states
        - battery-controller states
        - future plugin-defined dynamic models

    The physical/dynamic model defines the meaning of each state variable.
    The numerical layer stores the values.
    """

    __slots__ = ("_values",)

    def __init__(self, values: Any = None) -> None:
        self.values = values

    @staticmethod
    def _copy_values(values: Any) -> Any:
        if values is None:
            return None

        try:
            return values.copy()
        except AttributeError:
            return deepcopy(values)

    @property
    def values(self) -> Any:
        return self._values

    @values.setter
    def values(self, value: Any) -> None:
        if value is None:
            self._values = None
            return

        self._values = self._copy_values(value)

    def copy(self) -> "DynamicState":
        """Return an independent copy of the dynamic state."""
        return DynamicState(self._copy_values(self.values))

    def validate(self) -> None:
        """
        Validate basic numerical state integrity.

        Detailed dimensional and equation-specific validation belongs
        to the corresponding numerical model/solver.
        """
        if self.values is None:
            return

        values = self.values

        if isinstance(values, Real):
            if isinstance(values, bool) or not isfinite(float(values)):
                raise ValueError("Dynamic state contains a non-finite value.")
            return

        try:
            for value in values:
                if isinstance(value, Real):
                    if isinstance(value, bool) or not isfinite(float(value)):
                        raise ValueError(
                            "Dynamic state contains a non-finite value."
                        )
        except TypeError:
            # Backend-specific vector types may not expose direct iteration.
            # Their numerical backend remains responsible for detailed
            # validation.
            return

    def as_value(self) -> Any:
        """Return an independent copy of the stored numerical values."""
        return self._copy_values(self.values)

    def __repr__(self) -> str:
        return f"DynamicState(values={self.values!r})"
