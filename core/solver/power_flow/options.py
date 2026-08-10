"""
GridForge Power Flow Solver Options

Defines numerical and operational parameters for
Newton-Raphson power flow.

No solver logic here.
"""

class SolverOptions:

    def __init__(

        self,

        # ---------------------------------
        # Convergence
        # ---------------------------------
        tolerance=1e-8,
        max_iterations=50,

        # ---------------------------------
        # Numerical stability
        # ---------------------------------
        damping=1.0,
        regularization=0.0,   # for linear solver

        # ---------------------------------
        # Control behavior
        # ---------------------------------
        enforce_q_limits=True,
        q_limit_tolerance=1e-6,

        # ---------------------------------
        # Diagnostics
        # ---------------------------------
        verbose=False,
        track_history=True

    ):

        self.tolerance = tolerance
        self.max_iterations = max_iterations

        self.damping = damping
        self.regularization = regularization

        self.enforce_q_limits = enforce_q_limits
        self.q_limit_tolerance = q_limit_tolerance

        self.verbose = verbose
        self.track_history = track_history

    # =================================================
    # Validation
    # =================================================

    def validate(self):

        if self.tolerance <= 0:
            raise ValueError("Tolerance must be positive")

        if self.max_iterations <= 0:
            raise ValueError("Maximum iterations must be positive")

        if not (0 < self.damping <= 1):
            raise ValueError("Damping must be between 0 and 1")

        if self.regularization < 0:
            raise ValueError("Regularization must be >= 0")

        if self.q_limit_tolerance < 0:
            raise ValueError("Q limit tolerance must be >= 0")

        return True

    # =================================================
    # Debug / Introspection
    # =================================================

    def summary(self):

        return {

            "tolerance": self.tolerance,
            "max_iterations": self.max_iterations,

            "damping": self.damping,
            "regularization": self.regularization,

            "verbose": self.verbose,
            "track_history": self.track_history,

            "enforce_q_limits": self.enforce_q_limits,
            "q_limit_tolerance": self.q_limit_tolerance
        }
