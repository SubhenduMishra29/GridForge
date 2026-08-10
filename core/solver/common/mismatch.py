"""
GridForge Power Mismatch Engine
================================

File
----
core/solver/common/mismatch.py

Purpose
-------
Compute AC bus power injections and the Newton-Raphson
power mismatch vector.

This module is shared numerical infrastructure and therefore
belongs under:

    core/solver/common/

It is NOT specific to the Power Flow solver package.

Power Injection Equations
-------------------------
For bus i:

    P_i = Σ V_i V_j [
            G_ij cos(θ_i - θ_j)
            +
            B_ij sin(θ_i - θ_j)
          ]

    Q_i = Σ V_i V_j [
            G_ij sin(θ_i - θ_j)
            -
            B_ij cos(θ_i - θ_j)
          ]

where:

    Y_ij = G_ij + j B_ij

Mismatch Definition
-------------------
    ΔP = P_spec - P_calc
    ΔQ = Q_spec - Q_calc

Newton-Raphson state vector:

    Δx = [
        Δθ for non-SLACK buses,
        ΔV for PQ buses
    ]

Therefore the mismatch vector is:

    mismatch = [
        ΔP for non-SLACK buses,
        ΔQ for PQ buses
    ]

Bus Type Handling
-----------------
    SLACK:
        ΔP excluded
        ΔQ excluded

    PV:
        ΔP included
        ΔQ excluded

    PQ:
        ΔP included
        ΔQ included

Responsibilities
----------------
This module:

    - Reads electrical state from the unified Bus model.
    - Calculates P and Q injections from Ybus.
    - Builds the Newton-Raphson mismatch vector.
    - Provides calculated P/Q for numerical components.
    - Provides mismatch diagnostics.

This module does NOT:

    - Build Ybus.
    - Modify network topology.
    - Modify bus state.
    - Solve Newton-Raphson equations.
    - Perform convergence control.
    - Handle generator reactive limits.
    - Perform contingency analysis.
    - Perform short-circuit analysis.

Dependencies
------------
Expected Network interface:

    network.buses

Expected Bus interface:

    bus.V
    bus.theta
    bus.P_spec
    bus.Q_spec

    bus.is_slack()
    bus.is_pq()

Ybus must use exactly the same bus ordering as
network.buses.

Numerical Baseline
------------------
The implementation intentionally uses the conventional O(n²)
formulation.

This is the reference implementation for correctness.

Future optimization may introduce:

    - Vectorized evaluation
    - Sparse-aware evaluation
    - GPU evaluation
    - Batched power-flow evaluation

Those implementations must preserve the numerical behavior
of this reference implementation.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import numpy as np


class PowerMismatch:
    """
    Calculate AC bus power injections and Newton-Raphson
    mismatch vectors.

    Parameters
    ----------
    network:
        GridForge Network object containing the ordered bus list.

    Ybus:
        Complex bus admittance matrix corresponding exactly
        to ``network.buses`` ordering.

    Notes
    -----
    The object does not modify the network.

    Voltage state is read directly from each Bus object every
    time ``compute_power()`` or ``compute()`` is called.

    This ensures that the mismatch calculation always operates
    on the current Newton-Raphson state.
    """

    def __init__(self, network, Ybus):
        """
        Initialize the mismatch calculator.

        Parameters
        ----------
        network:
            GridForge network/model containing ``buses``.

        Ybus:
            Complex bus admittance matrix.

        Raises
        ------
        ValueError
            If the network is invalid or Ybus dimensions do not
            match the number of buses.
        """

        if network is None:
            raise ValueError(
                "Network cannot be None."
            )

        if not hasattr(network, "buses"):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        self.network = network
        self.Ybus = Ybus

        # -----------------------------------------------------
        # Bus ordering
        # -----------------------------------------------------
        #
        # Ybus row/column i corresponds to network.buses[i].
        #
        # This ordering must remain unchanged while the solver
        # is operating.
        # -----------------------------------------------------

        self.buses = network.buses
        self.n = len(self.buses)

        if self.n == 0:
            raise ValueError(
                "Network contains no buses."
            )

        self._validate_ybus()

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_ybus(self):
        """
        Validate the supplied Ybus matrix.

        Dense NumPy arrays and SciPy sparse matrices are both
        supported.

        Raises
        ------
        ValueError
            If Ybus is missing or has incorrect dimensions.
        """

        if self.Ybus is None:
            raise ValueError(
                "Ybus cannot be None."
            )

        if not hasattr(self.Ybus, "shape"):
            raise ValueError(
                "Ybus must provide a matrix shape."
            )

        expected_shape = (
            self.n,
            self.n
        )

        if self.Ybus.shape != expected_shape:
            raise ValueError(
                "Ybus dimension does not match network bus count: "
                f"expected {expected_shape}, "
                f"received {self.Ybus.shape}."
            )

    # =========================================================
    # VOLTAGE STATE
    # =========================================================

    def _voltage_state(self):
        """
        Read the current voltage state from the network.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            V:
                Voltage magnitudes in per-unit.

            theta:
                Voltage angles in radians.

        Notes
        -----
        Values are read every time this method is called.

        This is intentional because the Newton-Raphson solver
        modifies the bus state after every iteration.
        """

        V = np.asarray(
            [
                bus.V
                for bus in self.buses
            ],
            dtype=float
        )

        theta = np.asarray(
            [
                bus.theta
                for bus in self.buses
            ],
            dtype=float
        )

        if not np.all(np.isfinite(V)):
            raise ValueError(
                "Bus voltage magnitude contains "
                "non-finite values."
            )

        if not np.all(np.isfinite(theta)):
            raise ValueError(
                "Bus voltage angle contains "
                "non-finite values."
            )

        if np.any(V < 0.0):
            raise ValueError(
                "Bus voltage magnitude cannot be negative."
            )

        return V, theta

    # =========================================================
    # YBUS ARRAY
    # =========================================================

    def _get_ybus_array(self):
        """
        Return Ybus as a dense complex NumPy array.

        The reference implementation uses a dense matrix so
        that the numerical equations remain transparent.

        Sparse/GPU optimized implementations can later replace
        this internal representation without changing the
        public PowerMismatch API.

        Returns
        -------
        np.ndarray
            Dense complex Ybus matrix.
        """

        if hasattr(self.Ybus, "toarray"):
            Y = self.Ybus.toarray()
        else:
            Y = np.asarray(
                self.Ybus,
                dtype=complex
            )

        if Y.shape != (self.n, self.n):
            raise ValueError(
                "Ybus shape changed after initialization: "
                f"expected {(self.n, self.n)}, "
                f"received {Y.shape}."
            )

        if not np.all(np.isfinite(Y.real)):
            raise ValueError(
                "Ybus contains non-finite real values."
            )

        if not np.all(np.isfinite(Y.imag)):
            raise ValueError(
                "Ybus contains non-finite imaginary values."
            )

        return Y

    # =========================================================
    # POWER CALCULATION
    # =========================================================

    def compute_power(self):
        """
        Calculate active and reactive power injections.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            P:
                Calculated active-power injection at every bus.

            Q:
                Calculated reactive-power injection at every bus.

        Notes
        -----
        Positive P/Q follow the network injection convention
        represented by the supplied Ybus.

        This method does not modify network or bus state.
        """

        V, theta = self._voltage_state()

        Y = self._get_ybus_array()

        G = Y.real
        B = Y.imag

        P = np.zeros(
            self.n,
            dtype=float
        )

        Q = np.zeros(
            self.n,
            dtype=float
        )

        # -----------------------------------------------------
        # Conventional AC power-flow equations.
        #
        # This O(n²) implementation is deliberately retained
        # as the GridForge numerical reference implementation.
        # -----------------------------------------------------

        for i in range(self.n):

            for j in range(self.n):

                angle = (
                    theta[i]
                    -
                    theta[j]
                )

                voltage_product = (
                    V[i]
                    *
                    V[j]
                )

                cos_angle = np.cos(angle)
                sin_angle = np.sin(angle)

                # -------------------------------------------------
                # Active power:
                #
                # P_i = Σ Vi Vj
                #       (Gij cos θij + Bij sin θij)
                # -------------------------------------------------

                P[i] += (
                    voltage_product
                    *
                    (
                        G[i, j] * cos_angle
                        +
                        B[i, j] * sin_angle
                    )
                )

                # -------------------------------------------------
                # Reactive power:
                #
                # Q_i = Σ Vi Vj
                #       (Gij sin θij - Bij cos θij)
                # -------------------------------------------------

                Q[i] += (
                    voltage_product
                    *
                    (
                        G[i, j] * sin_angle
                        -
                        B[i, j] * cos_angle
                    )
                )

        return P, Q

    # =========================================================
    # MISMATCH VECTOR
    # =========================================================

    def compute(self):
        """
        Build the Newton-Raphson mismatch vector.

        Returns
        -------
        np.ndarray
            Mismatch vector arranged as:

                [ΔP_non_slack, ΔQ_PQ]

        Bus treatment:

            SLACK:
                no mismatch

            PV:
                active-power mismatch only

            PQ:
                active and reactive mismatch

        Notes
        -----
        The returned vector ordering MUST match the state
        variable ordering used by JacobianBuilder and the
        Newton-Raphson solver.
        """

        P_calc, Q_calc = self.compute_power()

        dP = []
        dQ = []

        # -----------------------------------------------------
        # Active-power mismatch block.
        #
        # All non-slack buses contribute one ΔP equation.
        # -----------------------------------------------------

        for i, bus in enumerate(self.buses):

            if not bus.is_slack():

                dP.append(
                    bus.P_spec
                    -
                    P_calc[i]
                )

        # -----------------------------------------------------
        # Reactive-power mismatch block.
        #
        # Only PQ buses contribute one ΔQ equation.
        # -----------------------------------------------------

        for i, bus in enumerate(self.buses):

            if bus.is_pq():

                dQ.append(
                    bus.Q_spec
                    -
                    Q_calc[i]
                )

        dp_array = np.asarray(
            dP,
            dtype=float
        )

        dq_array = np.asarray(
            dQ,
            dtype=float
        )

        # -----------------------------------------------------
        # Explicit block ordering:
        #
        #     [ ΔP_non_slack ]
        #     [ ΔQ_PQ        ]
        #
        # This MUST correspond to the Jacobian structure:
        #
        #     [ J1  J2 ]
        #     [ J3  J4 ]
        # -----------------------------------------------------

        return np.concatenate(
            (
                dp_array,
                dq_array
            )
        )

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def max_mismatch(self):
        """
        Return the infinity norm of the mismatch vector.

        Returns
        -------
        float
            Maximum absolute mismatch.

        Notes
        -----
        This method provides a diagnostic quantity only.

        It does not perform convergence control.
        """

        mismatch = self.compute()

        if mismatch.size == 0:
            return 0.0

        return float(
            np.max(
                np.abs(mismatch)
            )
        )

    # =========================================================
    # DEBUG / INTROSPECTION
    # =========================================================

    def summary(self):
        """
        Return diagnostic information about the mismatch engine.

        Returns
        -------
        dict
            Configuration and network information.
        """

        slack_count = sum(
            bus.is_slack()
            for bus in self.buses
        )

        pq_count = sum(
            bus.is_pq()
            for bus in self.buses
        )

        pv_count = (
            self.n
            -
            slack_count
            -
            pq_count
        )

        return {
            "buses": self.n,
            "ybus_shape": self.Ybus.shape,
            "slack_buses": slack_count,
            "pv_buses": pv_count,
            "pq_buses": pq_count,
            "mismatch_size": (
                (self.n - slack_count)
                +
                pq_count
            )
        }

    def __repr__(self):
        """
        Developer-friendly representation.
        """

        return (
            "PowerMismatch("
            f"buses={self.n}, "
            f"Ybus_shape={self.Ybus.shape}"
            ")"
        )
