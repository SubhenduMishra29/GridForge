```python
"""
GridForge Newton-Raphson Power Flow Engine
==========================================

File:
    core/solver/power_flow/nr_solver.py

GridForge Power Flow Engine v1.0
--------------------------------

Industrial AC Newton-Raphson power-flow orchestration layer.

Responsibilities
----------------
- Newton-Raphson iteration.
- Mismatch evaluation orchestration.
- Jacobian construction orchestration.
- Linear-system solution orchestration.
- Voltage-state update.
- Convergence monitoring.
- PV/PQ reactive-limit handling.
- Solver diagnostics and result construction.

This module does NOT:
- Build Ybus.
- Calculate AC power injections directly.
- Assemble the Jacobian directly.
- Perform linear algebra directly.
- Modify network topology.
- Perform contingency analysis.
- Perform short-circuit analysis.
- Perform protection decisions.

Numerical responsibilities are delegated to:

    core.solver.common.mismatch
    core.solver.common.jacobian
    core.solver.power_flow.sparse_solver
    core.solver.power_flow.q_limit_handler

Reference state ordering
------------------------
The Newton-Raphson state vector is:

    dx = [
        dtheta_non_slack,
        dV_PQ
    ]

The mismatch vector is:

    mismatch = [
        dP_non_slack,
        dQ_PQ
    ]

The ordering is obtained from JacobianBuilder.state_indices()
and is therefore shared by:

    PowerMismatch
    JacobianBuilder
    NewtonRaphsonSolver

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import numpy as np

from core.solver.common.mismatch import (
    PowerMismatch,
)

from core.solver.common.jacobian import (
    JacobianBuilder,
)

from core.solver.power_flow.sparse_solver import (
    SparseLinearSolver,
)

from core.solver.power_flow.q_limit_handler import (
    QLimitHandler,
)


class NewtonRaphsonSolver:
    """
    Newton-Raphson AC power-flow solver.

    Parameters
    ----------
    network:
        GridForge Network object containing the unified
        electrical model.

    options:
        GridForge SolverOptions instance.

    Notes
    -----
    The network must already contain a valid Ybus.

    The solver intentionally operates on the voltage state
    stored in the unified Bus model. This allows the numerical
    engine to remain synchronized with the GridForge model.

    No numerical power-flow calculation is performed directly
    in this orchestration class.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network,
        options,
    ):
        """
        Initialize the Newton-Raphson solver.
        """

        if network is None:
            raise ValueError(
                "Network cannot be None."
            )

        if options is None:
            raise ValueError(
                "Solver options cannot be None."
            )

        if not hasattr(
            network,
            "buses",
        ):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        self.network = network
        self.options = options

        # -----------------------------------------------------
        # Linear-system backend.
        # -----------------------------------------------------

        self.linear_solver = SparseLinearSolver(
            regularization=options.regularization,
        )

        # -----------------------------------------------------
        # Reactive-power limit handler.
        # -----------------------------------------------------

        self.q_handler = QLimitHandler(
            network,
            tolerance=options.q_limit_tolerance,
        )

        # -----------------------------------------------------
        # Iteration diagnostics.
        # -----------------------------------------------------

        self.history = []

        self._converted_pv = []

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_network(self):
        """
        Validate the network and Ybus before solving.

        Raises
        ------
        ValueError
            If the network or Ybus is invalid.
        """

        if not hasattr(
            self.network,
            "buses",
        ):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        n = len(
            self.network.buses
        )

        if n == 0:
            raise ValueError(
                "Network contains no buses."
            )

        Ybus = getattr(
            self.network,
            "Ybus",
            None,
        )

        if Ybus is None:
            raise ValueError(
                "Network Ybus has not been built."
            )

        if not hasattr(
            Ybus,
            "shape",
        ):
            raise ValueError(
                "Network Ybus must provide a matrix shape."
            )

        expected_shape = (
            n,
            n,
        )

        if Ybus.shape != expected_shape:
            raise ValueError(
                "Ybus dimension does not match network "
                f"bus count: expected {expected_shape}, "
                f"received {Ybus.shape}."
            )

        return Ybus

    # =========================================================
    # COMPONENT CONSTRUCTION
    # =========================================================

    def _create_components(
        self,
        Ybus,
    ):
        """
        Create the shared numerical components.

        Components read current Bus state whenever they are
        evaluated, so they remain valid after each Newton step
        and after PV-to-PQ transitions.
        """

        mismatch_engine = PowerMismatch(
            self.network,
            Ybus,
        )

        jacobian_builder = JacobianBuilder(
            self.network,
            Ybus,
        )

        return (
            mismatch_engine,
            jacobian_builder,
        )

    # =========================================================
    # MAIN SOLVER
    # =========================================================

    def solve(self):
        """
        Execute the Newton-Raphson power-flow solution.

        Returns
        -------
        dict
            Standard GridForge power-flow result:

                success
                iterations
                error
                pv_to_pq
                history
                message
                voltages

        Notes
        -----
        The network Bus voltage state is updated in-place.
        """

        # -----------------------------------------------------
        # Validate solver configuration.
        # -----------------------------------------------------

        self.options.validate()

        # -----------------------------------------------------
        # Reset runtime diagnostics.
        # -----------------------------------------------------

        self.history = []
        self._converted_pv = []

        # QLimitHandler maintains its own diagnostic history.
        self.q_handler.reset_history()

        # -----------------------------------------------------
        # Validate network.
        # -----------------------------------------------------

        Ybus = self._validate_network()

        # -----------------------------------------------------
        # Create shared numerical components.
        # -----------------------------------------------------

        (
            mismatch_engine,
            jacobian_builder,
        ) = self._create_components(
            Ybus
        )

        last_error = np.inf

        # =====================================================
        # NEWTON-RAPHSON ITERATION
        # =====================================================

        for iteration in range(
            self.options.max_iterations
        ):

            iteration_number = (
                iteration + 1
            )

            # -------------------------------------------------
            # 1. Calculate mismatch.
            # -------------------------------------------------

            try:

                mismatch = mismatch_engine.compute()

            except Exception as exc:

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=last_error,
                    message=(
                        "Mismatch calculation failed: "
                        f"{exc}"
                    ),
                )

            mismatch = np.asarray(
                mismatch,
                dtype=float,
            ).reshape(-1)

            if not np.all(
                np.isfinite(mismatch)
            ):
                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=np.inf,
                    message=(
                        "Mismatch calculation produced "
                        "NaN or infinite values."
                    ),
                )

            # -------------------------------------------------
            # Empty state vector.
            #
            # This can occur for a network containing no
            # independent power-flow equations.
            # -------------------------------------------------

            if mismatch.size == 0:

                return self._result(
                    success=True,
                    iterations=iteration_number,
                    error=0.0,
                    message=(
                        "No independent power-flow states."
                    ),
                )

            # -------------------------------------------------
            # 2. Calculate infinity-norm mismatch.
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

            if self.options.verbose:

                print(
                    f"Iteration {iteration_number}: "
                    f"Mismatch={error:.6e}"
                )

            # -------------------------------------------------
            # 3. Convergence test.
            #
            # Convergence is checked before Q-limit conversion.
            #
            # If the current solution satisfies the equations,
            # no additional PV/PQ transition is required.
            # -------------------------------------------------

            if error <= self.options.tolerance:

                return self._result(
                    success=True,
                    iterations=iteration_number,
                    error=error,
                    message="Converged.",
                )

            # -------------------------------------------------
            # 4. Reactive-power limit handling.
            # -------------------------------------------------

            if self.options.enforce_q_limits:

                try:

                    changed = (
                        self.q_handler.check_limits()
                    )

                except Exception as exc:

                    return self._result(
                        success=False,
                        iterations=iteration_number,
                        error=error,
                        message=(
                            "Reactive-power limit "
                            "handling failed: "
                            f"{exc}"
                        ),
                    )

                if changed:

                    self._converted_pv.extend(
                        changed
                    )

                    # -----------------------------------------
                    # Bus classification has changed.
                    #
                    # Therefore the next mismatch and
                    # Jacobian must use the new PV/PQ structure.
                    #
                    # No Newton correction is calculated from
                    # the obsolete Jacobian structure.
                    # -----------------------------------------

                    continue

            # -------------------------------------------------
            # 5. Build analytical Jacobian.
            # -------------------------------------------------

            try:

                J = jacobian_builder.build()

            except Exception as exc:

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=error,
                    message=(
                        "Jacobian construction failed: "
                        f"{exc}"
                    ),
                )

            J = np.asarray(
                J,
                dtype=float,
            )

            # -------------------------------------------------
            # Validate Jacobian shape against mismatch.
            # -------------------------------------------------

            expected_dimension = (
                mismatch.size
            )

            if J.shape != (
                expected_dimension,
                expected_dimension,
            ):

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=error,
                    message=(
                        "Jacobian dimension does not match "
                        "mismatch vector: "
                        f"expected "
                        f"{(expected_dimension, expected_dimension)}, "
                        f"received {J.shape}."
                    ),
                )

            if not np.all(
                np.isfinite(J)
            ):

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=error,
                    message=(
                        "Jacobian contains NaN or "
                        "infinite values."
                    ),
                )

            # -------------------------------------------------
            # 6. Solve:
            #
            #       J dx = mismatch
            #
            # The mismatch convention is:
            #
            #       specified - calculated
            #
            # Therefore the Newton correction is solved
            # directly against the mismatch vector.
            # -------------------------------------------------

            try:

                dx = self.linear_solver.solve(
                    J,
                    mismatch,
                )

            except Exception as exc:

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=error,
                    message=(
                        "Linear system solution failed: "
                        f"{exc}"
                    ),
                )

            dx = np.asarray(
                dx,
                dtype=float,
            ).reshape(-1)

            # -------------------------------------------------
            # 7. Validate correction.
            # -------------------------------------------------

            if dx.size != expected_dimension:

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=error,
                    message=(
                        "Newton-Raphson correction vector "
                        "has incorrect dimension: "
                        f"expected {expected_dimension}, "
                        f"received {dx.size}."
                    ),
                )

            if not np.all(
                np.isfinite(dx)
            ):

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=error,
                    message=(
                        "Newton-Raphson correction contains "
                        "NaN or infinite values."
                    ),
                )

            # -------------------------------------------------
            # 8. Apply Newton correction.
            # -------------------------------------------------

            try:

                self._update_states(
                    dx,
                    jacobian_builder,
                )

            except Exception as exc:

                return self._result(
                    success=False,
                    iterations=iteration_number,
                    error=error,
                    message=(
                        "Voltage state update failed: "
                        f"{exc}"
                    ),
                )

        # =====================================================
        # MAXIMUM ITERATIONS REACHED
        # =====================================================

        return self._result(
            success=False,
            iterations=self.options.max_iterations,
            error=last_error,
            message="Maximum iterations reached.",
        )

    # =========================================================
    # STATE UPDATE
    # =========================================================

    def _update_states(
        self,
        dx,
        jacobian_builder,
    ):
        """
        Apply a Newton-Raphson correction to the Bus state.

        State ordering:

            dx =
                [
                    dtheta_non_slack,
                    dV_PQ
                ]

        The state indices are obtained directly from
        JacobianBuilder.
        """

        buses = self.network.buses

        dx = np.asarray(
            dx,
            dtype=float,
        ).reshape(-1)

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
                f"received {dx.size}."
            )

        # -----------------------------------------------------
        # Angle correction.
        # -----------------------------------------------------

        for local_index, bus_index in enumerate(
            angle_indices
        ):

            bus = buses[
                bus_index
            ]

            bus.theta += (
                self.options.damping
                *
                dx[
                    local_index
                ]
            )

        # -----------------------------------------------------
        # Voltage magnitude correction.
        # -----------------------------------------------------

        voltage_offset = len(
            angle_indices
        )

        for local_index, bus_index in enumerate(
            voltage_indices
        ):

            bus = buses[
                bus_index
            ]

            bus.V += (
                self.options.damping
                *
                dx[
                    voltage_offset + local_index
                ]
            )

        # -----------------------------------------------------
        # Immediately validate the resulting state.
        # -----------------------------------------------------

        self._validate_voltage_state()

    # =========================================================
    # VOLTAGE STATE VALIDATION
    # =========================================================

    def _validate_voltage_state(self):
        """
        Validate the complete network voltage state after a
        Newton update.

        Raises
        ------
        ValueError
            If a voltage magnitude or angle becomes invalid.
        """

        for index, bus in enumerate(
            self.network.buses
        ):

            try:

                voltage = float(
                    bus.V
                )

                angle = float(
                    bus.theta
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "Bus voltage state is not numerical "
                    f"at bus index {index}."
                ) from exc

            if not np.isfinite(
                voltage
            ):

                raise ValueError(
                    "Bus voltage magnitude became "
                    f"non-finite at bus index {index}."
                )

            if not np.isfinite(
                angle
            ):

                raise ValueError(
                    "Bus voltage angle became "
                    f"non-finite at bus index {index}."
                )

            if voltage < 0.0:

                raise ValueError(
                    "Bus voltage magnitude became negative "
                    f"at bus index {index}: {voltage}."
                )

    # =========================================================
    # RESULT
    # =========================================================

    def _result(
        self,
        success,
        iterations,
        error,
        message,
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
                self._converted_pv
            ),

            "history": list(
                self.history
            ),

            "message": message,

            "voltages": self._voltage_result(),
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
                Voltage magnitudes in per-unit.

            Va:
                Voltage angles in radians.
        """

        Vm = np.asarray(
            [
                bus.V
                for bus in self.network.buses
            ],
            dtype=float,
        )

        Va = np.asarray(
            [
                bus.theta
                for bus in self.network.buses
            ],
            dtype=float,
        )

        return {
            "Vm": Vm,
            "Va": Va,
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
            "version": "1.0",
            "buses": len(
                self.network.buses
            ),
            "tolerance": float(
                self.options.tolerance
            ),
            "max_iterations": int(
                self.options.max_iterations
            ),
            "damping": float(
                self.options.damping
            ),
            "regularization": float(
                self.options.regularization
            ),
            "enforce_q_limits": bool(
                self.options.enforce_q_limits
            ),
            "q_limit_tolerance": float(
                self.options.q_limit_tolerance
            ),
            "iterations_completed": len(
                self.history
            ),
            "last_mismatch": (
                self.history[-1]
                if self.history
                else None
            ),
            "pv_to_pq_conversions": len(
                self._converted_pv
            ),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(
        self,
    ) -> str:
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


__all__ = [
    "NewtonRaphsonSolver",
]
```
