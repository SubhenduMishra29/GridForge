```python
"""
GridForge Governor Model
========================

File:
    core/model/governor.py

Defines the turbine-governor dynamic model.

Purpose
-------
The Governor represents the primary speed-control dynamics of a
synchronous generating unit.

Basic first-order governor equation:

    dPm/dt =
        [Pref - Pm - omega / R] / Tg

Where:

    Pm    = mechanical power output
    Pref  = mechanical power reference
    omega = rotor speed deviation
    R     = governor droop
    Tg    = governor time constant

The governor does NOT perform numerical integration.

The dynamic / DAE solver owns:

    - Dynamic state vector
    - State integration
    - Time stepping
    - Initial conditions
    - Differential-algebraic solution

The Governor provides:

    - Differential equation
    - Mechanical-power limiting
    - Initial-state calculation
    - Parameter management

Architecture
------------
The Governor is intentionally independent of the numerical solver.

Typical dynamic chain:

    Rotor speed
        |
        v
    Governor
        |
        v
    Mechanical power Pm
        |
        v
    Synchronous machine

Used by
-------
    Generator
    Dynamic Solver
    Transient Stability Solver

Future Extensions
-----------------
The model can later support:

    - Turbine dynamics
    - Steam turbine models
    - Hydro turbine models
    - Gas turbine models
    - Deadband
    - Rate limiting
    - Multiple turbine stages
    - IEEE governor models
    - Valve position limits

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class Governor:
    """
    First-order turbine-governor model.

    The Governor does not store an authoritative dynamic state.

    The dynamic solver supplies the current mechanical-power state
    ``Pm`` and integrates the derivative returned by ``derivative()``.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        Pref: float = 1.0,
        R: float = 0.05,
        Tg: float = 0.2,
        Pm_min: float = 0.0,
        Pm_max: float = 1.2,
    ):
        """
        Initialize the governor model.

        Parameters
        ----------
        Pref:
            Mechanical power reference in per-unit.

        R:
            Governor speed-droop coefficient.

        Tg:
            Governor time constant in seconds.

        Pm_min:
            Minimum mechanical power output.

        Pm_max:
            Maximum mechanical power output.
        """

        # ---------------------------------------------------------
        # Convert parameters
        # ---------------------------------------------------------

        self.Pref = float(Pref)
        self.R = float(R)
        self.Tg = float(Tg)

        self.Pm_min = float(Pm_min)
        self.Pm_max = float(Pm_max)

        self._validate()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate(self) -> None:
        """
        Validate governor parameters.
        """

        if self.R <= 0.0:
            raise ValueError(
                "Governor droop R must be greater than zero."
            )

        if self.Tg <= 0.0:
            raise ValueError(
                "Governor time constant Tg must be greater than zero."
            )

        if self.Pm_min > self.Pm_max:
            raise ValueError(
                "Pm_min must not be greater than Pm_max."
            )

    # =============================================================
    # DIFFERENTIAL EQUATION
    # =============================================================

    def derivative(
        self,
        Pm: float,
        omega: float,
    ) -> float:
        """
        Calculate the mechanical-power state derivative.

        Equation:

            dPm/dt =
                [Pref - Pm - omega/R] / Tg

        Parameters
        ----------
        Pm:
            Current mechanical power state.

        omega:
            Rotor speed deviation in per-unit.

        Returns
        -------
        float
            dPm/dt.
        """

        Pm = float(Pm)
        omega = float(omega)

        return (
            self.Pref
            - Pm
            - omega / self.R
        ) / self.Tg

    # =============================================================
    # OUTPUT LIMITER
    # =============================================================

    def limit(
        self,
        Pm: float,
    ) -> float:
        """
        Apply mechanical-power limits.

        Parameters
        ----------
        Pm:
            Unrestricted mechanical power.

        Returns
        -------
        float
            Limited mechanical power.
        """

        return max(
            self.Pm_min,
            min(
                float(Pm),
                self.Pm_max,
            ),
        )

    # =============================================================
    # OUTPUT
    # =============================================================

    def output(
        self,
        Pm: float,
    ) -> float:
        """
        Return the limited mechanical-power output.

        The dynamic solver may use this function when the
        integrated state must be constrained by governor limits.
        """

        return self.limit(Pm)

    # =============================================================
    # COMBINED EVALUATION
    # =============================================================

    def evaluate(
        self,
        Pm: float,
        omega: float,
    ) -> tuple[float, float]:
        """
        Evaluate governor derivative and limited output.

        Parameters
        ----------
        Pm:
            Current mechanical-power state.

        omega:
            Rotor speed deviation.

        Returns
        -------
        tuple
            (dPm_dt, Pm_output)

        Notes
        -----
        No numerical integration occurs here.
        """

        dPm_dt = self.derivative(
            Pm=Pm,
            omega=omega,
        )

        Pm_output = self.output(Pm)

        return dPm_dt, Pm_output

    # =============================================================
    # INITIAL STATE
    # =============================================================

    def initial_state(
        self,
        omega: float = 0.0,
    ) -> float:
        """
        Calculate the steady-state initial mechanical-power state.

        At steady state:

            dPm/dt = 0

        Therefore:

            Pm = Pref - omega/R

        The result is passed through the mechanical-power limits.

        Parameters
        ----------
        omega:
            Initial rotor speed deviation.

        Returns
        -------
        float
            Initial mechanical-power state.
        """

        Pm = (
            self.Pref
            - float(omega) / self.R
        )

        return self.limit(Pm)

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
        omega: float = 0.0,
    ) -> float:
        """
        Return the initial governor state.

        The dynamic solver should use this value when resetting
        the simulation.
        """

        return self.initial_state(
            omega=omega,
        )

    # =============================================================
    # PARAMETER MANAGEMENT
    # =============================================================

    def set_reference(
        self,
        Pref: float,
    ) -> None:
        """
        Update mechanical-power reference.
        """

        self.Pref = float(Pref)

    def set_droop(
        self,
        R: float,
    ) -> None:
        """
        Update governor droop coefficient.
        """

        R = float(R)

        if R <= 0.0:
            raise ValueError(
                "Governor droop R must be greater than zero."
            )

        self.R = R

    def set_time_constant(
        self,
        Tg: float,
    ) -> None:
        """
        Update governor time constant.
        """

        Tg = float(Tg)

        if Tg <= 0.0:
            raise ValueError(
                "Governor time constant Tg must be greater than zero."
            )

        self.Tg = Tg

    def set_limits(
        self,
        Pm_min: float,
        Pm_max: float,
    ) -> None:
        """
        Update mechanical-power limits.
        """

        Pm_min = float(Pm_min)
        Pm_max = float(Pm_max)

        if Pm_min > Pm_max:
            raise ValueError(
                "Pm_min must not be greater than Pm_max."
            )

        self.Pm_min = Pm_min
        self.Pm_max = Pm_max

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return governor configuration information.
        """

        return {
            "Pref": self.Pref,
            "R": self.R,
            "Tg": self.Tg,
            "Pm_min": self.Pm_min,
            "Pm_max": self.Pm_max,
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<Governor "
            f"Pref={self.Pref:.4f}, "
            f"R={self.R:.6f}, "
            f"Tg={self.Tg:.6f}, "
            f"limits=({self.Pm_min:.4f}, "
            f"{self.Pm_max:.4f})>"
        )
```
