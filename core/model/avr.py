"""
GridForge AVR Model
===================

File:
    core/model/avr.py

Defines the Automatic Voltage Regulator (AVR) model.

Purpose
-------
The AVR represents the excitation-control dynamics of a synchronous
generator.

Basic first-order AVR equation:

    dEfd/dt =
        [ Ka * (Vref - Vt + Vpss) - Efd ] / Ta

Where:

    Efd  = field/excitation voltage
    Vt   = generator terminal-voltage magnitude
    Vref = voltage reference
    Vpss = supplementary stabilizing signal from the PSS
    Ka   = AVR gain
    Ta   = AVR time constant

Architecture
------------
The AVR does NOT perform numerical integration.

The dynamic / DAE solver owns:

    - Dynamic state vector
    - State integration
    - Time stepping
    - Initial conditions
    - Differential-algebraic solution

The AVR provides:

    - Differential equation
    - Output limiting
    - Initial-state calculation
    - Parameter management

Used by
-------
    Generator
    PSS
    Dynamic Solver

Future Extensions
-----------------
The model can later support:

    - IEEE excitation-system models
    - Exciter saturation
    - Ceiling voltage
    - Rate limiting
    - Field current limits
    - Transducer dynamics
    - Over-excitation limiter
    - Under-excitation limiter

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class AVR:
    """
    First-order Automatic Voltage Regulator.

    The AVR does not integrate its internal state. The dynamic solver
    supplies the current Efd state and integrates the returned
    derivative.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        Ka: float = 200.0,
        Ta: float = 0.02,
        Vref: float = 1.0,
        Efd_min: float = 0.0,
        Efd_max: float = 5.0,
    ):
        """
        Initialize the AVR model.

        Parameters
        ----------
        Ka:
            AVR gain.

        Ta:
            AVR time constant in seconds.

        Vref:
            Voltage reference in per-unit.

        Efd_min:
            Minimum excitation voltage.

        Efd_max:
            Maximum excitation voltage.
        """

        # ---------------------------------------------------------
        # Validation
        # ---------------------------------------------------------

        if Ta <= 0.0:
            raise ValueError(
                "AVR time constant Ta must be greater than zero."
            )

        if Efd_min > Efd_max:
            raise ValueError(
                "Efd_min must not be greater than Efd_max."
            )

        # ---------------------------------------------------------
        # Parameters
        # ---------------------------------------------------------

        self.Ka = float(Ka)

        self.Ta = float(Ta)

        self.Vref = float(Vref)

        # ---------------------------------------------------------
        # Excitation limits
        # ---------------------------------------------------------

        self.Efd_min = float(Efd_min)

        self.Efd_max = float(Efd_max)

    # =============================================================
    # DIFFERENTIAL EQUATION
    # =============================================================

    def derivative(
        self,
        Efd: float,
        Vt: float,
        Vpss: float = 0.0,
    ) -> float:
        """
        Calculate the AVR state derivative.

        Equation:

            dEfd/dt =
                [Ka * (Vref - Vt + Vpss) - Efd] / Ta

        Parameters
        ----------
        Efd:
            Current excitation state.

        Vt:
            Generator terminal-voltage magnitude.

        Vpss:
            Supplementary stabilizing signal from the PSS.

        Returns
        -------
        float
            dEfd/dt.
        """

        error = (
            self.Vref
            - float(Vt)
            + float(Vpss)
        )

        return (
            self.Ka * error
            - float(Efd)
        ) / self.Ta

    # =============================================================
    # OUTPUT
    # =============================================================

    def output(
        self,
        Efd: float,
    ) -> float:
        """
        Return the limited excitation output.

        Parameters
        ----------
        Efd:
            Current AVR state.

        Returns
        -------
        float
            Limited field voltage.
        """

        return self.limit(Efd)

    # =============================================================
    # COMBINED EVALUATION
    # =============================================================

    def evaluate(
        self,
        Efd: float,
        Vt: float,
        Vpss: float = 0.0,
    ) -> tuple[float, float]:
        """
        Evaluate AVR derivative and limited output.

        Returns
        -------
        tuple
            (dEfd_dt, Efd_output)

        Notes
        -----
        No numerical integration occurs here.
        """

        dEfd_dt = self.derivative(
            Efd=Efd,
            Vt=Vt,
            Vpss=Vpss,
        )

        Efd_output = self.output(Efd)

        return dEfd_dt, Efd_output

    # =============================================================
    # LIMITER
    # =============================================================

    def limit(
        self,
        Efd: float,
    ) -> float:
        """
        Apply excitation-voltage limits.
        """

        return max(
            self.Efd_min,
            min(
                float(Efd),
                self.Efd_max,
            ),
        )

    # =============================================================
    # INITIAL STATE
    # =============================================================

    def initial_state(
        self,
        Vt: float = 1.0,
        Vpss: float = 0.0,
    ) -> float:
        """
        Calculate the steady-state initial Efd.

        At steady state:

            dEfd/dt = 0

        Therefore:

            Efd = Ka * (Vref - Vt + Vpss)

        The result is passed through the excitation limiter.

        Parameters
        ----------
        Vt:
            Initial terminal voltage.

        Vpss:
            Initial stabilizing signal.

        Returns
        -------
        float
            Initial excitation state.
        """

        Efd = self.Ka * (
            self.Vref
            - float(Vt)
            + float(Vpss)
        )

        return self.limit(Efd)

    # =============================================================
    # RESET
    # =============================================================

    def reset(
        self,
        Vt: float = 1.0,
        Vpss: float = 0.0,
    ) -> float:
        """
        Return the initial excitation state.

        The dynamic solver should use this value when resetting
        the simulation.
        """

        return self.initial_state(
            Vt=Vt,
            Vpss=Vpss,
        )

    # =============================================================
    # PARAMETER MANAGEMENT
    # =============================================================

    def set_gain(
        self,
        Ka: float,
    ) -> None:
        """
        Update AVR gain.
        """

        self.Ka = float(Ka)

    def set_time_constant(
        self,
        Ta: float,
    ) -> None:
        """
        Update AVR time constant.
        """

        if Ta <= 0.0:
            raise ValueError(
                "AVR time constant Ta must be greater than zero."
            )

        self.Ta = float(Ta)

    def set_reference(
        self,
        Vref: float,
    ) -> None:
        """
        Update voltage reference.
        """

        self.Vref = float(Vref)

    def set_limits(
        self,
        Efd_min: float,
        Efd_max: float,
    ) -> None:
        """
        Update excitation limits.
        """

        if Efd_min > Efd_max:
            raise ValueError(
                "Efd_min must not be greater than Efd_max."
            )

        self.Efd_min = float(Efd_min)
        self.Efd_max = float(Efd_max)

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict:
        """
        Return AVR configuration information.
        """

        return {
            "Ka": self.Ka,
            "Ta": self.Ta,
            "Vref": self.Vref,
            "Efd_min": self.Efd_min,
            "Efd_max": self.Efd_max,
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<AVR "
            f"Ka={self.Ka:.4f}, "
            f"Ta={self.Ta:.6f}, "
            f"Vref={self.Vref:.4f}, "
            f"limits=({self.Efd_min:.4f}, "
            f"{self.Efd_max:.4f})>"
        )
