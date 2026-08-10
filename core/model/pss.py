```python
"""
GridForge Power System Stabilizer Model
=======================================

File:
    core/model/pss.py

Defines the GridForge Power System Stabilizer (PSS) model.

Purpose
-------
The PSS provides a supplementary damping signal to the excitation
system / AVR to improve electromechanical oscillation damping.

The present implementation uses a first-order washout filter:

    Tw * dXw/dt + Xw = Δω

The PSS output is:

    Vpss = Kpss * (Δω - Xw)

Therefore, in transfer-function form:

    Vpss(s) / Δω(s)
        = Kpss * Tw*s / (1 + Tw*s)

Where:

    Δω   = rotor speed deviation
    Xw   = internal washout low-pass state
    Tw   = washout time constant
    Kpss = stabilizer gain
    Vpss = stabilizing voltage signal

The washout characteristic ensures that a sustained constant speed
deviation does not create a permanent AVR bias.

Architecture
------------
The PSS does NOT perform numerical integration.

The dynamic / DAE solver owns:

    - Dynamic state vector
    - State integration
    - Time stepping
    - Initial conditions
    - Differential-algebraic solution

The PSS provides:

    - Differential equation
    - Washout output calculation
    - Output limiting
    - Initial-state calculation
    - Parameter management

Used by
--------
    Generator
    AVR
    Dynamic Solver

Future Extensions
-----------------
The model can later be extended with:

    - Lead-lag compensators
    - Multiple washout stages
    - PSS1A / IEEE standard models
    - Output rate limiting
    - Multiple input signals
    - Frequency / power input selection

The PSS model deliberately contains no numerical integration
or simulation-state ownership.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math


class PSS:
    """
    First-order Power System Stabilizer.

    The PSS does not integrate its internal state. The dynamic
    solver supplies the current washout state Xw and integrates
    the returned derivative.

    State Definition
    ----------------
    Xw is the low-pass component of the rotor-speed deviation:

        Tw * dXw/dt + Xw = Δω

    The stabilizing output is:

        Vpss = Kpss * (Δω - Xw)

    Parameters
    ----------
    Kpss:
        Stabilizer gain.

    Tw:
        Washout time constant in seconds.

    Vpss_min:
        Minimum stabilizing-voltage output.

    Vpss_max:
        Maximum stabilizing-voltage output.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        Kpss: float = 10.0,
        Tw: float = 10.0,
        Vpss_min: float = -0.2,
        Vpss_max: float = 0.2,
    ) -> None:
        """
        Initialize the PSS model.
        """

        self.Kpss = float(Kpss)
        self.Tw = float(Tw)

        self.Vpss_min = float(Vpss_min)
        self.Vpss_max = float(Vpss_max)

        self._validate()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate(self) -> None:
        """
        Validate PSS parameters.
        """

        if not math.isfinite(self.Kpss):
            raise ValueError(
                "PSS gain Kpss must be finite."
            )

        if self.Kpss < 0.0:
            raise ValueError(
                "PSS gain Kpss must be >= 0."
            )

        if not math.isfinite(self.Tw):
            raise ValueError(
                "PSS washout time constant Tw must be finite."
            )

        if self.Tw <= 0.0:
            raise ValueError(
                "PSS washout time constant Tw "
                "must be greater than zero."
            )

        if not math.isfinite(self.Vpss_min):
            raise ValueError(
                "PSS Vpss_min must be finite."
            )

        if not math.isfinite(self.Vpss_max):
            raise ValueError(
                "PSS Vpss_max must be finite."
            )

        if self.Vpss_min > self.Vpss_max:
            raise ValueError(
                "Vpss_min must not be greater than Vpss_max."
            )

    # =========================================================
    # STATE EQUATION
    # =========================================================

    def derivative(
        self,
        omega: float,
        state: float,
    ) -> float:
        """
        Calculate the washout-state derivative.

        Washout equation:

            Tw * dXw/dt + Xw = Δω

        Therefore:

            dXw/dt = (Δω - Xw) / Tw

        Parameters
        ----------
        omega:
            Rotor speed deviation Δω.

        state:
            Current washout state Xw.

        Returns
        -------
        float
            dXw/dt.
        """

        omega = float(omega)
        state = float(state)

        if not math.isfinite(omega):
            raise ValueError(
                "PSS rotor speed deviation omega "
                "must be finite."
            )

        if not math.isfinite(state):
            raise ValueError(
                "PSS washout state Xw must be finite."
            )

        return (
            omega - state
        ) / self.Tw

    # =========================================================
    # OUTPUT
    # =========================================================

    def output(
        self,
        omega: float,
        state: float,
    ) -> float:
        """
        Calculate the PSS stabilizing-voltage output.

        The washout output is:

            Vpss = Kpss * (Δω - Xw)

        Parameters
        ----------
        omega:
            Rotor speed deviation Δω.

        state:
            Current washout state Xw.

        Returns
        -------
        float
            Limited stabilizing-voltage signal Vpss.
        """

        omega = float(omega)
        state = float(state)

        if not math.isfinite(omega):
            raise ValueError(
                "PSS rotor speed deviation omega "
                "must be finite."
            )

        if not math.isfinite(state):
            raise ValueError(
                "PSS washout state Xw must be finite."
            )

        Vpss = self.Kpss * (
            omega - state
        )

        return self.limit(Vpss)

    # =========================================================
    # COMBINED EVALUATION
    # =========================================================

    def evaluate(
        self,
        omega: float,
        state: float,
    ) -> tuple[float, float]:
        """
        Evaluate the PSS differential equation and output.

        Parameters
        ----------
        omega:
            Rotor speed deviation Δω.

        state:
            Current washout state Xw.

        Returns
        -------
        tuple[float, float]
            (dXw_dt, Vpss)

        Notes
        -----
        No numerical integration occurs here.

        The dynamic solver must integrate the returned state
        derivative.
        """

        dx = self.derivative(
            omega=omega,
            state=state,
        )

        Vpss = self.output(
            omega=omega,
            state=state,
        )

        return dx, Vpss

    # =========================================================
    # LIMITER
    # =========================================================

    def limit(
        self,
        value: float,
    ) -> float:
        """
        Apply the PSS output limiter.

        Parameters
        ----------
        value:
            Unrestricted PSS output.

        Returns
        -------
        float
            Limited PSS output.
        """

        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                "PSS output value must be finite."
            )

        return max(
            self.Vpss_min,
            min(
                value,
                self.Vpss_max,
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
        Calculate the steady-state washout initial condition.

        For a constant speed deviation:

            dXw/dt = 0

        Therefore:

            Xw = Δω

        This gives:

            Vpss = Kpss * (Δω - Xw)
                 = 0

        which is the expected steady-state behavior of a
        washout filter.

        Parameters
        ----------
        omega:
            Initial rotor speed deviation.

        Returns
        -------
        float
            Initial washout state Xw.
        """

        omega = float(omega)

        if not math.isfinite(omega):
            raise ValueError(
                "Initial rotor speed deviation omega "
                "must be finite."
            )

        return omega

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        omega: float = 0.0,
    ) -> float:
        """
        Return the initial washout state.

        The dynamic solver should use this value when resetting
        the dynamic simulation.

        Parameters
        ----------
        omega:
            Initial rotor speed deviation.

        Returns
        -------
        float
            Initial washout state.
        """

        return self.initial_state(
            omega=omega,
        )

    # =========================================================
    # PARAMETER MANAGEMENT
    # =========================================================

    def set_gain(
        self,
        Kpss: float,
    ) -> None:
        """
        Update the stabilizer gain.
        """

        Kpss = float(Kpss)

        if not math.isfinite(Kpss):
            raise ValueError(
                "PSS gain Kpss must be finite."
            )

        if Kpss < 0.0:
            raise ValueError(
                "PSS gain Kpss must be >= 0."
            )

        self.Kpss = Kpss

    def set_washout_time(
        self,
        Tw: float,
    ) -> None:
        """
        Update the washout time constant.
        """

        Tw = float(Tw)

        if not math.isfinite(Tw):
            raise ValueError(
                "PSS washout time constant Tw "
                "must be finite."
            )

        if Tw <= 0.0:
            raise ValueError(
                "PSS washout time constant Tw "
                "must be greater than zero."
            )

        self.Tw = Tw

    def set_limits(
        self,
        Vpss_min: float,
        Vpss_max: float,
    ) -> None:
        """
        Update the PSS output limits.
        """

        Vpss_min = float(Vpss_min)
        Vpss_max = float(Vpss_max)

        if not math.isfinite(Vpss_min):
            raise ValueError(
                "PSS Vpss_min must be finite."
            )

        if not math.isfinite(Vpss_max):
            raise ValueError(
                "PSS Vpss_max must be finite."
            )

        if Vpss_min > Vpss_max:
            raise ValueError(
                "Vpss_min must not be greater than Vpss_max."
            )

        self.Vpss_min = Vpss_min
        self.Vpss_max = Vpss_max

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return PSS configuration information.
        """

        return {
            "type": "PSS",
            "model": "FIRST_ORDER_WASHOUT",
            "Kpss": self.Kpss,
            "Tw": self.Tw,
            "Vpss_min": self.Vpss_min,
            "Vpss_max": self.Vpss_max,
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<PSS "
            f"Kpss={self.Kpss:.4f}, "
            f"Tw={self.Tw:.4f}, "
            f"limits=("
            f"{self.Vpss_min:.4f}, "
            f"{self.Vpss_max:.4f})>"
        )
```
