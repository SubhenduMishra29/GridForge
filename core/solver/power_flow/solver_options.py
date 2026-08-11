```python
"""
GridForge Power Flow Solver Options
===================================

File:
    core/solver/power_flow/solver_options.py

Industrial configuration and validation for the GridForge
AC Power Flow Engine.

Responsibilities
----------------
- Store Newton-Raphson solver configuration.
- Validate numerical parameters.
- Provide deterministic solver defaults.
- Prevent invalid numerical configurations.

This module contains configuration only.

It does NOT:
- Perform power-flow calculations.
- Modify the Network.
- Build Ybus.
- Assemble Jacobians.
- Solve linear systems.
- Handle reactive-power limits.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SolverOptions:
    """
    Configuration for the GridForge Newton-Raphson
    Power Flow Engine.

    Parameters
    ----------
    tolerance:
        Maximum acceptable infinity-norm mismatch.

    max_iterations:
        Maximum Newton-Raphson iterations.

    damping:
        Newton correction multiplier.

        1.0:
            Full Newton step.

        Values below 1.0:
            Damped Newton step.

    regularization:
        Non-negative regularization parameter supplied
        to the linear solver.

        Zero disables explicit regularization.

    verbose:
        Enable iteration diagnostics.

    enforce_q_limits:
        Enable PV-bus reactive-power limit enforcement.

    q_limit_tolerance:
        Numerical tolerance used when evaluating
        generator reactive-power limits.
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
    # VALIDATION
    # =========================================================

    def validate(self) -> None:
        """
        Validate solver configuration.

        Raises
        ------
        ValueError
            If any numerical option is invalid.

        TypeError
            If an option has an invalid basic type.
        """

        # -----------------------------------------------------
        # Tolerance
        # -----------------------------------------------------

        if not isinstance(
            self.tolerance,
            (int, float)
        ):
            raise TypeError(
                "tolerance must be a real number."
            )

        if self.tolerance <= 0.0:
            raise ValueError(
                "tolerance must be greater than zero."
            )

        # -----------------------------------------------------
        # Maximum iterations
        # -----------------------------------------------------

        if isinstance(
            self.max_iterations,
            bool
        ) or not isinstance(
            self.max_iterations,
            int
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

        if not isinstance(
            self.damping,
            (int, float)
        ):
            raise TypeError(
                "damping must be a real number."
            )

        if not (
            0.0 < self.damping <= 1.0
        ):
            raise ValueError(
                "damping must satisfy "
                "0.0 < damping <= 1.0."
            )

        # -----------------------------------------------------
        # Regularization
        # -----------------------------------------------------

        if not isinstance(
            self.regularization,
            (int, float)
        ):
            raise TypeError(
                "regularization must be a real number."
            )

        if self.regularization < 0.0:
            raise ValueError(
                "regularization cannot be negative."
            )

        # -----------------------------------------------------
        # Boolean options
        # -----------------------------------------------------

        if not isinstance(
            self.verbose,
            bool
        ):
            raise TypeError(
                "verbose must be a boolean."
            )

        if not isinstance(
            self.enforce_q_limits,
            bool
        ):
            raise TypeError(
                "enforce_q_limits must be a boolean."
            )

        # -----------------------------------------------------
        # Q-limit tolerance
        # -----------------------------------------------------

        if not isinstance(
            self.q_limit_tolerance,
            (int, float)
        ):
            raise TypeError(
                "q_limit_tolerance must be a real number."
            )

        if self.q_limit_tolerance < 0.0:
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
```
