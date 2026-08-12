"""
GridForge Dynamic Integrators
=============================

Numerical time-integration methods for GridForge dynamic simulation.

Supported methods
-----------------
- RK4
    Explicit classical fourth-order Runge-Kutta method.

- Trapezoidal
    Implicit trapezoidal integration using iterative correction.

Responsibilities
----------------
- Advance differential state vectors in time.
- Provide a common integration interface.
- Remain independent of physical dynamic models.
- Operate on NumPy state vectors.

This module does NOT:
- solve network algebraic equations
- evaluate generator equations
- manage events
- own simulation state
- know about buses or equipment
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import numpy as np


DerivativeFunction = Callable[
    [np.ndarray, float],
    np.ndarray,
]


class IntegrationError(RuntimeError):
    """Raised when an integration step cannot be completed."""


class BaseIntegrator(ABC):
    """
    Abstract interface for dynamic-system integrators.
    """

    @abstractmethod
    def step(
        self,
        x: np.ndarray,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
    ) -> np.ndarray:
        """
        Advance the state by one time step.

        Parameters
        ----------
        x:
            Current state vector.

        derivative:
            Callable returning dx/dt.

            Signature:
                derivative(x, t) -> dx/dt

        t:
            Current simulation time.

        dt:
            Integration time step.

        Returns
        -------
        numpy.ndarray
            State at t + dt.
        """
        raise NotImplementedError


class RK4Integrator(BaseIntegrator):
    """
    Classical fourth-order Runge-Kutta integrator.

    Suitable for explicit dynamic models such as:

    - rotor dynamics
    - excitation systems
    - governors
    - PSS models
    - other explicit differential equations
    """

    def step(
        self,
        x: np.ndarray,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
    ) -> np.ndarray:

        _validate_step_inputs(
            x,
            t,
            dt,
        )

        x = np.asarray(
            x,
            dtype=float,
        )

        k1 = _evaluate(
            derivative,
            x,
            t,
        )

        k2 = _evaluate(
            derivative,
            x + 0.5 * dt * k1,
            t + 0.5 * dt,
        )

        k3 = _evaluate(
            derivative,
            x + 0.5 * dt * k2,
            t + 0.5 * dt,
        )

        k4 = _evaluate(
            derivative,
            x + dt * k3,
            t + dt,
        )

        x_new = x + (
            dt / 6.0
        ) * (
            k1
            + 2.0 * k2
            + 2.0 * k3
            + k4
        )

        _validate_derivative_shape(
            x_new,
            x,
        )

        return x_new


class TrapezoidalIntegrator(BaseIntegrator):
    """
    Implicit trapezoidal integrator.

    Solves approximately:

        x(n+1) =
            x(n)
            + dt/2 * [
                f(x(n), t(n))
                + f(x(n+1), t(n+1))
            ]

    The nonlinear implicit equation is solved by fixed-point
    iteration.

    Notes
    -----
    This implementation intentionally does not claim to be a
    Newton-based DAE solver. A future fully implicit DAE solver may
    provide Jacobian-based Newton iterations separately.
    """

    def __init__(
        self,
        tolerance: float = 1.0e-8,
        max_iterations: int = 20,
    ) -> None:

        if tolerance <= 0.0:
            raise ValueError(
                "Tolerance must be greater than zero."
            )

        if max_iterations < 1:
            raise ValueError(
                "max_iterations must be at least 1."
            )

        self.tolerance = float(
            tolerance
        )

        self.max_iterations = int(
            max_iterations
        )

    def step(
        self,
        x: np.ndarray,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
    ) -> np.ndarray:

        _validate_step_inputs(
            x,
            t,
            dt,
        )

        x = np.asarray(
            x,
            dtype=float,
        )

        f_old = _evaluate(
            derivative,
            x,
            t,
        )

        t_new = t + dt

        # Explicit Euler prediction.
        x_new = (
            x
            + dt * f_old
        )

        for _ in range(
            self.max_iterations
        ):

            f_new = _evaluate(
                derivative,
                x_new,
                t_new,
            )

            target = (
                x
                + 0.5 * dt * (
                    f_old
                    + f_new
                )
            )

            correction = (
                target
                - x_new
            )

            x_new = (
                x_new
                + correction
            )

            if np.linalg.norm(
                correction,
                ord=np.inf,
            ) <= self.tolerance:

                return x_new

        raise IntegrationError(
            "Trapezoidal integration failed "
            "to converge within "
            f"{self.max_iterations} iterations."
        )


class Integrator:
    """
    Common GridForge integration interface.

    Parameters
    ----------
    method:
        Integration method.

        Supported values:
        - ``"RK4"``
        - ``"TRAPEZOIDAL"``
    """

    METHODS = {
        "RK4": RK4Integrator,
        "TRAPEZOIDAL": TrapezoidalIntegrator,
    }

    def __init__(
        self,
        method: str = "RK4",
        **kwargs,
    ) -> None:

        method_key = method.upper()

        try:
            integrator_class = (
                self.METHODS[method_key]
            )
        except KeyError as exc:
            supported = ", ".join(
                self.METHODS
            )

            raise ValueError(
                f"Unknown integration method "
                f"'{method}'. "
                f"Supported methods: {supported}."
            ) from exc

        self.method = method_key

        self.solver = integrator_class(
            **kwargs
        )

    def step(
        self,
        x: np.ndarray,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
    ) -> np.ndarray:
        """
        Advance the state by one integration step.
        """

        return self.solver.step(
            x=x,
            derivative=derivative,
            t=t,
            dt=dt,
        )


def _evaluate(
    derivative: DerivativeFunction,
    x: np.ndarray,
    t: float,
) -> np.ndarray:
    """
    Evaluate and validate a derivative function.
    """

    result = np.asarray(
        derivative(x, t),
        dtype=float,
    )

    _validate_derivative_shape(
        result,
        x,
    )

    if not np.all(
        np.isfinite(result)
    ):
        raise IntegrationError(
            "Derivative contains "
            "non-finite values."
        )

    return result


def _validate_derivative_shape(
    result: np.ndarray,
    x: np.ndarray,
) -> None:

    if result.shape != x.shape:
        raise IntegrationError(
            "Derivative/state shape mismatch: "
            f"state shape={x.shape}, "
            f"derivative shape={result.shape}."
        )


def _validate_step_inputs(
    x: np.ndarray,
    t: float,
    dt: float,
) -> None:

    if not isinstance(
        x,
        np.ndarray,
    ):
        raise TypeError(
            "State vector must be a NumPy array."
        )

    if x.ndim != 1:
        raise ValueError(
            "State vector must be one-dimensional."
        )

    if not np.all(
        np.isfinite(x)
    ):
        raise ValueError(
            "State vector contains "
            "non-finite values."
        )

    if not np.isfinite(t):
        raise ValueError(
            "Simulation time must be finite."
        )

    if not np.isfinite(dt):
        raise ValueError(
            "Time step must be finite."
        )

    if dt <= 0.0:
        raise ValueError(
            "Time step must be greater than zero."
        )
