```python
"""
GridForge Newton-Raphson Power Flow Engine
==========================================

File:
    core/solver/power_flow/nr_solver.py

Industrial AC Power Flow Solver

Responsibilities
----------------
- Newton-Raphson iteration
- Jacobian construction
- Linear-system solution
- Voltage state update
- Convergence monitoring
- PV/PQ reactive-limit handling

This module is the orchestration layer of the numerical
power-flow solver.

It does NOT:
- Build Ybus
- Calculate power injections directly
- Assemble the Jacobian directly
- Perform linear algebra directly
- Modify network topology
- Perform contingency analysis
- Perform short-circuit analysis
- Perform protection decisions

Numerical responsibilities are delegated to:

    core.solver.common.mismatch
    core.solver.common.jacobian
    core.solver.power_flow.sparse_solver
    core.solver.power_flow.q_limit_handler

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import numpy as np

from core.solver.common.mismatch import PowerMismatch
from core.solver.common.jacobian import JacobianBuilder

from core.solver.power_flow.sparse_solver import (
    SparseLinearSolver
)

from core.solver.power_flow.q_limit_handler import (
    QLimitHandler
)


class NewtonRaphsonSolver:
    """
    Newton-Raphson AC power-flow solver.

    Parameters
    ----------
    network:
        GridForge Network object.

    options:
        SolverOptions instance.

    Notes
    -----
    The Network must already contain a valid Ybus before
    ``solve()`` is called.

    The solver updates the voltage state stored in the Bus
    objects. This is intentional because the rest of the
    GridForge numerical infrastructure operates on the
    unified electrical model.
    """

    def __init__(self, network, options):

        if network is None:
            raise ValueError(
                "Network cannot be None"
            )

        if options is None:
            raise ValueError(
                "Solver options cannot be None"
            )

        self.network = network
        self.options = options

        # -----------------------------------------------------
        # Linear algebra layer
        #
        # Regularization belongs to the numerical options and
        # must therefore be passed explicitly to the linear
        # solver.
        # -----------------------------------------------------

        self.linear_solver = SparseLinearSolver(
            regularization=options.regularization
        )

        # -----------------------------------------------------
        # Reactive power limit handler
        # -----------------------------------------------------

        self.q_handler = QLimitHandler(
            network,
            tolerance=options.q_limit_tolerance
        )

        # -----------------------------------------------------
        # Iteration diagnostics
        # -----------------------------------------------------

        self.history = []

    # =========================================================
    # MAIN SOLVER
    # =========================================================

    def solve(self):
        """
        Execute the Newton-Raphson power-flow solution.

        Returns
        -------
        dict
            Solver result containing:

                success
                iterations
                error
                pv_to_pq
                history
                message
                voltages

        Raises
        ------
        ValueError
            If the network or Ybus is invalid.
        """

        # -----------------------------------------------------
        # Validate numerical options
        # -----------------------------------------------------

        self.options.validate()

        # -----------------------------------------------------
        # Reset diagnostic history.
        #
        # A solver object may legitimately be reused for
        # multiple power-flow studies.
        # -----------------------------------------------------

        self.history = []

        # -----------------------------------------------------
        # Validate network
        # -----------------------------------------------------

        if not hasattr(
            self.network,
            "buses"
        ):

            raise ValueError(
                "Network must provide a 'buses' collection"
            )

        if len(
            self.network.buses
        ) == 0:

            raise ValueError(
                "Network contains no buses"
            )

        # -----------------------------------------------------
        # Ybus must already exist.
        #
        # Ybus construction belongs to the Network/Core layer,
        # not to the Newton-Raphson solver.
        # -----------------------------------------------------

        Ybus = getattr(
            self.network,
            "Ybus",
            None
        )

        if Ybus is None:

            raise ValueError(
                "Network Ybus has not been built"
            )

        # -----------------------------------------------------
        # Validate Ybus dimensions.
        # -----------------------------------------------------

        n = len(
            self.network.buses
        )

        if not hasattr(
            Ybus,
            "shape"
        ):

            raise ValueError(
                "Network Ybus must provide a matrix shape"
            )

        if Ybus.shape != (
            n,
            n
        ):

            raise ValueError(
                "Ybus dimension does not match "
                f"network bus count: "
                f"expected {(n, n)}, "
                f"received {Ybus.shape}"
            )

        # -----------------------------------------------------
        # Create reusable numerical components.
        #
        # They read the current Bus state each iteration.
        # -----------------------------------------------------

        mismatch_engine = PowerMismatch(
            self.network,
            Ybus
        )

        jacobian_builder = JacobianBuilder(
            self.network,
            Ybus
        )

        converted_pv = []

        last_error = np.inf

        # =====================================================
        # NEWTON-RAPHSON ITERATION
        # =====================================================

        for iteration in range(
            self.options.max_iterations
        ):

            # -------------------------------------------------
            # 1. Calculate mismatch
            # -------------------------------------------------

            mismatch = mismatch_engine.compute()

            # -------------------------------------------------
            # Handle trivial/empty state vector.
            # -------------------------------------------------

            if mismatch.size == 0:

                return self._result(
                    success=True,
                    iterations=iteration + 1,
                    error=0.0,
                    converted_pv=converted_pv,
                    message="No independent power-flow states"
                )

            # -------------------------------------------------
            # Maximum mismatch
            # -------------------------------------------------

            error = float(
                np.max(
                    np.abs(
                        mismatch
                    )
                )
            )

            last_error = error

            self.history.append(
                error
            )

            # -------------------------------------------------
            # Optional diagnostics
            # -------------------------------------------------

            if self.options.verbose:

                print(
                    f"Iteration {iteration + 1}: "
                    f"Mismatch={error:.6e}"
                )

            # -------------------------------------------------
            # 2. Convergence test
            # -------------------------------------------------

            if error <= self.options.tolerance:

                return self._result(
                    success=True,
                    iterations=iteration + 1,
                    error=error,
                    converted_pv=converted_pv,
                    message="Converged"
                )

            # -------------------------------------------------
            # 3. Reactive power limit enforcement
            #
            # The Q-limit handler is deliberately independent
            # of the NR algorithm.
            # -------------------------------------------------

            if self.options.enforce_q_limits:

                changed = (
                    self.q_handler.check_limits()
                )

                if changed:

                    converted_pv.extend(
                        changed
                    )

                    # -----------------------------------------
                    # Bus type has changed.
                    #
                    # Therefore the mismatch vector and
                    # Jacobian dimensions may have changed.
                    #
                    # Restart the NR iteration using the new
                    # bus classification.
                    # -----------------------------------------

                    continue

            # -------------------------------------------------
            # 4. Build Jacobian
            # -------------------------------------------------

            try:

                J = jacobian_builder.build()

            except Exception as error:

                return self._result(
                    success=False,
                    iterations=iteration + 1,
                    error=last_error,
                    converted_pv=converted_pv,
                    message=(
                        "Jacobian construction failed: "
                        f"{error}"
                    )
                )

            # -------------------------------------------------
            # 5. Solve:
            #
            #       J Δx = mismatch
            # -------------------------------------------------

            try:

                dx = self.linear_solver.solve(
                    J,
                    mismatch
                )

            except Exception as error:

                return self._result(
                    success=False,
                    iterations=iteration + 1,
                    error=last_error,
                    converted_pv=converted_pv,
                    message=(
                        "Linear system solution failed: "
                        f"{error}"
                    )
                )

            # -------------------------------------------------
            # 6. Validate correction vector
            # -------------------------------------------------

            expected_size = mismatch.size

            if dx.size != expected_size:

                return self._result(
                    success=False,
                    iterations=iteration + 1,
                    error=last_error,
                    converted_pv=converted_pv,
                    message=(
                        "Newton-Raphson correction vector "
                        "has incorrect dimension: "
                        f"expected {expected_size}, "
                        f"received {dx.size}"
                    )
                )

            if not np.all(
                np.isfinite(dx)
            ):

                return self._result(
                    success=False,
                    iterations=iteration + 1,
                    error=last_error,
                    converted_pv=converted_pv,
                    message=(
                        "Newton-Raphson correction contains "
                        "NaN or infinite values"
                    )
                )

            # -------------------------------------------------
            # 7. Update voltage state
            # -------------------------------------------------

            try:

                self._update_states(
                    dx,
                    jacobian_builder
                )

            except Exception as error:

                return self._result(
                    success=False,
                    iterations=iteration + 1,
                    error=last_error,
                    converted_pv=converted_pv,
                    message=(
                        "Voltage state update failed: "
                        f"{error}"
                    )
                )

        # =====================================================
        # MAXIMUM ITERATIONS REACHED
        # =====================================================

        return self._result(
            success=False,
            iterations=self.options.max_iterations,
            error=last_error,
            converted_pv=converted_pv,
            message="Maximum iterations reached"
        )

    # =========================================================
    # STATE UPDATE
    # =========================================================

    def _update_states(
        self,
        dx,
        jacobian_builder
    ):
        """
        Apply Newton-Raphson correction to the Bus state.

        State vector ordering:

            dx =
                [
                    Δθ_non_slack,
                    ΔV_PQ
                ]

        The indexing is obtained directly from the
        JacobianBuilder so that the solver cannot silently
        diverge from the Jacobian/mismatch ordering.

        Parameters
        ----------
        dx:
            Newton-Raphson correction vector.

        jacobian_builder:
            JacobianBuilder instance providing state indices.
        """

        buses = self.network.buses

        indices = (
            jacobian_builder.state_indices()
        )

        angle_indices = indices[
            "angle"
        ]

        voltage_indices = indices[
            "voltage"
        ]

        expected_size = (
            len(angle_indices)
            +
            len(voltage_indices)
        )

        if dx.size != expected_size:

            raise ValueError(
                "Correction vector size does not match "
                "Jacobian state structure: "
                f"expected {expected_size}, "
                f"received {dx.size}"
            )

        # -----------------------------------------------------
        # Angle correction
        # -----------------------------------------------------

        offset = 0

        for local_index, bus_index in enumerate(
            angle_indices
        ):

            buses[
                bus_index
            ].theta += (
                self.options.damping
                *
                dx[
                    offset + local_index
                ]
            )

        # -----------------------------------------------------
        # Voltage magnitude correction
        # -----------------------------------------------------

        voltage_offset = (
            len(angle_indices)
        )

        for local_index, bus_index in enumerate(
            voltage_indices
        ):

            buses[
                bus_index
            ].V += (
                self.options.damping
                *
                dx[
                    voltage_offset + local_index
                ]
            )

    # =========================================================
    # RESULT
    # =========================================================

    def _result(
        self,
        success,
        iterations,
        error,
        converted_pv,
        message=None
    ):
        """
        Construct the standard GridForge power-flow result.
        """

        return {
            "success": bool(
                success
            ),

            "iterations": int(
                iterations
            ),

            "error": float(
                error
            ),

            "pv_to_pq": list(
                converted_pv
            ),

            "history": list(
                self.history
            ),

            "message": message,

            "voltages": self._voltage_result()
        }

    # =========================================================
    # VOLTAGE RESULT
    # =========================================================

    def _voltage_result(self):
        """
        Return the current network voltage state.

        Returns
        -------
        dict
            Vm:
                Voltage magnitudes in pu.

            Va:
                Voltage angles in radians.
        """

        return {
            "Vm": np.asarray(
                [
                    bus.V
                    for bus in self.network.buses
                ],
                dtype=float
            ),

            "Va": np.asarray(
                [
                    bus.theta
                    for bus in self.network.buses
                ],
                dtype=float
            )
        }

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(self):
        """
        Return solver configuration and runtime information.
        """

        return {
            "solver": "Newton-Raphson",
            "buses": len(
                self.network.buses
            ),
            "tolerance": self.options.tolerance,
            "max_iterations": (
                self.options.max_iterations
            ),
            "damping": self.options.damping,
            "regularization": (
                self.options.regularization
            ),
            "enforce_q_limits": (
                self.options.enforce_q_limits
            ),
            "q_limit_tolerance": (
                self.options.q_limit_tolerance
            ),
            "iterations_completed": len(
                self.history
            ),
            "last_mismatch": (
                self.history[-1]
                if self.history
                else None
            )
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self):
        """
        Developer-friendly representation.
        """

        return (
            "NewtonRaphsonSolver("
            f"buses={len(self.network.buses)}, "
            f"tolerance={self.options.tolerance}, "
            f"max_iterations="
            f"{self.options.max_iterations}"
            ")"
        )
```
