```python
"""
GridForge Automatic Voltage Regulator Model
============================================

File:
    core/model/avr.py

Defines the GridForge Automatic Voltage Regulator (AVR) model.

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
--------
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

The AVR model deliberately contains no numerical integration
or simulation-state ownership.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math


class AVR:
    """
    First-order Automatic Voltage Regulator.

    The AVR does not integrate its internal state. The dynamic
    solver supplies the current Efd state and integrates the
    returned derivative.

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

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        Ka: float = 200.0,
        Ta: float = 0.02,
        Vref: float = 1.0,
        Efd_min: float = 0.0,
        Efd_max: float = 5.0,
    ) -> None:
        """
        Initialize the AVR model.
        """

        self.Ka = float(Ka)
        self.Ta = float(Ta)
        self.Vref = float(Vref)

        self.Efd_min = float(Efd_min)
        self.Efd_max = float(Efd_max)

        self._validate()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate(self) -> None:
        """
        Validate AVR parameters.
        """

        if not math.isfinite(self.Ka):
            raise ValueError(
                "AVR gain Ka must be finite."
            )

        if self.Ka <= 0.0:
            raise ValueError(
                "AVR gain Ka must be greater than zero."
            )

        if not math.isfinite(self.Ta):
            raise ValueError(
                "AVR time constant Ta must be finite."
            )

        if self.Ta <= 0.0:
            raise ValueError(
                "AVR time constant Ta must be greater than zero."
            )

        if not math.isfinite(self.Vref):
            raise ValueError(
                "AVR voltage reference Vref must be finite."
            )

        if not math.isfinite(self.Efd_min):
            raise ValueError(
                "AVR Efd_min must be finite."
            )

        if not math.isfinite(self.Efd_max):
            raise ValueError(
                "AVR Efd_max must be finite."
            )

        if self.Efd_min > self.Efd_max:
            raise ValueError(
                "Efd_min must not be greater than Efd_max."
            )

    # =========================================================
    # DIFFERENTIAL EQUATION
    # =========================================================

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

        Efd = float(Efd)
        Vt = float(Vt)
        Vpss = float(Vpss)

        if not math.isfinite(Efd):
            raise ValueError(
                "AVR Efd state must be finite."
            )

        if not math.isfinite(Vt):
            raise ValueError(
                "AVR terminal voltage Vt must be finite."
            )

        if not math.isfinite(Vpss):
            raise ValueError(
                "AVR PSS input Vpss must be finite."
            )

        error = (
            self.Vref
            - Vt
            + Vpss
        )

        return (
            self.Ka * error
            - Efd
        ) / self.Ta

    # =========================================================
    # OUTPUT
    # =========================================================

    def output(
        self,
        Efd: float,
    ) -> float:
        """
        Return the limited excitation output.

        Parameters
        ----------
        Efd:
            Current excitation state.

        Returns
        -------
        float
            Limited field voltage.
        """

        return self.limit(Efd)

    # =========================================================
    # COMBINED EVALUATION
    # =========================================================

    def evaluate(
        self,
        Efd: float,
        Vt: float,
        Vpss: float = 0.0,
    ) -> tuple[float, float]:
        """
        Evaluate the AVR derivative and output.

        Returns
        -------
        tuple[float, float]
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

    # =========================================================
    # LIMITER
    # =========================================================

    def limit(
        self,
        Efd: float,
    ) -> float:
        """
        Apply excitation-voltage limits.

        Parameters
        ----------
        Efd:
            Excitation state.

        Returns
        -------
        float
            Limited excitation voltage.
        """

        Efd = float(Efd)

        if not math.isfinite(Efd):
            raise ValueError(
                "AVR Efd value must be finite."
            )

        return max(
            self.Efd_min,
            min(
                Efd,
                self.Efd_max,
            ),
        )

    # =========================================================
    # INITIAL STATE
    # =========================================================

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

        Vt = float(Vt)
        Vpss = float(Vpss)

        if not math.isfinite(Vt):
            raise ValueError(
                "Initial terminal voltage Vt must be finite."
            )

        if not math.isfinite(Vpss):
            raise ValueError(
                "Initial PSS signal Vpss must be finite."
            )

        Efd = self.Ka * (
            self.Vref
            - Vt
            + Vpss
        )

        return self.limit(Efd)

    # =========================================================
    # RESET
    # =========================================================

    def reset(
        self,
        Vt: float = 1.0,
        Vpss: float = 0.0,
    ) -> float:
        """
        Return the steady-state initial excitation value.

        The dynamic solver should use this value when resetting
        the simulation.
        """

        return self.initial_state(
            Vt=Vt,
            Vpss=Vpss,
        )

    # =========================================================
    # PARAMETER MANAGEMENT
    # =========================================================

    def set_gain(
        self,
        Ka: float,
    ) -> None:
        """
        Update AVR gain.
        """

        Ka = float(Ka)

        if not math.isfinite(Ka):
            raise ValueError(
                "AVR gain Ka must be finite."
            )

        if Ka <= 0.0:
            raise ValueError(
                "AVR gain Ka must be greater than zero."
            )

        self.Ka = Ka

    def set_time_constant(
        self,
        Ta: float,
    ) -> None:
        """
        Update AVR time constant.
        """

        Ta = float(Ta)

        if not math.isfinite(Ta):
            raise ValueError(
                "AVR time constant Ta must be finite."
            )

        if Ta <= 0.0:
            raise ValueError(
                "AVR time constant Ta must be greater than zero."
            )

        self.Ta = Ta

    def set_reference(
        self,
        Vref: float,
    ) -> None:
        """
        Update voltage reference.
        """

        Vref = float(Vref)

        if not math.isfinite(Vref):
            raise ValueError(
                "AVR voltage reference Vref must be finite."
            )

        self.Vref = Vref

    def set_limits(
        self,
        Efd_min: float,
        Efd_max: float,
    ) -> None:
        """
        Update excitation limits.
        """

        Efd_min = float(Efd_min)
        Efd_max = float(Efd_max)

        if not math.isfinite(Efd_min):
            raise ValueError(
                "AVR Efd_min must be finite."
            )

        if not math.isfinite(Efd_max):
            raise ValueError(
                "AVR Efd_max must be finite."
            )

        if Efd_min > Efd_max:
            raise ValueError(
                "Efd_min must not be greater than Efd_max."
            )

        self.Efd_min = Efd_min
        self.Efd_max = Efd_max

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return AVR configuration information.
        """

        return {
            "type": "AVR",
            "model": "FIRST_ORDER",
            "Ka": self.Ka,
            "Ta": self.Ta,
            "Vref": self.Vref,
            "Efd_min": self.Efd_min,
            "Efd_max": self.Efd_max,
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<AVR "
            f"Ka={self.Ka:.4f}, "
            f"Ta={self.Ta:.6f}, "
            f"Vref={self.Vref:.4f}, "
            f"limits=("
            f"{self.Efd_min:.4f}, "
            f"{self.Efd_max:.4f})>"
        )
```
