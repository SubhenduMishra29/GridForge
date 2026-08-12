"""
GridForge Power Flow Solver Options
===================================

File:
    core/solver/power_flow/solver_options.py

GridForge Power Flow Solver Options v1.0
----------------------------------------

Industrial configuration and validation for the GridForge
AC Newton-Raphson Power Flow Engine.

Responsibilities
----------------
- Store Newton-Raphson solver configuration.
- Validate numerical parameters.
- Provide deterministic solver defaults.
- Prevent invalid numerical configurations.
- Provide serializable configuration diagnostics.

This module contains configuration only.

It does NOT:
- Perform power-flow calculations.
- Modify the Network.
- Build Ybus.
- Assemble Jacobians.
- Solve linear systems.
- Handle reactive-power limits.
- Select numerical backends.
- Implement advanced convergence algorithms.

Current Numerical Scope
-----------------------
The reference GridForge power-flow solver supports:

- Classical Newton-Raphson iteration.
- Explicit Newton damping.
- Explicit linear-system regularization.
- PV/PQ reactive-power limit enforcement.
- Deterministic convergence criteria.

Advanced numerical strategies are intentionally NOT part of
this configuration baseline.

Deferred capabilities include:

- Line search.
- Trust-region methods.
- Levenberg-Marquardt methods.
- Adaptive damping.
- Automatic flat-start initialization.
- Voltage-limit optimization/control.
- Angle-limit control.
- GPU backend selection.
- Sparse backend selection.

These capabilities may be introduced later only when a
fundamental numerical requirement justifies them.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from dataclasses import dataclass

import math


@dataclass
class SolverOptions:
    """
    Configuration for the GridForge Newton-Raphson
    Power Flow Engine.

    Parameters
    ----------
    tolerance:
        Maximum acceptable infinity-norm mismatch.

        Must be finite and strictly greater than zero.

    max_iterations:
        Maximum number of Newton-Raphson iterations.

        Must be an integer greater than or equal to one.

    damping:
        Newton correction multiplier.

        1.0:
            Full Newton step.

        Values below 1.0:
            Damped Newton step.

        Required range:

            0.0 < damping <= 1.0

    regularization:
        Non-negative diagonal regularization parameter supplied
        to the linear solver.

        Zero disables explicit regularization.

    verbose:
        Enable iteration diagnostics.

    enforce_q_limits:
        Enable PV-bus reactive-power limit enforcement.

    q_limit_tolerance:
        Numerical tolerance used when evaluating generator
        reactive-power limits.

    Notes
    -----
    This class contains configuration only.

    It deliberately does not contain algorithm-selection
    controls for advanced numerical methods.
    """

    # =========================================================
    # CONVERGENCE
    # =========================================================

    tolerance: float = 1.0e-8

    max_iterations: int = 20

    # =========================================================
    # NEWTON STEP
    # =========================================================

    damping: float = 1.0

    # =========================================================
    # LINEAR SOLVER
    # =========================================================

    regularization: float = 0.0

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    verbose: bool = False

    # =========================================================
    # REACTIVE POWER LIMITS
    # =========================================================

    enforce_q_limits: bool = True

    q_limit_tolerance: float = 1.0e-8

    # =========================================================
    # VALIDATION HELPERS
    # =========================================================

    @staticmethod
    def _validate_real(
        value,
        name: str,
    ) -> float:
        """
        Validate and normalize a real-valued numerical option.

        Parameters
        ----------
        value:
            Value to validate.

        name:
            Configuration field name used in diagnostics.

        Returns
        -------
        float
            Finite floating-point representation.

        Raises
        ------
        TypeError
            If the value is not a real numerical value or is bool.

        ValueError
            If the value is NaN or infinite.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                f"{name} must be a real number."
            )

        value = float(
            value
        )

        if not math.isfinite(
            value
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self) -> None:
        """
        Validate the complete solver configuration.

        Raises
        ------
        ValueError
            If a numerical option is outside its permitted
            range or is non-finite.

        TypeError
            If an option has an invalid basic type.

        Notes
        -----
        Validation is intentionally explicit so invalid
        numerical configuration cannot silently enter the
        Newton-Raphson solver.
        """

        # -----------------------------------------------------
        # Tolerance
        # -----------------------------------------------------

        tolerance = self._validate_real(
            self.tolerance,
            "tolerance",
        )

        if tolerance <= 0.0:
            raise ValueError(
                "tolerance must be greater than zero."
            )

        # -----------------------------------------------------
        # Maximum iterations
        # -----------------------------------------------------

        if isinstance(
            self.max_iterations,
            bool,
        ) or not isinstance(
            self.max_iterations,
            int,
        ):
            raise TypeError(
                "max_iterations must be an integer."
            )

        if self.max_iterations < 1:
            raise ValueError(
                "max_iterations must be at least 1."
            )

        # -----------------------------------------------------
        # Damping
        # -----------------------------------------------------

        damping = self._validate_real(
            self.damping,
            "damping",
        )

        if not (
            0.0 < damping <= 1.0
        ):
            raise ValueError(
                "damping must satisfy "
                "0.0 < damping <= 1.0."
            )

        # -----------------------------------------------------
        # Regularization
        # -----------------------------------------------------

        regularization = self._validate_real(
            self.regularization,
            "regularization",
        )

        if regularization < 0.0:
            raise ValueError(
                "regularization cannot be negative."
            )

        # -----------------------------------------------------
        # Boolean options
        # -----------------------------------------------------

        if not isinstance(
            self.verbose,
            bool,
        ):
            raise TypeError(
                "verbose must be a boolean."
            )

        if not isinstance(
            self.enforce_q_limits,
            bool,
        ):
            raise TypeError(
                "enforce_q_limits must be a boolean."
            )

        # -----------------------------------------------------
        # Q-limit tolerance
        # -----------------------------------------------------

        q_limit_tolerance = self._validate_real(
            self.q_limit_tolerance,
            "q_limit_tolerance",
        )

        if q_limit_tolerance < 0.0:
            raise ValueError(
                "q_limit_tolerance cannot be negative."
            )

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self) -> dict:
        """
        Return the complete solver configuration.

        Returns
        -------
        dict
            Serializable solver configuration.

        Notes
        -----
        The returned dictionary contains only configuration
        state and does not expose any runtime solver state.
        """

        return {
            "tolerance": float(
                self.tolerance
            ),

            "max_iterations": int(
                self.max_iterations
            ),

            "damping": float(
                self.damping
            ),

            "regularization": float(
                self.regularization
            ),

            "verbose": bool(
                self.verbose
            ),

            "enforce_q_limits": bool(
                self.enforce_q_limits
            ),

            "q_limit_tolerance": float(
                self.q_limit_tolerance
            ),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            "SolverOptions("
            f"tolerance={self.tolerance}, "
            f"max_iterations={self.max_iterations}, "
            f"damping={self.damping}, "
            f"regularization={self.regularization}, "
            f"verbose={self.verbose}, "
            f"enforce_q_limits="
            f"{self.enforce_q_limits}, "
            f"q_limit_tolerance="
            f"{self.q_limit_tolerance}"
            ")"
        )


__all__ = [
    "SolverOptions",
]
