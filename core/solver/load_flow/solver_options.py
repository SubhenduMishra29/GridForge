"""
GridForge Load Flow Solver Options

Defines numerical parameters for
Newton-Raphson power flow.

No solver logic here.

"""


class SolverOptions:


    def __init__(

        self,

        tolerance=1e-8,

        max_iterations=50,

        damping=1.0,

        verbose=False,

        enforce_q_limits=True

    ):


        # ---------------------------------
        # Convergence
        # ---------------------------------

        self.tolerance = tolerance

        self.max_iterations = max_iterations



        # ---------------------------------
        # Numerical stability
        # ---------------------------------

        self.damping = damping



        # ---------------------------------
        # Output
        # ---------------------------------

        self.verbose = verbose



        # ---------------------------------
        # Generator limits
        # ---------------------------------

        self.enforce_q_limits = enforce_q_limits



    # =================================================
    # Validation
    # =================================================

    def validate(self):


        if self.tolerance <= 0:

            raise ValueError(
                "Tolerance must be positive"
            )


        if self.max_iterations <= 0:

            raise ValueError(
                "Maximum iterations must be positive"
            )


        if not (0 < self.damping <= 1):

            raise ValueError(
                "Damping must be between 0 and 1"
            )


        return True



    # =================================================
    # Debug
    # =================================================

    def summary(self):


        return {

            "tolerance":
                self.tolerance,

            "max_iterations":
                self.max_iterations,

            "damping":
                self.damping,

            "verbose":
                self.verbose,

            "q_limits":
                self.enforce_q_limits

        }
