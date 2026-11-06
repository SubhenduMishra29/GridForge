"""
GridForge Power Flow Solver Options
===================================

File:
    core/solver/power_flow/solver_options.py

GridForge Power Flow Engine v1.0
--------------------------------

Configuration and validation for the GridForge AC
Newton-Raphson power-flow solver.

Responsibilities
----------------
- Store Newton-Raphson solver configuration.
- Validate numerical parameters.
- Provide deterministic solver defaults.
- Prevent invalid numerical configurations.
- Provide serializable diagnostics.

This module contains configuration only.

It does NOT:
- Perform power-flow calculations.
- Modify the Network.
- Build Ybus.
- Assemble Jacobians.
- Solve linear systems.
- Handle reactive-power limits directly.
- Perform line-search or trust-region algorithms.
- Perform GPU computation.
- Select sparse numerical backends.

Advanced numerical strategies are intentionally excluded from
this baseline and may be introduced later only when supported by
a fundamental solver requirement.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real

import numpy as np


@dataclass
class SolverOptions:
    """
    Configuration for the GridForge Newton-Raphson
    AC Power Flow Engine.

    Parameters
    ----------
    tolerance:
        Maximum acceptable infinity-norm power mismatch.

    max_iterations:
        Maximum number of Newton-Raphson iterations.

    damping:
        Newton correction multiplier.

        1.0:
            Full Newton step.

        Values between 0 and 1:
            Damped Newton step.

    regularization:
        Explicit non-negative diagonal regularization parameter
        passed to the linear-system solver.

        0.0:
            No regularization.

    verbose:
        Enable iteration-level diagnostic output.

    enforce_q_limits:
        Enable PV-bus reactive-power limit handling.

    q_limit_tolerance:
        Numerical tolerance used when comparing calculated
        reactive power against Qmin/Qmax.

    Notes
    -----
    The options object is intentionally limited to the stable
    GridForge Power Flow Engine V1.0 numerical contract.

    The following are deliberately NOT included:

        line_search
        trust_region
        Levenberg-Marquardt
        flat_start
        voltage_limits
        angle_limits
        adaptive_damping
        GPU
        sparse_backend

    These are separate numerical or engineering features and
    must not be introduced into the baseline configuration
    without a demonstrated architectural requirement.
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
        Validate a finite real-valued numerical parameter.

        Booleans are deliberately rejected because bool is a
        subclass of int in Python.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            Real,
        ):
            raise TypeError(
                f"{name} must be a real number."
            )

        value = float(
            value
        )

        if not np.isfinite(
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
        TypeError
            If an option has an invalid type.

        ValueError
            If an option contains an invalid numerical value.
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
        # Newton damping
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
        # Linear-system regularization
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
        Return the complete validated solver configuration.

        Returns
        -------
        dict
            Serializable configuration dictionary.
        """

        self.validate()

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

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise developer-facing representation.
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
