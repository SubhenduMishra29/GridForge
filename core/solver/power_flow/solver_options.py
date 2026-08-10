# GridForge

# Copyright © 2026 Subhendu Mishra

# All Rights Reserved.

# Proprietary and confidential.

"""
GridForge Power Flow Solver Options
===================================

File:
core/solver/power_flow/solver_options.py

## Purpose

Defines numerical and operational parameters used by the
Newton-Raphson AC power-flow solver.

## Responsibilities

* Store convergence parameters.
* Store numerical-stability parameters.
* Store reactive-power-limit controls.
* Store diagnostic controls.
* Validate solver configuration.
* Provide configuration introspection.

## Does NOT

* Perform power-flow calculations.
* Build Ybus.
* Assemble the Jacobian.
* Solve linear equations.
* Modify network state.

All numerical execution belongs to the solver modules.
"""

class SolverOptions:
"""
Configuration container for the GridForge AC power-flow
solver.

```
The object is intentionally free of solver logic. It can
therefore be created, inspected, validated, and passed to
different solver components without coupling those
components together.
"""

def __init__(
    self,

    # -----------------------------------------------------
    # CONVERGENCE
    # -----------------------------------------------------

    tolerance: float = 1e-8,
    max_iterations: int = 50,

    # -----------------------------------------------------
    # NUMERICAL STABILITY
    # -----------------------------------------------------

    damping: float = 1.0,
    regularization: float = 0.0,

    # -----------------------------------------------------
    # REACTIVE POWER LIMIT CONTROL
    # -----------------------------------------------------

    enforce_q_limits: bool = True,
    q_limit_tolerance: float = 1e-6,

    # -----------------------------------------------------
    # DIAGNOSTICS
    # -----------------------------------------------------

    verbose: bool = False,
    track_history: bool = True,
):
    """
    Create solver configuration.

    Parameters
    ----------
    tolerance:
        Maximum acceptable absolute power mismatch for
        convergence.

    max_iterations:
        Maximum Newton-Raphson iterations.

    damping:
        State-update damping factor.

        Valid range:

            0 < damping <= 1

        A value of 1.0 means a full Newton step.

    regularization:
        Optional diagonal regularization supplied to the
        linear-system solver.

        Zero means no regularization.

    enforce_q_limits:
        Enable generator reactive-power limit enforcement.

    q_limit_tolerance:
        Numerical tolerance used when checking generator
        reactive-power limits.

    verbose:
        Enable iteration diagnostics.

    track_history:
        Store convergence history.
    """

    # -----------------------------------------------------
    # CONVERGENCE
    # -----------------------------------------------------

    self.tolerance = tolerance
    self.max_iterations = max_iterations

    # -----------------------------------------------------
    # NUMERICAL STABILITY
    # -----------------------------------------------------

    self.damping = damping
    self.regularization = regularization

    # -----------------------------------------------------
    # REACTIVE POWER LIMITS
    # -----------------------------------------------------

    self.enforce_q_limits = enforce_q_limits
    self.q_limit_tolerance = q_limit_tolerance

    # -----------------------------------------------------
    # DIAGNOSTICS
    # -----------------------------------------------------

    self.verbose = verbose
    self.track_history = track_history

    # -----------------------------------------------------
    # Validate immediately.
    #
    # Invalid numerical configuration should fail when the
    # options object is created rather than much later
    # during a solver iteration.
    # -----------------------------------------------------

    self.validate()

# =========================================================
# VALIDATION
# =========================================================

def validate(self) -> bool:
    """
    Validate all solver configuration parameters.

    Returns
    -------
    bool
        True when the configuration is valid.

    Raises
    ------
    TypeError
        If a parameter has an invalid type.

    ValueError
        If a parameter is outside its valid range.
    """

    # -----------------------------------------------------
    # TOLERANCE
    # -----------------------------------------------------

    if not isinstance(
        self.tolerance,
        (int, float)
    ):
        raise TypeError(
            "Tolerance must be numeric."
        )

    if self.tolerance <= 0:
        raise ValueError(
            "Tolerance must be positive."
        )

    # -----------------------------------------------------
    # MAXIMUM ITERATIONS
    # -----------------------------------------------------

    if not isinstance(
        self.max_iterations,
        int
    ):
        raise TypeError(
            "Maximum iterations must be an integer."
        )

    if self.max_iterations <= 0:
        raise ValueError(
            "Maximum iterations must be positive."
        )

    # -----------------------------------------------------
    # DAMPING
    # -----------------------------------------------------

    if not isinstance(
        self.damping,
        (int, float)
    ):
        raise TypeError(
            "Damping must be numeric."
        )

    if not (
        0.0 < self.damping <= 1.0
    ):
        raise ValueError(
            "Damping must satisfy 0 < damping <= 1."
        )

    # -----------------------------------------------------
    # REGULARIZATION
    # -----------------------------------------------------

    if not isinstance(
        self.regularization,
        (int, float)
    ):
        raise TypeError(
            "Regularization must be numeric."
        )

    if self.regularization < 0:
        raise ValueError(
            "Regularization must be >= 0."
        )

    # -----------------------------------------------------
    # Q-LIMIT TOLERANCE
    # -----------------------------------------------------

    if not isinstance(
        self.q_limit_tolerance,
        (int, float)
    ):
        raise TypeError(
            "Q limit tolerance must be numeric."
        )

    if self.q_limit_tolerance < 0:
        raise ValueError(
            "Q limit tolerance must be >= 0."
        )

    # -----------------------------------------------------
    # BOOLEAN CONTROLS
    # -----------------------------------------------------

    if not isinstance(
        self.enforce_q_limits,
        bool
    ):
        raise TypeError(
            "enforce_q_limits must be boolean."
        )

    if not isinstance(
        self.verbose,
        bool
    ):
        raise TypeError(
            "verbose must be boolean."
        )

    if not isinstance(
        self.track_history,
        bool
    ):
        raise TypeError(
            "track_history must be boolean."
        )

    return True

# =========================================================
# DEBUG / INTROSPECTION
# =========================================================

def summary(self) -> dict:
    """
    Return the complete solver configuration as a dictionary.

    This is intended for diagnostics, logging, result
    metadata, and UI inspection.
    """

    return {
        "tolerance": self.tolerance,
        "max_iterations": self.max_iterations,
        "damping": self.damping,
        "regularization": self.regularization,
        "enforce_q_limits": self.enforce_q_limits,
        "q_limit_tolerance": self.q_limit_tolerance,
        "verbose": self.verbose,
        "track_history": self.track_history,
    }

# =========================================================
# REPRESENTATION
# =========================================================

def __repr__(self) -> str:
    """
    Developer-friendly representation of the solver
    configuration.
    """

    return (
        "SolverOptions("
        f"tolerance={self.tolerance!r}, "
        f"max_iterations={self.max_iterations!r}, "
        f"damping={self.damping!r}, "
        f"regularization={self.regularization!r}, "
        f"enforce_q_limits={self.enforce_q_limits!r}, "
        f"q_limit_tolerance={self.q_limit_tolerance!r}, "
        f"verbose={self.verbose!r}, "
        f"track_history={self.track_history!r}"
        ")"
    )
```

**all** = [
"SolverOptions",
]
