```python id="7q2m4c"
"""
GridForge Dynamic Integrators
=============================

Numerical time-integration methods used by the GridForge dynamics
solver.

Supported methods
-----------------
RK4
    Classical explicit fourth-order Runge-Kutta integration.

TRAPEZOIDAL
    Implicit trapezoidal integration using nonlinear fixed-point
    iteration.

Architectural responsibilities
-------------------------------
Integrators:

- operate only on numerical state vectors;
- evaluate a supplied derivative function;
- advance the state in time;
- perform no network calculations;
- perform no machine calculations;
- perform no event processing;
- own no simulation state.

Derivative contract
-------------------
The derivative callable must have the form:

    derivative(x, t) -> dx/dt

where:

    x = numerical state vector
    t = simulation time

The derivative function must not modify ``x``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import numpy as np


# ======================================================================
# TYPES
# ======================================================================


DerivativeFunction = Callable[
    [np.ndarray, float],
    np.ndarray,
]


# ======================================================================
# ERRORS
# ======================================================================


class IntegrationError(RuntimeError):
    """Raised when numerical integration fails."""


# ======================================================================
# BASE INTEGRATOR
# ======================================================================


class BaseIntegrator(ABC):
    """
    Common interface for GridForge time integrators.
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
            Function returning dx/dt.

        t:
            Current simulation time.

        dt:
            Integration step size.

        Returns
        -------
        numpy.ndarray
            State at ``t + dt``.
        """
        raise NotImplementedError

    @staticmethod
    def _validate_inputs(
        x: np.ndarray,
        t: float,
        dt: float,
    ) -> np.ndarray:
        """
        Validate common integration inputs.
        """

        state = np.asarray(
            x,
            dtype=float,
        )

        if state.ndim != 1:
            raise IntegrationError(
                "State vector must be "
                "one-dimensional."
            )

        if not np.all(
            np.isfinite(state)
        ):
            raise IntegrationError(
                "State vector contains "
                "non-finite values."
            )

        if not np.isfinite(t):
            raise IntegrationError(
                "Integration time must "
                "be finite."
            )

        if not np.isfinite(dt):
            raise IntegrationError(
                "Integration step must "
                "be finite."
            )

        if dt <= 0.0:
            raise IntegrationError(
                "Integration step must "
                "be greater than zero."
            )

        return state

    @staticmethod
    def _evaluate_derivative(
        derivative: DerivativeFunction,
        x: np.ndarray,
        t: float,
        expected_size: int,
    ) -> np.ndarray:
        """
        Evaluate and validate a derivative function.
        """

        dx = np.asarray(
            derivative(x, t),
            dtype=float,
        )

        if dx.ndim != 1:
            raise IntegrationError(
                "Derivative function must "
                "return a one-dimensional "
                "vector."
            )

        if dx.size != expected_size:
            raise IntegrationError(
                "Derivative vector size "
                f"mismatch: expected "
                f"{expected_size}, received "
                f"{dx.size}."
            )

        if not np.all(
            np.isfinite(dx)
        ):
            raise IntegrationError(
                "Derivative vector contains "
                "non-finite values."
            )

        return dx


# ======================================================================
# RK4
# ======================================================================


class RK4Integrator(
    BaseIntegrator
):
    """
    Classical fourth-order Runge-Kutta integrator.

    The method evaluates:

        k1 = f(x_n, t_n)

        k2 = f(
            x_n + dt/2*k1,
            t_n + dt/2
        )

        k3 = f(
            x_n + dt/2*k2,
            t_n + dt/2
        )

        k4 = f(
            x_n + dt*k3,
            t_n + dt
        )

    and:

        x_(n+1)
            =
        x_n
        +
        dt/6 * (
            k1 + 2*k2 + 2*k3 + k4
        )
    """

    def step(
        self,
        x: np.ndarray,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
    ) -> np.ndarray:

        state = self._validate_inputs(
            x,
            t,
            dt,
        )

        k1 = self._evaluate_derivative(
            derivative,
            state,
            t,
            state.size,
        )

        k2 = self._evaluate_derivative(
            derivative,
            state + 0.5 * dt * k1,
            t + 0.5 * dt,
            state.size,
        )

        k3 = self._evaluate_derivative(
            derivative,
            state + 0.5 * dt * k2,
            t + 0.5 * dt,
            state.size,
        )

        k4 = self._evaluate_derivative(
            derivative,
            state + dt * k3,
            t + dt,
            state.size,
        )

        result = (
            state
            + (
                dt / 6.0
            )
            * (
                k1
                + 2.0 * k2
                + 2.0 * k3
                + k4
            )
        )

        if not np.all(
            np.isfinite(result)
        ):
            raise IntegrationError(
                "RK4 produced a "
                "non-finite state."
            )

        return result


# ======================================================================
# IMPLICIT TRAPEZOIDAL
# ======================================================================


class TrapezoidalIntegrator(
    BaseIntegrator
):
    """
    Implicit trapezoidal integrator.

    The nonlinear equation is:

        x_(n+1)
        =
        x_n
        +
        dt/2 *
        (
            f(x_n, t_n)
            +
            f(x_(n+1), t_(n+1))
        )

    This implementation uses fixed-point iteration.

    It is therefore an implicit ODE integrator, not a full Newton-based
    DAE solver.

    A future GridForge DAE Newton solver may use this integrator
    contract while solving the complete residual/Jacobian system.
    """

    def __init__(
        self,
        tolerance: float = 1e-8,
        max_iterations: int = 20,
    ) -> None:

        if tolerance <= 0.0:
            raise ValueError(
                "tolerance must be "
                "greater than zero."
            )

        if max_iterations < 1:
            raise ValueError(
                "max_iterations must be "
                "at least one."
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

        state = self._validate_inputs(
            x,
            t,
            dt,
        )

        f_old = (
            self._evaluate_derivative(
                derivative,
                state,
                t,
                state.size,
            )
        )

        t_new = (
            t + dt
        )

        # Explicit-Euler prediction.
        x_new = (
            state
            + dt * f_old
        )

        converged = False

        for _ in range(
            self.max_iterations
        ):

            f_new = (
                self._evaluate_derivative(
                    derivative,
                    x_new,
                    t_new,
                    state.size,
                )
            )

            predicted = (
                state
                + (
                    dt / 2.0
                )
                * (
                    f_old
                    + f_new
                )
            )

            correction = (
                predicted
                - x_new
            )

            x_new = predicted

            if np.linalg.norm(
                correction,
                ord=np.inf,
            ) < self.tolerance:

                converged = True
                break

        if not converged:
            raise IntegrationError(
                "Implicit trapezoidal "
                "iteration did not converge "
                f"within "
                f"{self.max_iterations} "
                "iterations."
            )

        if not np.all(
            np.isfinite(x_new)
        ):
            raise IntegrationError(
                "Trapezoidal integration "
                "produced a non-finite "
                "state."
            )

        return x_new


# ======================================================================
# FACADE
# ======================================================================


class Integrator:
    """
    Public integrator facade.

    Parameters
    ----------
    method:
        Integration method.

        Supported values:

            "RK4"
            "TRAPEZOIDAL"

    tolerance:
        Convergence tolerance used by the trapezoidal method.

    max_iterations:
        Maximum nonlinear fixed-point iterations used by the
        trapezoidal method.
    """

    RK4 = "RK4"
    TRAPEZOIDAL = "TRAPEZOIDAL"

    def __init__(
        self,
        method: str = RK4,
        tolerance: float = 1e-8,
        max_iterations: int = 20,
    ) -> None:

        normalized = (
            str(method)
            .strip()
            .upper()
        )

        if normalized == self.RK4:

            self.solver: BaseIntegrator = (
                RK4Integrator()
            )

        elif normalized == self.TRAPEZOIDAL:

            self.solver = (
                TrapezoidalIntegrator(
                    tolerance=tolerance,
                    max_iterations=max_iterations,
                )
            )

        else:

            raise ValueError(
                "Unknown integration method "
                f"'{method}'. Supported methods "
                "are 'RK4' and 'TRAPEZOIDAL'."
            )

        self.method = normalized

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


__all__ = [
    "DerivativeFunction",
    "IntegrationError",
    "BaseIntegrator",
    "RK4Integrator",
    "TrapezoidalIntegrator",
    "Integrator",
]
```
