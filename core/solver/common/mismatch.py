"""
GridForge Power Mismatch Engine
===============================

File:
    core/solver/common/mismatch.py

Purpose:
    Compute AC power injections and the Newton-Raphson
    power mismatch vector.

This module is shared numerical infrastructure and is
therefore located under:

    core/solver/common/

It is NOT specific to the Power Flow solver package.

-----------------------------------------------------------------------
POWER INJECTION EQUATIONS
-----------------------------------------------------------------------

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

-----------------------------------------------------------------------
MISMATCH DEFINITION
-----------------------------------------------------------------------

    ΔP = P_spec - P_calc
    ΔQ = Q_spec - Q_calc

The Newton-Raphson state vector follows the standard AC
power-flow formulation:

    Δx =
        [ Δθ for non-SLACK buses,
          ΔV for PQ buses ]

Therefore the mismatch vector is:

    mismatch =
        [ ΔP for non-SLACK buses,
          ΔQ for PQ buses ]

-----------------------------------------------------------------------
BUS TYPE HANDLING
-----------------------------------------------------------------------

    SLACK:
        ΔP excluded
        ΔQ excluded

    PV:
        ΔP included
        ΔQ excluded

    PQ:
        ΔP included
        ΔQ included

-----------------------------------------------------------------------
RESPONSIBILITIES
-----------------------------------------------------------------------

This module:

    - Reads the electrical state from the unified Bus model.
    - Calculates P and Q injections from Ybus.
    - Builds the Newton-Raphson mismatch vector.
    - Provides calculated P/Q for other numerical components.

This module does NOT:

    - Build Ybus.
    - Modify network topology.
    - Modify bus state.
    - Solve Newton-Raphson equations.
    - Perform convergence control.
    - Handle generator reactive limits.
    - Perform contingency analysis.
    - Perform short-circuit analysis.

-----------------------------------------------------------------------
DEPENDENCIES
-----------------------------------------------------------------------

Expected Bus interface:

    bus.V
    bus.theta
    bus.P_spec
    bus.Q_spec

    bus.is_slack()
    bus.is_pq()

Expected Network interface:

    network.buses

The supplied Ybus must use exactly the same bus ordering as
network.buses.

-----------------------------------------------------------------------
NUMERICAL BASELINE
-----------------------------------------------------------------------

The implementation intentionally uses the conventional O(n²)
formulation.

This is the reference implementation for correctness.

Future optimization may introduce:

    - vectorized evaluation
    - sparse-aware evaluation
    - GPU evaluation
    - batched power-flow evaluation

Those optimizations must preserve the numerical behavior of
this baseline implementation.

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
        Bus admittance matrix corresponding exactly to
        ``network.buses`` ordering.

    Notes
    -----
    The object does not modify the network.

    The voltage state is read directly from each Bus object
    every time ``compute_power()`` or ``compute()`` is called.
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
            If the network has no buses or Ybus dimensions do
            not match the number of buses.
        """

        if network is None:
            raise ValueError(
                "Network cannot be None"
            )

        if not hasattr(network, "buses"):
            raise ValueError(
                "Network must provide a 'buses' collection"
            )

        self.network = network
        self.Ybus = Ybus

        # ---------------------------------------------------------
        # Bus ordering
        # ---------------------------------------------------------
        #
        # Ybus row/column i corresponds to network.buses[i].
        #
        # This ordering must remain stable during a solver run.
        # ---------------------------------------------------------

        self.buses = network.buses
        self.n = len(self.buses)

        if self.n == 0:
            raise ValueError(
                "Network contains no buses"
            )

        self._validate_ybus()

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_ybus(self):
        """
        Validate the supplied Ybus matrix.

        Both dense NumPy arrays and SciPy sparse matrices are
        supported.

        Raises
        ------
        ValueError
            If Ybus is missing or has incorrect dimensions.
        """

        if self.Ybus is None:
            raise ValueError(
                "Ybus cannot be None"
            )

        if not hasattr(self.Ybus, "shape"):
            raise ValueError(
                "Ybus must provide a matrix shape"
            )

        expected_shape = (
            self.n,
            self.n
        )

        if self.Ybus.shape != expected_shape:
            raise ValueError(
                "Ybus dimension does not match network bus count: "
                f"expected {expected_shape}, "
                f"received {self.Ybus.shape}"
            )

    # =============================================================
    # INTERNAL VOLTAGE STATE
    # =============================================================

    def _voltage_state(self):
        """
        Read the current voltage state from the network.

        Returns
        -------
        V : ndarray
            Voltage magnitudes in per-unit.

        theta : ndarray
            Voltage angles in radians.

        Notes
        -----
        The values are read every time this method is called.
        This is intentional because Newton-Raphson modifies the
        bus state after every iteration.
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

        return V, theta

    # =============================================================
    # POWER CALCULATION
    # =============================================================

    def compute_power(self):
        """
        Calculate active and reactive power injections.

        Returns
        -------
        P : ndarray
            Calculated active power injection at every bus.

        Q : ndarray
            Calculated reactive power injection at every bus.

        Notes
        -----
        Positive P/Q follow the network injection convention
        represented by the Ybus equations.

        This method performs no state modification.
        """

        V, theta = self._voltage_state()

        # ---------------------------------------------------------
        # Extract conductance and susceptance matrices.
        #
        # np.asarray() also allows this implementation to operate
        # with a normal dense NumPy Ybus.
        #
        # Sparse Ybus is converted only for this baseline
        # implementation. The sparse/GPU optimized implementation
        # can be introduced later without changing this API.
        # ---------------------------------------------------------

        if hasattr(self.Ybus, "toarray"):
            Y = self.Ybus.toarray()
        else:
            Y = np.asarray(
                self.Ybus,
                dtype=complex
            )

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

        # ---------------------------------------------------------
        # Conventional AC power-flow equations.
        #
        # This O(n²) implementation is intentionally kept simple
        # and transparent as the numerical reference implementation.
        # ---------------------------------------------------------

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
                # Active power injection
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
                # Reactive power injection
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

    # =============================================================
    # MISMATCH VECTOR
    # =============================================================

    def compute(self):
        """
        Build the Newton-Raphson mismatch vector.

        Returns
        -------
        ndarray
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
        The returned vector ordering MUST match the state-variable
        ordering used by the Jacobian and Newton-Raphson solver.
        """

        P_calc, Q_calc = self.compute_power()

        dP = []
        dQ = []

        # ---------------------------------------------------------
        # Construct ΔP and ΔQ blocks separately.
        #
        # Keeping the two blocks separate is important because
        # the Jacobian uses the same ordering:
        #
        #       [ ΔP ]
        #       [ ΔQ ]
        #
        # rather than interleaving P and Q per bus.
        # ---------------------------------------------------------

        for i, bus in enumerate(self.buses):

            # -----------------------------------------------------
            # Active-power mismatch
            #
            # Slack bus has fixed V and theta, therefore it does
            # not contribute an independent P equation.
            # -----------------------------------------------------

            if not bus.is_slack():

                dP.append(
                    bus.P_spec
                    -
                    P_calc[i]
                )

        for i, bus in enumerate(self.buses):

            # -----------------------------------------------------
            # Reactive-power mismatch
            #
            # Only PQ buses have independently specified Q.
            # -----------------------------------------------------

            if bus.is_pq():

                dQ.append(
                    bus.Q_spec
                    -
                    Q_calc[i]
                )

        # ---------------------------------------------------------
        # Convert to NumPy arrays.
        #
        # np.concatenate() is used instead of np.array(dP + dQ)
        # so the intended block structure remains explicit.
        # ---------------------------------------------------------

        dp_array = np.asarray(
            dP,
            dtype=float
        )

        dq_array = np.asarray(
            dQ,
            dtype=float
        )

        return np.concatenate(
            (
                dp_array,
                dq_array
            )
        )

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def max_mismatch(self):
        """
        Return the maximum absolute mismatch.

        Returns
        -------
        float
            Infinity norm of the mismatch vector.

        Notes
        -----
        This is useful for convergence monitoring but does not
        perform convergence checking itself.
        """

        mismatch = self.compute()

        if mismatch.size == 0:
            return 0.0

        return float(
            np.max(
                np.abs(mismatch)
            )
        )

    # =============================================================
    # DEBUG / INTROSPECTION
    # =============================================================

    def summary(self):
        """
        Return diagnostic information about the mismatch engine.

        Returns
        -------
        dict
            Basic configuration and network information.
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
