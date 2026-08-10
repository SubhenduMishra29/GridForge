"""
GridForge Sparse Linear Solver
==============================

File:
    core/solver/power_flow/sparse_solver.py

Purpose:
    Solve the Newton-Raphson linear correction equation:

        J * Δx = mismatch

This module provides the linear algebra layer between the
Newton-Raphson solver and the underlying numerical library.

-----------------------------------------------------------------------
SUPPORTED SOLUTION MODES
-----------------------------------------------------------------------

Preferred:

    SciPy sparse direct solver

Fallback:

    NumPy dense solver

The fallback exists primarily for:

    - environments without SciPy
    - small test systems
    - development/debugging

-----------------------------------------------------------------------
NUMERICAL SAFEGUARDS
-----------------------------------------------------------------------

Supports optional diagonal regularization:

    J_reg = J + λI

where λ is supplied through ``regularization``.

Regularization should normally remain zero.

It is a numerical recovery mechanism rather than a substitute
for a correctly formed Jacobian.

-----------------------------------------------------------------------
RESPONSIBILITIES
-----------------------------------------------------------------------

This module:

    - Validates linear-system dimensions.
    - Solves J Δx = mismatch.
    - Supports sparse SciPy solving.
    - Provides dense fallback.
    - Detects NaN/Inf results.
    - Reports numerical failures clearly.

This module does NOT:

    - Build the Jacobian.
    - Calculate mismatch.
    - Modify bus states.
    - Perform Newton-Raphson iteration.
    - Perform convergence checking.
    - Handle Q limits.

-----------------------------------------------------------------------
INPUT CONVENTION
-----------------------------------------------------------------------

J:

    Square Jacobian matrix of dimension m × m.

mismatch:

    Vector of length m.

Output:

    Δx vector of length m.

-----------------------------------------------------------------------
FUTURE EXTENSIONS
-----------------------------------------------------------------------

The public ``solve()`` interface is intentionally simple so that
future implementations can add:

    - sparse LU
    - iterative Krylov methods
    - GPU linear solvers
    - CUDA sparse factorization
    - conditioning estimates

without changing the Newton-Raphson engine.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------
# Optional SciPy dependency
# ---------------------------------------------------------------------

try:
    from scipy.sparse import (
        csr_matrix,
        issparse,
    )

    from scipy.sparse.linalg import (
        spsolve,
    )

    SCIPY_AVAILABLE = True

except ImportError:

    SCIPY_AVAILABLE = False


class SparseLinearSolver:
    """
    Linear solver for Newton-Raphson correction equations.

    Parameters
    ----------
    regularization : float, optional
        Diagonal regularization coefficient.

        The system solved becomes:

            (J + λI) Δx = mismatch

        Default is 0.0, meaning no regularization.

    Notes
    -----
    The solver itself does not decide whether regularization is
    appropriate. That decision belongs to the higher-level solver
    configuration.
    """

    def __init__(
        self,
        regularization: float = 0.0
    ):
        """
        Initialize the linear solver.

        Parameters
        ----------
        regularization:
            Non-negative diagonal regularization coefficient.

        Raises
        ------
        ValueError
            If regularization is negative.
        """

        if regularization < 0:
            raise ValueError(
                "Regularization must be >= 0"
            )

        self.regularization = float(
            regularization
        )

    # =============================================================
    # PUBLIC SOLVE API
    # =============================================================

    def solve(
        self,
        J,
        mismatch
    ):
        """
        Solve:

            J * Δx = mismatch

        Parameters
        ----------
        J:
            Square Jacobian matrix.

        mismatch:
            One-dimensional mismatch vector.

        Returns
        -------
        ndarray
            Newton-Raphson correction vector Δx.

        Raises
        ------
        ValueError
            If dimensions or numerical inputs are invalid.

        RuntimeError
            If the linear system cannot be solved.
        """

        # ---------------------------------------------------------
        # Normalize mismatch first.
        # ---------------------------------------------------------

        mismatch = np.asarray(
            mismatch,
            dtype=float
        )

        if mismatch.ndim != 1:
            raise ValueError(
                "Mismatch must be a one-dimensional vector"
            )

        # ---------------------------------------------------------
        # Detect sparse versus dense Jacobian.
        #
        # Keeping sparse matrices sparse is important for the
        # eventual large-system implementation.
        # ---------------------------------------------------------

        is_sparse = (
            SCIPY_AVAILABLE
            and
            issparse(J)
        )

        if is_sparse:

            J_matrix = J.tocsr()

        else:

            J_matrix = np.asarray(
                J,
                dtype=float
            )

        # ---------------------------------------------------------
        # Validate dimensions.
        # ---------------------------------------------------------

        if J_matrix.ndim != 2:

            raise ValueError(
                "Jacobian must be a two-dimensional matrix"
            )

        rows, cols = J_matrix.shape

        if rows != cols:

            raise ValueError(
                "Jacobian must be square: "
                f"received shape {J_matrix.shape}"
            )

        if mismatch.size != rows:

            raise ValueError(
                "Jacobian and mismatch dimensions do not match: "
                f"Jacobian={J_matrix.shape}, "
                f"mismatch={mismatch.shape}"
            )

        # ---------------------------------------------------------
        # Empty system.
        #
        # This can occur in pathological or trivial networks.
        # Returning an empty correction is mathematically consistent.
        # ---------------------------------------------------------

        if rows == 0:

            return np.empty(
                0,
                dtype=float
            )

        # ---------------------------------------------------------
        # Validate numerical input.
        # ---------------------------------------------------------

        if not np.all(
            np.isfinite(mismatch)
        ):

            raise ValueError(
                "Mismatch contains NaN or infinite values"
            )

        # ---------------------------------------------------------
        # Apply optional regularization.
        # ---------------------------------------------------------

        if self.regularization > 0:

            if is_sparse:

                from scipy.sparse import (
                    eye
                )

                J_matrix = (
                    J_matrix
                    +
                    self.regularization
                    *
                    eye(
                        rows,
                        format="csr"
                    )
                )

            else:

                J_matrix = (
                    J_matrix
                    +
                    self.regularization
                    *
                    np.eye(
                        rows,
                        dtype=float
                    )
                )

        # =========================================================
        # SPARSE SOLUTION
        # =========================================================

        if SCIPY_AVAILABLE:

            try:

                # -------------------------------------------------
                # Convert dense matrices to CSR for the preferred
                # sparse direct solve.
                # -------------------------------------------------

                if not is_sparse:

                    J_sparse = csr_matrix(
                        J_matrix
                    )

                else:

                    J_sparse = J_matrix

                dx = spsolve(
                    J_sparse,
                    mismatch
                )

                dx = np.asarray(
                    dx,
                    dtype=float
                )

                # -------------------------------------------------
                # Validate solver output.
                # -------------------------------------------------

                self._validate_solution(
                    dx
                )

                return dx

            except Exception as sparse_error:

                # -------------------------------------------------
                # Sparse solution failed.
                #
                # Attempt dense recovery. This is useful for small
                # systems and development environments.
                # -------------------------------------------------

                try:

                    J_dense = (
                        J_matrix.toarray()
                        if hasattr(
                            J_matrix,
                            "toarray"
                        )
                        else np.asarray(
                            J_matrix,
                            dtype=float
                        )
                    )

                    return self._dense_solve(
                        J_dense,
                        mismatch,
                        sparse_error=sparse_error
                    )

                except Exception as dense_error:

                    raise RuntimeError(
                        "Linear system solution failed using "
                        "both sparse and dense solvers"
                    ) from dense_error

        # =========================================================
        # DENSE FALLBACK
        # =========================================================

        return self._dense_solve(
            J_matrix,
            mismatch
        )

    # =============================================================
    # DENSE SOLVER
    # =============================================================

    def _dense_solve(
        self,
        J,
        mismatch,
        sparse_error=None
    ):
        """
        Solve the system using NumPy dense linear algebra.

        Parameters
        ----------
        J:
            Dense square Jacobian.

        mismatch:
            Mismatch vector.

        sparse_error:
            Optional exception from the sparse solver.

        Returns
        -------
        ndarray
            Correction vector Δx.

        Raises
        ------
        RuntimeError
            If NumPy cannot solve the system.
        """

        try:

            dx = np.linalg.solve(
                J,
                mismatch
            )

            dx = np.asarray(
                dx,
                dtype=float
            )

            self._validate_solution(
                dx
            )

            return dx

        except np.linalg.LinAlgError as error:

            if sparse_error is not None:

                raise RuntimeError(
                    "Linear solve failed. "
                    "The Jacobian may be singular or "
                    "ill-conditioned. "
                    f"Sparse solver error: {sparse_error}"
                ) from error

            raise RuntimeError(
                "Linear solve failed. "
                "The Jacobian may be singular or "
                "ill-conditioned."
            ) from error

    # =============================================================
    # SOLUTION VALIDATION
    # =============================================================

    @staticmethod
    def _validate_solution(dx):
        """
        Validate a calculated correction vector.

        Raises
        ------
        RuntimeError
            If the solver returned NaN or infinite values.
        """

        if dx.ndim != 1:

            raise RuntimeError(
                "Linear solver returned an invalid vector"
            )

        if not np.all(
            np.isfinite(dx)
        ):

            raise RuntimeError(
                "Linear solver returned NaN or infinite values"
            )

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self):
        """
        Return solver configuration information.
        """

        return {
            "scipy_available": SCIPY_AVAILABLE,
            "regularization": self.regularization,
            "preferred_method": (
                "scipy.sparse.linalg.spsolve"
                if SCIPY_AVAILABLE
                else "numpy.linalg.solve"
            )
        }

    def __repr__(self):
        """
        Developer-friendly representation.
        """

        return (
            "SparseLinearSolver("
            f"scipy_available={SCIPY_AVAILABLE}, "
            f"regularization={self.regularization}"
            ")"
        )
