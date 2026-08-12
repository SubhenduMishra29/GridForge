"""
GridForge Dynamic Integrators
=============================

Numerical integration methods for GridForge dynamic simulation.

Supported methods
-----------------
RK4
    Classical explicit fourth-order Runge-Kutta integration.

TRAPEZOIDAL
    Implicit trapezoidal integration solved using Newton iteration.

Architecture
------------
The integrator is deliberately independent of:

- generators;
- machine models;
- AVR/governor/PSS models;
- network topology;
- Y-bus construction;
- algebraic network solving.

It receives a generic differential-equation callback:

    derivative(x, t) -> dx/dt

and advances the dynamic state:

    x(t + dt)

The DAE solver is responsible for constructing the complete derivative
function, including the required algebraic-network solution.

Numerical contract
------------------
All integrators implement:

    step(
        x,
        derivative,
        t,
        dt,
        jacobian=None,
    )

where:

    x
        Current dynamic state vector.

    derivative
        Callable returning dx/dt.

    t
        Current simulation time.

    dt
        Positive integration interval.

    jacobian
        Optional Jacobian of the derivative function:

            df/dx

        Used by the implicit trapezoidal solver.

Notes
-----
The RK4 implementation evaluates both state and time at all four
intermediate stages. This is important for time-dependent events,
inputs, controls, and dynamic models.

The trapezoidal solver solves:

    x_new =
        x_old
        + dt/2 * (
            f(x_old, t_old)
            + f(x_new, t_new)
        )

using Newton iteration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

import numpy as np


# ======================================================================
# TYPE ALIASES
# ======================================================================

State = np.ndarray

DerivativeFunction = Callable[
    [State, float],
    State,
]

JacobianFunction = Callable[
    [State, float],
    np.ndarray,
]


# ======================================================================
# ERRORS
# ======================================================================


class IntegrationError(
    RuntimeError
):
    """Base exception for integration failures."""


class IntegrationConvergenceError(
    IntegrationError
):
    """
    Raised when an implicit integration step fails to converge.
    """


# ======================================================================
# BASE INTEGRATOR
# ======================================================================


class BaseIntegrator(ABC):
    """
    Common interface for all GridForge dynamic integrators.
    """

    @abstractmethod
    def step(
        self,
        x: State,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
        jacobian: JacobianFunction | None = None,
    ) -> State:
        """
        Advance the state by one integration step.
        """
        ...


# ======================================================================
# RK4
# ======================================================================


class RK4Integrator(
    BaseIntegrator
):
    """
    Classical fourth-order Runge-Kutta integrator.

    The method is:

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

        x_(n+1) =
            x_n
            + dt/6 * (
                k1 + 2*k2 + 2*k3 + k4
            )

    This is the default explicit integrator for GridForge transient
    stability calculations where appropriate.
    """

    def step(
        self,
        x: State,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
        jacobian: JacobianFunction | None = None,
    ) -> State:
        """
        Advance the state by one RK4 step.

        Parameters
        ----------
        x:
            Current state vector.

        derivative:
            Callable:

                derivative(x, t) -> dx/dt

        t:
            Current simulation time.

        dt:
            Integration step.

        jacobian:
            Ignored by RK4. Accepted to maintain the common interface.
        """

        del jacobian

        x = _validate_state(
            x
        )

        t = _validate_time(
            t
        )

        dt = _validate_dt(
            dt
        )

        k1 = _evaluate_derivative(
            derivative,
            x,
            t,
        )

        k2 = _evaluate_derivative(
            derivative,
            x + 0.5 * dt * k1,
            t + 0.5 * dt,
        )

        k3 = _evaluate_derivative(
            derivative,
            x + 0.5 * dt * k2,
            t + 0.5 * dt,
        )

        k4 = _evaluate_derivative(
            derivative,
            x + dt * k3,
            t + dt,
        )

        x_new = (
            x
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

        return np.asarray(
            x_new,
            dtype=float,
        )


# ======================================================================
# IMPLICIT TRAPEZOIDAL
# ======================================================================


class TrapezoidalIntegrator(
    BaseIntegrator
):
    """
    Implicit trapezoidal integrator.

    The nonlinear equation solved at each step is:

        F(x_new) =
            x_new
            - x_old
            - dt/2 * (
                f_old
                + f(x_new, t_new)
            )

        F(x_new) = 0

    Newton iteration uses:

        J_F =
            I
            - dt/2 * df/dx

    If an analytical derivative Jacobian is not supplied, a numerical
    finite-difference Jacobian is constructed.

    Parameters
    ----------
    tolerance:
        Newton convergence tolerance.

    max_iterations:
        Maximum Newton iterations.

    finite_difference_step:
        Perturbation used for numerical Jacobian construction.

    Notes
    -----
    The numerical Jacobian fallback is intended as a correctness
    reference and general-purpose implementation. Detailed production
    models may provide analytical Jacobians for improved performance.
    """

    def __init__(
        self,
        tolerance: float = 1e-8,
        max_iterations: int = 20,
        finite_difference_step: float = 1e-7,
    ) -> None:

        if tolerance <= 0.0:
            raise ValueError(
                "tolerance must be "
                "greater than zero."
            )

        if max_iterations <= 0:
            raise ValueError(
                "max_iterations must be "
                "greater than zero."
            )

        if finite_difference_step <= 0.0:
            raise ValueError(
                "finite_difference_step "
                "must be greater than zero."
            )

        self.tolerance = float(
            tolerance
        )

        self.max_iterations = int(
            max_iterations
        )

        self.finite_difference_step = (
            float(
                finite_difference_step
            )
        )

    def step(
        self,
        x: State,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
        jacobian: JacobianFunction | None = None,
    ) -> State:
        """
        Advance the state using implicit trapezoidal integration.
        """

        x = _validate_state(
            x
        )

        t = _validate_time(
            t
        )

        dt = _validate_dt(
            dt
        )

        t_new = (
            t + dt
        )

        # --------------------------------------------------------------
        # Evaluate derivative at the beginning of the interval.
        # --------------------------------------------------------------

        f_old = _evaluate_derivative(
            derivative,
            x,
            t,
        )

        # --------------------------------------------------------------
        # Predictor.
        #
        # Explicit Euler is used only as the initial Newton guess.
        # --------------------------------------------------------------

        x_new = (
            x
            + dt * f_old
        )

        identity = np.eye(
            x.size,
            dtype=float,
        )

        # --------------------------------------------------------------
        # Newton iteration.
        # --------------------------------------------------------------

        for iteration in range(
            self.max_iterations
        ):

            f_new = _evaluate_derivative(
                derivative,
                x_new,
                t_new,
            )

            residual = (
                x_new
                - x
                - (
                    dt / 2.0
                )
                * (
                    f_old
                    + f_new
                )
            )

            residual_norm = (
                np.linalg.norm(
                    residual,
                    ord=np.inf,
                )
            )

            if residual_norm <= (
                self.tolerance
            ):

                return np.asarray(
                    x_new,
                    dtype=float,
                )

            # ----------------------------------------------------------
            # Evaluate df/dx.
            # ----------------------------------------------------------

            if jacobian is not None:

                df_dx = np.asarray(
                    jacobian(
                        x_new,
                        t_new,
                    ),
                    dtype=float,
                )

                _validate_jacobian(
                    df_dx,
                    x.size,
                )

            else:

                df_dx = (
                    self._numerical_jacobian(
                        derivative,
                        x_new,
                        t_new,
                        f_new,
                    )
                )

            # ----------------------------------------------------------
            # Newton system:
            #
            # [I - dt/2 * df/dx] Δx = -F
            # ----------------------------------------------------------

            jacobian_residual = (
                identity
                - (
                    dt / 2.0
                ) * df_dx
            )

            try:

                correction = np.linalg.solve(
                    jacobian_residual,
                    -residual,
                )

            except np.linalg.LinAlgError as exc:

                raise IntegrationError(
                    "Implicit trapezoidal "
                    "Newton system is "
                    "singular or ill-conditioned "
                    f"at t={t_new:.12g}."
                ) from exc

            x_new = (
                x_new
                + correction
            )

            correction_norm = (
                np.linalg.norm(
                    correction,
                    ord=np.inf,
                )
            )

            if correction_norm <= (
                self.tolerance
            ):

                # Re-evaluate the residual
                # after the correction so that
                # convergence is based on the
                # actual implicit equation.
                f_check = (
                    _evaluate_derivative(
                        derivative,
                        x_new,
                        t_new,
                    )
                )

                residual_check = (
                    x_new
                    - x
                    - (
                        dt / 2.0
                    )
                    * (
                        f_old
                        + f_check
                    )
                )

                if (
                    np.linalg.norm(
                        residual_check,
                        ord=np.inf,
                    )
                    <= self.tolerance
                ):

                    return np.asarray(
                        x_new,
                        dtype=float,
                    )

        raise IntegrationConvergenceError(
            "Implicit trapezoidal integration "
            "failed to converge after "
            f"{self.max_iterations} Newton "
            f"iterations at t={t_new:.12g}."
        )

    # ==================================================================
    # NUMERICAL JACOBIAN
    # ==================================================================

    def _numerical_jacobian(
        self,
        derivative: DerivativeFunction,
        x: State,
        t: float,
        f_x: State,
    ) -> np.ndarray:
        """
        Construct df/dx using forward finite differences.
        """

        n = x.size

        jacobian = np.empty(
            (n, n),
            dtype=float,
        )

        h_base = (
            self.finite_difference_step
        )

        for column in range(n):

            h = h_base * max(
                1.0,
                abs(
                    x[column]
                ),
            )

            x_perturbed = (
                x.copy()
            )

            x_perturbed[column] += h

            f_perturbed = (
                _evaluate_derivative(
                    derivative,
                    x_perturbed,
                    t,
                )
            )

            jacobian[:, column] = (
                f_perturbed
                - f_x
            ) / h

        return jacobian


# ======================================================================
# PUBLIC INTEGRATOR FACADE
# ======================================================================


class Integrator:
    """
    Common GridForge integration facade.

    Parameters
    ----------
    method:
        Integration method.

        Supported values:

        - ``"RK4"``
        - ``"TRAPEZOIDAL"``

    tolerance:
        Convergence tolerance for implicit trapezoidal integration.

    max_iterations:
        Maximum Newton iterations for implicit trapezoidal integration.

    finite_difference_step:
        Numerical Jacobian perturbation.
    """

    SUPPORTED_METHODS = (
        "RK4",
        "TRAPEZOIDAL",
    )

    def __init__(
        self,
        method: str = "RK4",
        *,
        tolerance: float = 1e-8,
        max_iterations: int = 20,
        finite_difference_step: float = 1e-7,
    ) -> None:

        if not isinstance(
            method,
            str,
        ):

            raise TypeError(
                "method must be a string."
            )

        normalized_method = (
            method.strip().upper()
        )

        if normalized_method == (
            "TRAPEZOID"
        ):

            normalized_method = (
                "TRAPEZOIDAL"
            )

        if normalized_method not in (
            self.SUPPORTED_METHODS
        ):

            raise ValueError(
                "Unknown integration method "
                f"'{method}'. Supported "
                f"methods: "
                f"{', '.join(self.SUPPORTED_METHODS)}."
            )

        self.method = (
            normalized_method
        )

        if normalized_method == "RK4":

            self.solver = (
                RK4Integrator()
            )

        else:

            self.solver = (
                TrapezoidalIntegrator(
                    tolerance=tolerance,
                    max_iterations=max_iterations,
                    finite_difference_step=(
                        finite_difference_step
                    ),
                )
            )

    def step(
        self,
        x: State,
        derivative: DerivativeFunction,
        t: float,
        dt: float,
        jacobian: JacobianFunction | None = None,
    ) -> State:
        """
        Advance the dynamic state by one step.

        Parameters
        ----------
        x:
            Current dynamic state.

        derivative:
            Differential-equation callback:

                derivative(x, t) -> dx/dt

        t:
            Current simulation time.

        dt:
            Positive integration interval.

        jacobian:
            Optional analytical Jacobian:

                jacobian(x, t) -> df/dx

            Used by the implicit trapezoidal solver.
        """

        return self.solver.step(
            x=x,
            derivative=derivative,
            t=t,
            dt=dt,
            jacobian=jacobian,
        )


# ======================================================================
# VALIDATION HELPERS
# ======================================================================


def _validate_state(
    x: State,
) -> np.ndarray:
    """
    Validate and normalize the dynamic state vector.
    """

    state = np.asarray(
        x,
        dtype=float,
    )

    if state.ndim != 1:

        raise ValueError(
            "Dynamic state must be "
            "a one-dimensional vector."
        )

    if state.size == 0:

        raise ValueError(
            "Dynamic state cannot be empty."
        )

    if not np.all(
        np.isfinite(state)
    ):

        raise ValueError(
            "Dynamic state contains "
            "non-finite values."
        )

    return state.copy()


def _validate_time(
    t: float,
) -> float:
    """
    Validate simulation time.
    """

    value = float(t)

    if not np.isfinite(
        value
    ):

        raise ValueError(
            "Simulation time must "
            "be finite."
        )

    return value


def _validate_dt(
    dt: float,
) -> float:
    """
    Validate integration step.
    """

    value = float(dt)

    if not np.isfinite(
        value
    ) or value <= 0.0:

        raise ValueError(
            "Integration dt must be "
            "finite and greater "
            "than zero."
        )

    return value


def _evaluate_derivative(
    derivative: DerivativeFunction,
    x: State,
    t: float,
) -> np.ndarray:
    """
    Evaluate and validate a derivative callback.
    """

    result = np.asarray(
        derivative(
            x,
            t,
        ),
        dtype=float,
    )

    if result.shape != x.shape:

        raise ValueError(
            "Derivative shape "
            f"{result.shape} does not "
            "match state shape "
            f"{x.shape}."
        )

    if not np.all(
        np.isfinite(result)
    ):

        raise IntegrationError(
            "Derivative returned "
            "non-finite values."
        )

    return result


def _validate_jacobian(
    jacobian: np.ndarray,
    state_size: int,
) -> None:
    """
    Validate an analytical derivative Jacobian.
    """

    expected_shape = (
        state_size,
        state_size,
    )

    if jacobian.shape != (
        expected_shape
    ):

        raise ValueError(
            "Derivative Jacobian shape "
            f"{jacobian.shape} does not "
            f"match expected shape "
            f"{expected_shape}."
        )

    if not np.all(
        np.isfinite(jacobian)
    ):

        raise IntegrationError(
            "Derivative Jacobian "
            "contains non-finite values."
        )


# ======================================================================
# PUBLIC API
# ======================================================================


__all__ = [
    "State",
    "DerivativeFunction",
    "JacobianFunction",
    "IntegrationError",
    "IntegrationConvergenceError",
    "BaseIntegrator",
    "RK4Integrator",
    "TrapezoidalIntegrator",
    "Integrator",
]
```
