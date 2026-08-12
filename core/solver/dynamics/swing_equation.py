```python
"""
GridForge Swing Equation
========================

Reference rotor-motion equations for transient-stability simulation.

The swing equation describes the electromechanical motion of a
synchronous-machine rotor.

State convention
----------------
GridForge uses:

    delta
        Rotor electrical angle [rad].

    omega
        Rotor speed deviation [pu].

        omega = (wr - ws) / ws

where:

    wr = actual rotor electrical angular speed
    ws = synchronous electrical angular speed [rad/s]

Therefore:

    d(delta)/dt = ws * omega

and:

    d(omega)/dt =
        (Pm - Pe - D * omega) / (2H)

Parameters
----------
H:
    Inertia constant [s].

D:
    Damping coefficient in the selected per-unit convention.

frequency:
    System frequency [Hz].

Architectural responsibilities
-------------------------------
This module:

- evaluates rotor-motion equations;
- provides a reusable numerical physics primitive;
- performs no integration;
- owns no dynamic state;
- performs no network solution;
- performs no event handling;
- does not modify generator objects.

The numerical integrator is responsible for advancing the returned
derivatives in time.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ======================================================================
# RESULT CONTRACT
# ======================================================================


@dataclass(frozen=True)
class SwingDerivatives:
    """
    Result of the swing-equation evaluation.

    Parameters
    ----------
    delta:
        Rotor-angle derivative [rad/s].

    omega:
        Rotor-speed-deviation derivative [pu/s].
    """

    delta: float
    omega: float


# ======================================================================
# SWING EQUATION
# ======================================================================


class SwingEquation:
    """
    Classical synchronous-machine swing equation.

    Parameters
    ----------
    H:
        Machine inertia constant [s].

    D:
        Damping coefficient.

    frequency:
        System frequency [Hz].

    Notes
    -----
    ``omega`` is speed deviation in per-unit, not absolute rotor speed.

    Consequently the rotor-angle equation is:

        d(delta)/dt = omega_base * omega

    where:

        omega_base = 2*pi*frequency
    """

    def __init__(
        self,
        H: float,
        D: float = 0.0,
        frequency: float = 50.0,
    ) -> None:

        if not np.isfinite(H):
            raise ValueError(
                "H must be finite."
            )

        if H <= 0.0:
            raise ValueError(
                "H must be greater than zero."
            )

        if not np.isfinite(D):
            raise ValueError(
                "D must be finite."
            )

        if not np.isfinite(
            frequency
        ):
            raise ValueError(
                "frequency must be finite."
            )

        if frequency <= 0.0:
            raise ValueError(
                "frequency must be greater than zero."
            )

        self.H = float(H)

        self.D = float(D)

        self.frequency = float(
            frequency
        )

    # ==================================================================
    # SYSTEM FREQUENCY
    # ==================================================================

    @property
    def omega_base(
        self,
    ) -> float:
        """
        Synchronous electrical angular frequency [rad/s].
        """

        return (
            2.0
            * np.pi
            * self.frequency
        )

    # ==================================================================
    # DERIVATIVES
    # ==================================================================

    def derivatives(
        self,
        delta: float,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> SwingDerivatives:
        """
        Evaluate the classical swing equation.

        Parameters
        ----------
        delta:
            Rotor electrical angle [rad].

        omega:
            Rotor speed deviation [pu].

        Pm:
            Mechanical input power [pu].

        Pe:
            Electrical output power [pu].

        Returns
        -------
        SwingDerivatives
            Rotor-angle and speed-deviation derivatives.
        """

        values = (
            delta,
            omega,
            Pm,
            Pe,
        )

        if not all(
            np.isfinite(value)
            for value in values
        ):
            raise ValueError(
                "Swing-equation inputs "
                "must all be finite."
            )

        ddelta_dt = (
            self.omega_base
            * omega
        )

        domega_dt = (
            Pm
            - Pe
            - self.D * omega
        ) / (
            2.0 * self.H
        )

        result = SwingDerivatives(
            delta=float(
                ddelta_dt
            ),
            omega=float(
                domega_dt
            ),
        )

        if not np.isfinite(
            result.delta
        ):
            raise FloatingPointError(
                "Swing-equation delta "
                "derivative is non-finite."
            )

        if not np.isfinite(
            result.omega
        ):
            raise FloatingPointError(
                "Swing-equation omega "
                "derivative is non-finite."
            )

        return result

    # ==================================================================
    # ACCELERATION ONLY
    # ==================================================================

    def acceleration(
        self,
        omega: float,
        Pm: float,
        Pe: float,
    ) -> float:
        """
        Return rotor speed-deviation acceleration.

        This convenience method is useful for machine models that
        already have the rotor-angle derivative available.
        """

        return self.derivatives(
            delta=0.0,
            omega=omega,
            Pm=Pm,
            Pe=Pe,
        ).omega


__all__ = [
    "SwingDerivatives",
    "SwingEquation",
]
```
