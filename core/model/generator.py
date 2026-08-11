```python
"""
GridForge Governor Model
========================

File:
    core/model/governor.py

Defines the turbine governor model used by the GridForge
transient-stability / dynamic simulation framework.

Purpose
-------
The Governor represents a simplified first-order turbine-governor
dynamic model.

The governing equation is:

    dPm/dt = (Pref - Pm - omega / R) / Tg

where:

    Pm:
        Current mechanical power output in per-unit.

    Pref:
        Mechanical power reference in per-unit.

    omega:
        Rotor speed deviation in per-unit.

    R:
        Governor speed-droop coefficient.

    Tg:
        Governor time constant in seconds.

Architecture
------------
The Governor is a dynamic component, but it does NOT perform
numerical integration.

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
    - Diagnostic information

The Governor deliberately does NOT maintain an authoritative
dynamic state internally.

Used by
-------
    Generator
    Transient Stability Solver
    Dynamic Solver
    Governor Dynamic Plugin

Future Extensions
-----------------
The model can later support:

    - IEEE turbine-governor models
    - Hydraulic turbine governors
    - Steam turbine governors
    - Deadband
    - Rate limiting
    - Servo dynamics
    - Multiple turbine stages
    - Reheat dynamics
    - Nonlinear governor characteristics

Sign Convention
---------------
Mechanical power is represented as positive generation-side
mechanical input to the synchronous-machine model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math


class Governor:
    """
    First-order turbine governor model.

    The Governor does not integrate its internal state.

    The dynamic solver supplies the current mechanical-power
    state ``Pm`` and rotor-speed deviation ``omega`` and integrates
    the derivative returned by :meth:`derivative`.

    Parameters
    ----------
    Pref:
        Mechanical power reference in per-unit.

    R:
        Governor speed-droop coefficient.

    Tg:
        Governor time constant in seconds.

    Pm_min:
        Minimum mechanical power output in per-unit.

    Pm_max:
        Maximum mechanical power output in per-unit.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        Pref: float = 1.0,
        R: float = 0.05,
        Tg: float = 0.2,
        Pm_min: float = 0.0,
        Pm_max: float = 1.2,
    ) -> None:
        """
        Initialize the governor model.
        """

        # -----------------------------------------------------
        # Parameters
        # -----------------------------------------------------

        self.Pref = float(Pref)

        self.R = float(R)

        self.Tg = float(Tg)

        # -----------------------------------------------------
        # Mechanical-power limits
        # -----------------------------------------------------

        self.Pm_min = float(Pm_min)

        self.Pm_max = float(Pm_max)

        # -----------------------------------------------------
        # Validation
        # -----------------------------------------------------

        self._validate()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate(self) -> None:
        """
        Validate governor parameters.
        """

        if not math.isfinite(self.Pref):
            raise ValueError(
                "Governor reference Pref must be finite."
            )

        if not math.isfinite(self.R):
            raise ValueError(
                "Governor droop coefficient R must be finite."
            )

        if self.R <= 0.0:
            raise ValueError(
                "Governor droop coefficient R "
                "must be greater than zero."
            )

        if not math.isfinite(self.Tg):
            raise ValueError(
                "Governor time constant Tg must be finite."
            )

        if self.Tg <= 0.0:
            raise ValueError(
                "Governor time constant Tg "
                "must be greater than zero."
            )

        if not math.isfinite(self.Pm_min):
            raise ValueError(
                "Governor Pm_min must be finite."
            )

        if not math.isfinite(self.Pm_max):
            raise ValueError(
                "Governor Pm_max must be finite."
            )

        if self.Pm_min > self.Pm_max:
            raise ValueError(
                "Pm_min must not be greater than Pm_max."
            )

    # =========================================================
    # DIFFERENTIAL EQUATION
    # =========================================================

    def derivative(
        self,
        Pm: float,
        omega: float,
    ) -> float:
        """
        Calculate the mechanical-power state derivative.

        Equation
        --------
            dPm/dt =
                (Pref - Pm - omega / R) / Tg

        Parameters
        ----------
        Pm:
            Current mechanical-power state.

        omega:
            Rotor speed deviation.

        Returns
        -------
        float
            dPm/dt.

        Notes
        -----
        No numerical integration occurs here.

        The dynamic solver is responsible for integrating the
        returned derivative.
        """

        Pm = float(Pm)
        omega = float(omega)

        if not math.isfinite(Pm):
            raise ValueError(
                "Governor mechanical-power state Pm "
                "must be finite."
            )

        if not math.isfinite(omega):
            raise ValueError(
                "Governor rotor speed deviation omega "
                "must be finite."
            )

        return (
            self.Pref
            - Pm
            - omega / self.R
        ) / self.Tg

    # =========================================================
    # OUTPUT
    # =========================================================

    def output(
        self,
        Pm: float,
    ) -> float:
        """
        Return the limited mechanical-power output.

        Parameters
        ----------
        Pm:
            Current mechanical-power state.

        Returns
        -------
        float
            Limited mechanical power.
        """

        return self.limit(Pm)

    # =========================================================
    # COMBINED EVALUATION
    # =========================================================

    def evaluate(
        self,
        Pm: float,
        omega: float,
    ) -> tuple[float, float]:
        """
        Evaluate governor derivative and mechanical-power output.

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

        Pm_output = self.output(
            Pm=Pm,
        )

        return (
            dPm_dt,
            Pm_output,
        )

    # =========================================================
    # LIMITER
    # =========================================================

    def limit(
        self,
        Pm: float,
    ) -> float:
        """
        Apply mechanical-power limits.

        Parameters
        ----------
        Pm:
            Unrestricted mechanical-power state.

        Returns
        -------
        float
            Limited mechanical power.
        """

        Pm = float(Pm)

        if not math.isfinite(Pm):
            raise ValueError(
                "Governor mechanical-power value Pm "
                "must be finite."
            )

        return max(
            self.Pm_min,
            min(
                Pm,
                self.Pm_max,
            ),
        )

    # =========================================================
    # INITIAL STATE
    # =========================================================

    def initial_state(
        self,
        omega: float = 0.0,
    ) -> float:
        """
        Calculate the steady-state initial mechanical power.

        At steady state:

            dPm/dt = 0

        Therefore:

            Pm = Pref - omega / R

        The result is passed through the configured mechanical
        power limits.

        Parameters
        ----------
        omega:
            Initial rotor speed deviation.

        Returns
        -------
        float
            Initial mechanical-power state.
        """

        omega = float(omega)

        if not math.isfinite(omega):
            raise ValueError(
                "Initial rotor speed deviation omega "
                "must be finite."
            )

        Pm = (
            self.Pref
            - omega / self.R
        )

        return self.limit(Pm)

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        omega: float = 0.0,
    ) -> float:
        """
        Return the initial governor state.

        The dynamic solver should use this value when resetting
        the dynamic simulation.

        Parameters
        ----------
        omega:
            Initial rotor speed deviation.

        Returns
        -------
        float
            Initial mechanical-power state.
        """

        return self.initial_state(
            omega=omega,
        )

    # =========================================================
    # PARAMETER MANAGEMENT
    # =========================================================

    def set_reference(
        self,
        Pref: float,
    ) -> None:
        """
        Update the mechanical-power reference.
        """

        Pref = float(Pref)

        if not math.isfinite(Pref):
            raise ValueError(
                "Governor reference Pref must be finite."
            )

        self.Pref = Pref

    def set_droop(
        self,
        R: float,
    ) -> None:
        """
        Update the governor speed-droop coefficient.
        """

        R = float(R)

        if not math.isfinite(R):
            raise ValueError(
                "Governor droop coefficient R must be finite."
            )

        if R <= 0.0:
            raise ValueError(
                "Governor droop coefficient R "
                "must be greater than zero."
            )

        self.R = R

    def set_time_constant(
        self,
        Tg: float,
    ) -> None:
        """
        Update the governor time constant.
        """

        Tg = float(Tg)

        if not math.isfinite(Tg):
            raise ValueError(
                "Governor time constant Tg must be finite."
            )

        if Tg <= 0.0:
            raise ValueError(
                "Governor time constant Tg "
                "must be greater than zero."
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

        if not math.isfinite(Pm_min):
            raise ValueError(
                "Governor Pm_min must be finite."
            )

        if not math.isfinite(Pm_max):
            raise ValueError(
                "Governor Pm_max must be finite."
            )

        if Pm_min > Pm_max:
            raise ValueError(
                "Pm_min must not be greater than Pm_max."
            )

        self.Pm_min = Pm_min
        self.Pm_max = Pm_max

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return governor configuration information.
        """

        return {
            "type": "Governor",
            "model": "FIRST_ORDER",
            "Pref": self.Pref,
            "R": self.R,
            "Tg": self.Tg,
            "Pm_min": self.Pm_min,
            "Pm_max": self.Pm_max,
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<Governor "
            f"Pref={self.Pref:.4f}, "
            f"R={self.R:.6f}, "
            f"Tg={self.Tg:.6f}, "
            f"limits=("
            f"{self.Pm_min:.4f}, "
            f"{self.Pm_max:.4f})>"
        )
```
