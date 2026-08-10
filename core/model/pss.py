"""
GridForge Power System Stabilizer (PSS)
=======================================

File:
    core/model/pss.py

Defines the Power System Stabilizer model.

Purpose
-------
The PSS provides a supplementary damping signal to the excitation
system / AVR to improve electromechanical oscillation damping.

Basic model
-----------
The present implementation uses a first-order washout filter:

    Tw * dXw/dt + Xw = Δω

and:

    Vpss = Kpss * Xw

followed by output limiting.

Where:

    Δω   = rotor speed deviation
    Xw   = washout state
    Tw   = washout time constant
    Kpss = stabilizer gain
    Vpss = stabilizing voltage signal

Architecture
------------
The PSS is a dynamic component, but it does NOT perform numerical
integration.

The DAE / dynamic simulation solver is responsible for:

    - State vector management
    - Time integration
    - Initial-condition calculation
    - Algebraic/differential equation solution

The PSS provides:

    - Differential equations
    - Output calculation
    - Output limiting
    - State reset

Used by
-------
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

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class PSS:
    """
    Power System Stabilizer.

    The PSS itself does not integrate its internal state. It provides
    the state derivative to the dynamic solver.

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

    Notes
    -----
    The dynamic state is intentionally NOT stored as an authoritative
    numerical state inside this model.

    The DAE solver owns the actual state vector.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        Kpss: float = 10.0,
        Tw: float = 10.0,
        Vpss_min: float = -0.2,
        Vpss_max: float = 0.2,
    ):
        """
        Initialize the PSS model.
        """

        # ---------------------------------------------------------
        # Validation
        # ---------------------------------------------------------

        if Tw <= 0.0:
            raise ValueError(
                "PSS washout time constant Tw must be greater than zero."
            )

        if Vpss_min > Vpss_max:
            raise ValueError(
                "Vpss_min must not be greater than Vpss_max."
            )

        # ---------------------------------------------------------
        # Parameters
        # ---------------------------------------------------------

        self.Kpss = float(Kpss)

        self.Tw = float(Tw)

        self.Vpss_min = float(Vpss_min)

        self.Vpss_max = float(Vpss_max)

    # =============================================================
    # STATE EQUATION
    # =============================================================

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

        return (
            float(omega) - float(state)
        ) / self.Tw

    # =============================================================
    # OUTPUT
    # =============================================================

    def output(
        self,
        state: float,
    ) -> float:
        """
        Calculate the PSS stabilizing-voltage output.

        Equation:

            Vpss = Kpss * Xw

        The output is passed through the configured limiter.

        Parameters
        ----------
        state:
            Current washout state Xw.

        Returns
        -------
        float
            Limited stabilizing-voltage signal Vpss.
        """

        Vpss = self.Kpss * float(state)

        return self.limit(Vpss)

    # =============================================================
    # COMBINED EVALUATION
    # =============================================================

    def evaluate(
        self,
        omega: float,
        state: float,
    ) -> tuple[float, float]:
        """
        Evaluate the PSS differential equation and output.

        This convenience method is useful for dynamic solvers.

        Parameters
        ----------
        omega:
            Rotor speed deviation Δω.

        state:
            Current washout state Xw.

        Returns
        -------
        tuple
            (state_derivative, Vpss)

        Notes
        -----
        No integration occurs here.

        The solver must integrate the returned derivative.
        """

        dx = self.derivative(
            omega,
            state,
        )

        Vpss = self.output(
            state,
        )

        return dx, Vpss

    # =============================================================
    # LIMITER
    # =============================================================

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

        return max(
            self.Vpss_min,
            min(
                float(value),
                self.Vpss_max,
            ),
        )

    # =============================================================
    # INITIAL STATE
    # =============================================================

    def initial_state(
        self,
        omega: float = 0.0,
    ) -> float:
        """
        Return the steady-state washout initial condition.

        For a constant speed deviation:

            dXw/dt = 0

        gives:

            Xw = Δω

        Therefore the steady-state initial condition is the supplied
        rotor-speed deviation.

        For normal initialization at nominal speed:

            omega = 0

        and therefore:

            Xw = 0
        """

        return float(omega)

    # =============================================================
    # RESET
    # =============================================================

    def reset(self) -> float:
        """
        Return the default PSS initial state.

        The solver should use this value when resetting the dynamic
        simulation.

        Returns
        -------
        float
            Initial washout state.
        """

        return 0.0

    # =============================================================
    # PARAMETERS
    # =============================================================

    def set_gain(
        self,
        Kpss: float,
    ) -> None:
        """
        Update the stabilizer gain.
        """

        self.Kpss = float(Kpss)

    def set_washout_time(
        self,
        Tw: float,
    ) -> None:
        """
        Update the washout time constant.
        """

        if Tw <= 0.0:
            raise ValueError(
                "PSS washout time constant Tw must be greater than zero."
            )

        self.Tw = float(Tw)

    def set_limits(
        self,
        Vpss_min: float,
        Vpss_max: float,
    ) -> None:
        """
        Update the PSS output limits.
        """

        if Vpss_min > Vpss_max:
            raise ValueError(
                "Vpss_min must not be greater than Vpss_max."
            )

        self.Vpss_min = float(Vpss_min)

        self.Vpss_max = float(Vpss_max)

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return PSS configuration information.
        """

        return {
            "Kpss": self.Kpss,
            "Tw": self.Tw,
            "Vpss_min": self.Vpss_min,
            "Vpss_max": self.Vpss_max,
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<PSS "
            f"Kpss={self.Kpss:.4f}, "
            f"Tw={self.Tw:.4f}, "
            f"limits=({self.Vpss_min:.4f}, "
            f"{self.Vpss_max:.4f})>"
        )
