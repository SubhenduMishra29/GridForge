"""
GridForge Newton-Raphson Jacobian Builder
=========================================

File:
    core/solver/common/jacobian.py

Purpose:
    Assemble the analytical Jacobian matrix used by the
    Newton-Raphson AC power-flow solver.

-----------------------------------------------------------------------
JACOBIAN STRUCTURE
-----------------------------------------------------------------------

The Newton-Raphson state vector is:

    Δx =
        [ Δθ_non_slack,
          ΔV_PQ ]

The mismatch vector is:

    Δf =
        [ ΔP_non_slack,
          ΔQ_PQ ]

Therefore:

              [ ∂P/∂θ   ∂P/∂V ]
    J =       [               ]
              [ ∂Q/∂θ   ∂Q/∂V ]

or:

              [ J1  J2 ]
    J =       [        ]
              [ J3  J4 ]

where:

    J1 = ∂P/∂θ
    J2 = ∂P/∂V
    J3 = ∂Q/∂θ
    J4 = ∂Q/∂V

-----------------------------------------------------------------------
BUS TYPE HANDLING
-----------------------------------------------------------------------

SLACK:
    No ΔP equation
    No ΔQ equation
    No θ state variable
    No V state variable

PV:
    ΔP equation
    θ state variable
    V fixed

PQ:
    ΔP equation
    ΔQ equation
    θ state variable
    V state variable

-----------------------------------------------------------------------
RESPONSIBILITIES
-----------------------------------------------------------------------

This module:

    - Reads the current voltage state.
    - Calculates analytical Jacobian blocks.
    - Maintains state/mismatch ordering consistency.

This module does NOT:

    - Build Ybus.
    - Modify bus states.
    - Solve the linear system.
    - Perform Newton-Raphson iteration.
    - Handle generator Q limits.
    - Perform convergence checking.

-----------------------------------------------------------------------
DEPENDENCIES
-----------------------------------------------------------------------

Expected Bus interface:

    bus.V
    bus.theta

    bus.is_slack()
    bus.is_pq()

Expected Network interface:

    network.buses

Expected Ybus:

    Complex n × n matrix corresponding exactly to
    network.buses ordering.

-----------------------------------------------------------------------
NUMERICAL BASELINE
-----------------------------------------------------------------------

The implementation uses explicit analytical equations and dense
Jacobian blocks.

This is intentionally the reference implementation.

Future versions may provide:

    - sparse Jacobian assembly
    - vectorized assembly
    - GPU assembly
    - automatic differentiation

without changing the external Jacobian interface.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import numpy as np

from core.solver.common.mismatch import PowerMismatch


class JacobianBuilder:
    """
    Build the analytical Newton-Raphson Jacobian.

    Parameters
    ----------
    network:
        GridForge Network object.

    Ybus:
        Optional complex bus admittance matrix.

        If omitted, ``network.Ybus`` is used.

    Notes
    -----
    The Ybus bus ordering must exactly match ``network.buses``.
    """

    def __init__(
        self,
        network,
        Ybus=None
    ):
        """
        Initialize the Jacobian builder.

        Parameters
        ----------
        network:
            GridForge network containing the ordered bus list.

        Ybus:
            Optional Ybus matrix. If ``None``, the matrix stored
            in ``network.Ybus`` is used.
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

        # ---------------------------------------------------------
        # Ybus ownership remains outside this module.
        #
        # The Jacobian builder consumes an already constructed
        # electrical network model.
        # ---------------------------------------------------------

        if Ybus is None:
            Ybus = getattr(
                network,
                "Ybus",
                None
            )

        if Ybus is None:
            raise ValueError(
                "Ybus is required to build the Jacobian"
            )

        self.Ybus = Ybus

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
        Validate Ybus dimensions against the network.

        Raises
        ------
        ValueError
            If Ybus dimensions do not match the bus count.
        """

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
    # MATRIX NORMALIZATION
    # =============================================================

    def _dense_ybus(self):
        """
        Return Ybus as a dense complex NumPy array.

        The baseline Jacobian implementation is dense.

        Sparse/GPU Jacobian assembly can be introduced later while
        retaining this public interface.
        """

        if hasattr(self.Ybus, "toarray"):
            Y = self.Ybus.toarray()
        else:
            Y = np.asarray(
                self.Ybus,
                dtype=complex
            )

        return Y

    # =============================================================
    # BUILD JACOBIAN
    # =============================================================

    def build(self):
        """
        Assemble and return the complete Newton-Raphson Jacobian.

        Returns
        -------
        ndarray
            Dense Jacobian matrix.

        Matrix structure:

            [ J1  J2 ]
            [ J3  J4 ]

        where:

            J1 = dP/dθ
            J2 = dP/dV
            J3 = dQ/dθ
            J4 = dQ/dV
        """

        # ---------------------------------------------------------
        # Network state
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Prevent division by zero in diagonal dP/dV and dQ/dV
        # equations.
        # ---------------------------------------------------------

        if np.any(
            np.isclose(
                V,
                0.0
            )
        ):
            raise ValueError(
                "Cannot build Jacobian with zero bus voltage"
            )

        # ---------------------------------------------------------
        # Ybus
        # ---------------------------------------------------------

        Y = self._dense_ybus()

        G = Y.real
        B = Y.imag

        # =========================================================
        # STATE INDEXING
        # =========================================================

        # ---------------------------------------------------------
        # P equations and theta state variables:
        #
        # all non-slack buses
        # ---------------------------------------------------------

        pvpq = [
            i
            for i, bus in enumerate(self.buses)
            if not bus.is_slack()
        ]

        # ---------------------------------------------------------
        # Q equations and V state variables:
        #
        # PQ buses only
        # ---------------------------------------------------------

        pq = [
            i
            for i, bus in enumerate(self.buses)
            if bus.is_pq()
        ]

        npvpq = len(pvpq)
        npq = len(pq)

        # =========================================================
        # JACOBIAN BLOCKS
        # =========================================================

        J1 = np.zeros(
            (npvpq, npvpq),
            dtype=float
        )

        J2 = np.zeros(
            (npvpq, npq),
            dtype=float
        )

        J3 = np.zeros(
            (npq, npvpq),
            dtype=float
        )

        J4 = np.zeros(
            (npq, npq),
            dtype=float
        )

        # =========================================================
        # POWER INJECTIONS
        # =========================================================

        # ---------------------------------------------------------
        # Use the same power equations as PowerMismatch.
        #
        # This is important:
        #
        #     mismatch.py
        #          and
        #     jacobian.py
        #
        # must use exactly the same network convention.
        # ---------------------------------------------------------

        mismatch_engine = PowerMismatch(
            self.network,
            self.Ybus
        )

        P, Q = mismatch_engine.compute_power()

        # =========================================================
        # J1 = dP/dθ
        # =========================================================

        for row, i in enumerate(pvpq):

            for col, j in enumerate(pvpq):

                if i == j:

                    # -------------------------------------------------
                    # Diagonal:
                    #
                    # dP_i / dθ_i
                    #
                    # = -Q_i - B_ii V_i²
                    # -------------------------------------------------

                    J1[row, col] = (
                        -Q[i]
                        -
                        B[i, i] * V[i] ** 2
                    )

                else:

                    angle = (
                        theta[i]
                        -
                        theta[j]
                    )

                    J1[row, col] = (
                        V[i]
                        *
                        V[j]
                        *
                        (
                            G[i, j]
                            *
                            np.sin(angle)
                            -
                            B[i, j]
                            *
                            np.cos(angle)
                        )
                    )

        # =========================================================
        # J2 = dP/dV
        # =========================================================

        for row, i in enumerate(pvpq):

            for col, j in enumerate(pq):

                if i == j:

                    # -------------------------------------------------
                    # Diagonal:
                    #
                    # dP_i / dV_i
                    #
                    # = P_i / V_i + G_ii V_i
                    # -------------------------------------------------

                    J2[row, col] = (
                        P[i] / V[i]
                        +
                        G[i, i] * V[i]
                    )

                else:

                    angle = (
                        theta[i]
                        -
                        theta[j]
                    )

                    J2[row, col] = (
                        V[i]
                        *
                        (
                            G[i, j]
                            *
                            np.cos(angle)
                            +
                            B[i, j]
                            *
                            np.sin(angle)
                        )
                    )

        # =========================================================
        # J3 = dQ/dθ
        # =========================================================

        for row, i in enumerate(pq):

            for col, j in enumerate(pvpq):

                if i == j:

                    # -------------------------------------------------
                    # Diagonal:
                    #
                    # dQ_i / dθ_i
                    #
                    # = P_i - G_ii V_i²
                    # -------------------------------------------------

                    J3[row, col] = (
                        P[i]
                        -
                        G[i, i] * V[i] ** 2
                    )

                else:

                    angle = (
                        theta[i]
                        -
                        theta[j]
                    )

                    J3[row, col] = (
                        -V[i]
                        *
                        V[j]
                        *
                        (
                            G[i, j]
                            *
                            np.cos(angle)
                            +
                            B[i, j]
                            *
                            np.sin(angle)
                        )
                    )

        # =========================================================
        # J4 = dQ/dV
        # =========================================================

        for row, i in enumerate(pq):

            for col, j in enumerate(pq):

                if i == j:

                    # -------------------------------------------------
                    # Diagonal:
                    #
                    # dQ_i / dV_i
                    #
                    # = Q_i / V_i - B_ii V_i
                    # -------------------------------------------------

                    J4[row, col] = (
                        Q[i] / V[i]
                        -
                        B[i, i] * V[i]
                    )

                else:

                    angle = (
                        theta[i]
                        -
                        theta[j]
                    )

                    J4[row, col] = (
                        V[i]
                        *
                        (
                            G[i, j]
                            *
                            np.sin(angle)
                            -
                            B[i, j]
                            *
                            np.cos(angle)
                        )
                    )

        # =========================================================
        # FINAL ASSEMBLY
        # =========================================================

        J = np.block(
            [
                [J1, J2],
                [J3, J4]
            ]
        )

        return J

    # =============================================================
    # STATE INDEX INFORMATION
    # =============================================================

    def state_indices(self):
        """
        Return the state-variable indexing used by the Jacobian.

        Returns
        -------
        dict

            {
                "angle": [...],
                "voltage": [...]
            }

        ``angle`` contains non-slack bus indices.

        ``voltage`` contains PQ bus indices.

        This information is useful to the Newton-Raphson solver
        when applying the solved correction vector.
        """

        return {
            "angle": [
                i
                for i, bus in enumerate(self.buses)
                if not bus.is_slack()
            ],
            "voltage": [
                i
                for i, bus in enumerate(self.buses)
                if bus.is_pq()
            ]
        }

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self):
        """
        Return Jacobian structure information.
        """

        indices = self.state_indices()

        n_angle = len(
            indices["angle"]
        )

        n_voltage = len(
            indices["voltage"]
        )

        return {
            "buses": self.n,
            "angle_states": n_angle,
            "voltage_states": n_voltage,
            "jacobian_shape": (
                n_angle + n_voltage,
                n_angle + n_voltage
            )
        }

    def __repr__(self):
        """
        Developer-friendly representation.
        """

        return (
            "JacobianBuilder("
            f"buses={self.n}, "
            f"shape={self.summary()['jacobian_shape']}"
            ")"
        )
