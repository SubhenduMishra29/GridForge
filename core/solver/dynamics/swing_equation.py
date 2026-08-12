"""
GridForge Swing Equation
========================

Reusable synchronous-machine rotor dynamics.

Responsibilities
----------------
- Evaluate the classical swing equation.
- Support inertia and damping.
- Provide rotor-angle and speed-deviation derivatives.
- Provide a pure, stateless numerical formulation.

Non-responsibilities
--------------------
This module does NOT:

- store simulation state;
- perform numerical integration;
- solve the electrical network;
- calculate electrical power;
- implement AVR, governor, or PSS;
- process simulation events;
- manage multiple machines.

Classical swing equation
------------------------

    dδ/dt = ω

    dω/dt = (Pm - Pe - Dω) / (2H)

where:

    δ  = rotor electrical angle [rad]
    ω  = speed deviation [pu]
    Pm = mechanical input power [pu]
    Pe = electrical output power [pu]
    H  = inertia constant [s]
    D  = damping coefficient

The formulation assumes that ``omega`` represents speed deviation
from synchronous speed:

    ω = Δω

Therefore, rotor angle is integrated using:

    dδ/dt = Δω

This component is deliberately independent of the numerical
integration method. RK4, implicit trapezoidal, or another integrator
may call this equation evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ======================================================================
# ERRORS
# ======================================================================


class SwingEquationError(
    ValueError
):
    """Base exception for swing-equation errors."""


# ======================================================================
# RESULT
# ======================================================================


@dataclass(frozen=True)
class SwingDerivatives:
    """
    Result of the swing-equation evaluation.

    Attributes
    ----------
    delta:
        Rotor-angle derivative dδ/dt [rad/s in normalized formulation].

    omega:
        Speed-deviation derivative dω/dt.
    """

    delta: float
    omega: float

    def as_array(
        self,
    ) -> np.ndarray:
        """
        Return derivatives as a numerical state vector.

        Ordering:

            [dδ/dt, dω/dt]
        """

        return np.array(
            [
                self.delta,
                self.omega,
            ],
            dtype=float,
        )


# ======================================================================
# SWING EQUATION
# ======================================================================


class SwingEquation:
    """
    Classical synchronous-machine swing equation.

    Parameters
    ----------
    H:
        Inertia constant [s].

    D:
        Damping coefficient.

    Notes
    -----
    The class is intentionally stateless with respect to the dynamic
    trajectory. ``delta`` and ``omega`` are supplied to ``derivatives()``
    and are not stored internally.

    This makes the component safe to use with vectorized solvers,
    predictor-corrector methods, RK4, and implicit methods.
    """

    def __init__(
        self,
        H: float,
        D: float = 0.0,
    ) -> None:

        self._validate_parameter(
            "H",
            H,
            strictly_positive=True,
        )

        self._validate_parameter(
            "D",
            D,
            strictly_positive=False,
        )

        if D < 0.0:

            raise SwingEquationError(
                "D cannot be negative."
            )

        self._H = float(H)
        self._D = float(D)

    # ==================================================================
    # PARAMETERS
    # ==================================================================

    @property
    def H(
        self,
    ) -> float:
        """Inertia constant [s]."""

        return self._H

    @property
    def D(
        self,
    ) -> float:
        """Damping coefficient."""

        return self._D

    @property
    def M(
        self,
    ) -> float:
        """
        Equivalent inertia coefficient.

        M = 2H
        """

        return 2.0 * self._H

    # ==================================================================
    # DIFFERENTIAL EQUATIONS
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
            Rotor angle [rad].

        omega:
            Rotor speed deviation [pu].

        Pm:
            Mechanical input power [pu].

        Pe:
            Electrical active power output [pu].

        Returns
        -------
        SwingDerivatives
            ``dδ/dt`` and ``dω/dt``.

        Notes
        -----
        ``delta`` is accepted explicitly because it is part of the
        machine state, although it does not appear directly in the
        classical first-order rotor equations.
        """

        self._validate_finite(
            "delta",
            delta,
        )

        self._validate_finite(
            "omega",
            omega,
        )

        self._validate_finite(
            "Pm",
            Pm,
        )

        self._validate_finite(
            "Pe",
            Pe,
        )

        ddelta_dt = float(
            omega
        )

        domega_dt = (
            float(Pm)
            - float(Pe)
            - self._D * float(omega)
        ) / self.M

        result = SwingDerivatives(
            delta=ddelta_dt,
            omega=domega_dt,
        )

        if not np.all(
            np.isfinite(
                result.as_array()
            )
        ):

            raise SwingEquationError(
                "Swing-equation derivative "
                "calculation produced "
                "non-finite values."
            )

        return result

    # ==================================================================
    # ARRAY INTERFACE
    # ==================================================================

    def derivative_vector(
        self,
        state: np.ndarray,
        Pm: float,
        Pe: float,
    ) -> np.ndarray:
        """
        Evaluate the swing equation directly from a rotor state vector.

        Parameters
        ----------
        state:
            Rotor state ordered as:

                [delta, omega]

        Pm:
            Mechanical input power [pu].

        Pe:
            Electrical active power output [pu].

        Returns
        -------
        numpy.ndarray
            Derivative vector ordered as:

                [d_delta/dt, d_omega/dt]
        """

        values = np.asarray(
            state,
            dtype=float,
        )

        if values.ndim != 1:

            raise SwingEquationError(
                "Rotor state must be "
                "one-dimensional."
            )

        if values.size != 2:

            raise SwingEquationError(
                "Rotor state must contain "
                "exactly two values: "
                "[delta, omega]."
            )

        result = self.derivatives(
            delta=values[0],
            omega=values[1],
            Pm=Pm,
            Pe=Pe,
        )

        return result.as_array()

    # ==================================================================
    # POWER ACCELERATION
    # ==================================================================

    def accelerating_power(
        self,
        Pm: float,
        Pe: float,
    ) -> float:
        """
        Return accelerating power:

            Pa = Pm - Pe
        """

        self._validate_finite(
            "Pm",
            Pm,
        )

        self._validate_finite(
            "Pe",
            Pe,
        )

        return float(
            Pm - Pe
        )

    def acceleration(
        self,
        Pm: float,
        Pe: float,
        omega: float = 0.0,
    ) -> float:
        """
        Return rotor speed-deviation acceleration.

            dω/dt =
                (Pm - Pe - Dω) / (2H)
        """

        self._validate_finite(
            "Pm",
            Pm,
        )

        self._validate_finite(
            "Pe",
            Pe,
        )

        self._validate_finite(
            "omega",
            omega,
        )

        return float(
            (
                Pm
                - Pe
                - self._D * omega
            )
            / self.M
        )

    # ==================================================================
    # VALIDATION
    # ==================================================================

    @staticmethod
    def _validate_parameter(
        name: str,
        value: float,
        *,
        strictly_positive: bool,
    ) -> None:
        """
        Validate a scalar model parameter.
        """

        try:

            numeric = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise SwingEquationError(
                f"{name} must be "
                "numeric."
            ) from exc

        if not np.isfinite(
            numeric
        ):

            raise SwingEquationError(
                f"{name} must be finite."
            )

        if (
            strictly_positive
            and numeric <= 0.0
        ):

            raise SwingEquationError(
                f"{name} must be "
                "greater than zero."
            )

    @staticmethod
    def _validate_finite(
        name: str,
        value: float,
    ) -> None:
        """
        Validate a dynamic scalar.
        """

        try:

            numeric = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise SwingEquationError(
                f"{name} must be numeric."
            ) from exc

        if not np.isfinite(
            numeric
        ):

            raise SwingEquationError(
                f"{name} must be finite."
            )


# ======================================================================
# CONVENIENCE FUNCTION
# ======================================================================


def swing_derivatives(
    delta: float,
    omega: float,
    Pm: float,
    Pe: float,
    H: float,
    D: float = 0.0,
) -> tuple[
    float,
    float,
]:
    """
    Evaluate the classical swing equation without explicitly creating
    a ``SwingEquation`` instance.

    Returns
    -------
    tuple
        ``(d_delta_dt, d_omega_dt)``
    """

    equation = SwingEquation(
        H=H,
        D=D,
    )

    result = equation.derivatives(
        delta=delta,
        omega=omega,
        Pm=Pm,
        Pe=Pe,
    )

    return (
        result.delta,
        result.omega,
    )


__all__ = [
    "SwingEquationError",
    "SwingDerivatives",
    "SwingEquation",
    "swing_derivatives",
]
```
