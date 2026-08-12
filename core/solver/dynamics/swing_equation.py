"""
GridForge Swing Equation
========================

Canonical rotor-dynamics formulation for GridForge dynamic
and transient-stability simulations.

The model uses rotor-speed deviation from synchronous speed:

    omega = (omega_r - omega_s) / omega_s

Therefore:

    omega = 0

represents synchronous speed.

Classical swing equations
-------------------------

    d(delta)/dt = omega_s * omega

    d(omega)/dt =
        (Pm - Pe - D * omega) / (2 * H)

where:

    delta
        Rotor electrical angle [rad].

    omega
        Per-unit rotor-speed deviation.

    omega_s
        Synchronous angular speed [rad/s].

    H
        Inertia constant [s].

    D
        Damping coefficient [pu power / pu speed].

    Pm
        Mechanical input power [pu].

    Pe
        Electrical output power [pu].

Responsibilities
----------------
- Define the canonical classical swing equation.
- Evaluate rotor-angle and rotor-speed derivatives.
- Provide acceleration calculations.
- Maintain no simulation state.

This module does NOT:
- integrate states
- solve the network
- model generators
- implement AVR/GOV/PSS
- manage events
- modify GridForge network state
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SwingEquation:
    """
    Classical swing-equation model.

    Parameters
    ----------
    H:
        Generator inertia constant in seconds.

    D:
        Damping coefficient in per-unit power per per-unit
        speed deviation.

    omega_s:
        Synchronous angular frequency in rad/s.

        For a system with nominal frequency ``f_nom``:

            omega_s = 2 * pi * f_nom
    """

    H: float
    D: float = 0.0
    omega_s: float = 2.0 * np.pi * 50.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.H):
            raise ValueError(
                "Inertia constant H must be finite."
            )

        if self.H <= 0.0:
            raise ValueError(
                "Inertia constant H must be greater than zero."
            )

        if not np.isfinite(self.D):
            raise ValueError(
                "Damping coefficient D must be finite."
            )

        if self.D < 0.0:
            raise ValueError(
                "Damping coefficient D must not be negative."
            )

        if not np.isfinite(self.omega_s):
            raise ValueError(
                "Synchronous angular frequency must be finite."
            )

        if self.omega_s <= 0.0:
            raise ValueError(
                "Synchronous angular frequency must be "
                "greater than zero."
            )

    # =========================================================
    # DIFFERENTIAL EQUATIONS
    # =========================================================

    def derivatives(
        self,
        delta: float,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> tuple[float, float]:
        """
        Evaluate the classical swing equations.

        Parameters
        ----------
        delta:
            Rotor electrical angle [rad].

        omega:
            Per-unit rotor-speed deviation.

        Pm:
            Mechanical input power [pu].

        Pe:
            Electrical output power [pu].

        Returns
        -------
        tuple[float, float]
            ``(d_delta_dt, d_omega_dt)``.
        """

        self._validate_numeric(
            delta,
            "delta",
        )

        self._validate_numeric(
            omega,
            "omega",
        )

        self._validate_numeric(
            Pm,
            "Pm",
        )

        self._validate_numeric(
            Pe,
            "Pe",
        )

        d_delta_dt = (
            self.omega_s
            * omega
        )

        d_omega_dt = (
            Pm
            - Pe
            - self.D * omega
        ) / (
            2.0 * self.H
        )

        return (
            d_delta_dt,
            d_omega_dt,
        )

    # =========================================================
    # ACCELERATION
    # =========================================================

    def acceleration(
        self,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> float:
        """
        Return rotor-speed acceleration.

        This is equivalent to the second component returned by
        :meth:`derivatives`.
        """

        _, d_omega_dt = self.derivatives(
            delta=0.0,
            omega=omega,
            Pm=Pm,
            Pe=Pe,
        )

        return d_omega_dt

    # =========================================================
    # ELECTROMECHANICAL POWER BALANCE
    # =========================================================

    def power_imbalance(
        self,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> float:
        """
        Return the accelerating-power imbalance.

        Positive value means the machine is accelerating.
        """

        self._validate_numeric(
            omega,
            "omega",
        )

        self._validate_numeric(
            Pm,
            "Pm",
        )

        self._validate_numeric(
            Pe,
            "Pe",
        )

        return (
            Pm
            - Pe
            - self.D * omega
        )

    # =========================================================
    # INITIAL STEADY-STATE CHECK
    # =========================================================

    def steady_state_residual(
        self,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> float:
        """
        Return the swing-equation steady-state residual.

        A machine is in electromechanical steady state when:

            omega = 0
            Pm = Pe

        with damping therefore also equal to zero.
        """

        return self.power_imbalance(
            omega=omega,
            Pm=Pm,
            Pe=Pe,
        )

    def is_steady_state(
        self,
        omega: float,
        Pm: float,
        Pe: float,
        tolerance: float = 1.0e-8,
    ) -> bool:
        """
        Check whether the rotor is in electromechanical steady state.
        """

        if tolerance <= 0.0:
            raise ValueError(
                "Tolerance must be greater than zero."
            )

        residual = self.steady_state_residual(
            omega=omega,
            Pm=Pm,
            Pe=Pe,
        )

        return (
            abs(omega) <= tolerance
            and abs(residual) <= tolerance
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    @staticmethod
    def _validate_numeric(
        value: float,
        name: str,
    ) -> None:

        if not isinstance(
            value,
            (int, float, np.number),
        ):
            raise TypeError(
                f"{name} must be numeric."
            )

        if not np.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )
