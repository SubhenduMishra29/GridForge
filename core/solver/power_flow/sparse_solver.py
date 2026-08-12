"""
GridForge Sparse Linear Solver
==============================

File:
    core/solver/power_flow/sparse_solver.py

GridForge Power Flow Engine v1.0
--------------------------------

Industrial linear-system backend for the GridForge
Newton-Raphson power-flow engine.

Responsibilities
----------------
- Solve J * dx = rhs.
- Accept dense and SciPy sparse matrices.
- Validate matrix and vector dimensions.
- Validate numerical finiteness.
- Apply explicitly requested diagonal regularization.
- Return a deterministic correction vector.
- Provide lightweight diagnostics.

This module is deliberately independent of:

- Network
- Bus
- Ybus
- PowerMismatch
- JacobianBuilder
- Newton-Raphson iteration
- PV/PQ classification
- Reactive-power limits

The public interface represents a linear-algebra service.

Implementation note
-------------------
The V1.0 reference implementation uses NumPy's dense
linear-system solver after normalizing sparse inputs.

This preserves a stable solver API while keeping the numerical
backend replaceable in a future implementation.

No sparse backend, GPU backend, iterative solver, or automatic
regularization is selected implicitly.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from numbers import Real
from typing import Any

import numpy as np


class SparseLinearSolver:
    """
    Solve linear systems used by the GridForge
    Newton-Raphson power-flow engine.

    Parameters
    ----------
    regularization:
        Non-negative diagonal regularization parameter.

        ``0.0``:
            Solve the original system:

                J dx = rhs

        ``lambda > 0``:
            Solve:

                (J + lambda I) dx = rhs

        Regularization is never enabled implicitly.

    Notes
    -----
    The solver accepts:

        - NumPy dense arrays
        - SciPy sparse matrices

    The public API does not expose the underlying numerical
    backend, allowing the implementation to evolve without
    changing the Power Flow Engine interface.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        regularization: float = 0.0,
    ) -> None:
        """
        Initialize the linear solver.
        """

        if isinstance(
            regularization,
            bool,
        ) or not isinstance(
            regularization,
            Real,
        ):
            raise TypeError(
                "regularization must be a real number."
            )

        regularization = float(
            regularization
        )

        if not np.isfinite(
            regularization
        ):
            raise ValueError(
                "regularization must be finite."
            )

        if regularization < 0.0:
            raise ValueError(
                "regularization cannot be negative."
            )

        self.regularization = regularization

    # =========================================================
    # MATRIX VALIDATION
    # =========================================================

    @staticmethod
    def _validate_matrix(
        J: Any,
    ) -> tuple[int, int]:
        """
        Validate the structural properties of the matrix.

        Returns
        -------
        tuple[int, int]
            Matrix dimensions.
        """

        if J is None:
            raise ValueError(
                "Jacobian matrix J cannot be None."
            )

        if not hasattr(
            J,
            "shape",
        ):
            raise ValueError(
                "Jacobian matrix must provide a shape."
            )

        shape = J.shape

        if len(shape) != 2:
            raise ValueError(
                "Jacobian matrix must be two-dimensional."
            )

        rows, cols = shape

        if rows != cols:
            raise ValueError(
                "Jacobian matrix must be square: "
                f"received shape {shape}."
            )

        return int(rows), int(cols)

    # =========================================================
    # MATRIX NORMALIZATION
    # =========================================================

    @staticmethod
    def _to_dense(
        J: Any,
        shape: tuple[int, int],
    ) -> np.ndarray:
        """
        Normalize dense or sparse matrix input to a NumPy
        floating-point matrix.

        Notes
        -----
        The reference implementation deliberately solves the
        normalized dense representation.
        """

        try:

            if hasattr(
                J,
                "toarray",
            ):
                matrix = np.asarray(
                    J.toarray(),
                    dtype=float,
                )

            else:
                matrix = np.asarray(
                    J,
                    dtype=float,
                )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Jacobian matrix could not be converted "
                "to a finite numerical matrix."
            ) from exc

        if matrix.shape != shape:
            raise ValueError(
                "Jacobian matrix shape changed during "
                "normalization."
            )

        if not np.all(
            np.isfinite(matrix)
        ):
            raise ValueError(
                "Jacobian matrix contains "
                "NaN or infinite values."
            )

        return matrix

    # =========================================================
    # RHS VALIDATION
    # =========================================================

    @staticmethod
    def _normalize_rhs(
        rhs: Any,
        expected_size: int,
    ) -> np.ndarray:
        """
        Normalize and validate the right-hand-side vector.
        """

        if rhs is None:
            raise ValueError(
                "Right-hand-side vector cannot be None."
            )

        try:

            rhs_array = np.asarray(
                rhs,
                dtype=float,
            ).reshape(-1)

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Right-hand-side vector must contain "
                "real numerical values."
            ) from exc

        if rhs_array.size != expected_size:
            raise ValueError(
                "Linear-system dimension mismatch: "
                f"Jacobian has dimension {expected_size}, "
                f"but RHS has dimension "
                f"{rhs_array.size}."
            )

        if not np.all(
            np.isfinite(rhs_array)
        ):
            raise ValueError(
                "Right-hand-side vector contains "
                "NaN or infinite values."
            )

        return rhs_array

    # =========================================================
    # MAIN SOLVE
    # =========================================================

    def solve(
        self,
        J: Any,
        rhs: Any,
    ) -> np.ndarray:
        """
        Solve the linear system:

            J dx = rhs

        or, when explicit regularization is enabled:

            (J + lambda I) dx = rhs

        Parameters
        ----------
        J:
            Square dense or sparse Jacobian matrix.

        rhs:
            One-dimensional right-hand-side vector.

        Returns
        -------
        numpy.ndarray
            One-dimensional finite correction vector.

        Raises
        ------
        ValueError
            If dimensions or numerical values are invalid.

        RuntimeError
            If the linear system cannot be solved.
        """

        # -----------------------------------------------------
        # Validate matrix structure.
        # -----------------------------------------------------

        rows, cols = self._validate_matrix(
            J
        )

        # -----------------------------------------------------
        # Validate RHS.
        # -----------------------------------------------------

        rhs_array = self._normalize_rhs(
            rhs,
            rows,
        )

        # -----------------------------------------------------
        # Empty system.
        # -----------------------------------------------------

        if rows == 0:
            return np.empty(
                0,
                dtype=float,
            )

        # -----------------------------------------------------
        # Normalize matrix.
        # -----------------------------------------------------

        matrix = self._to_dense(
            J,
            (rows, cols),
        )

        # -----------------------------------------------------
        # Explicit regularization.
        # -----------------------------------------------------

        if self.regularization > 0.0:

            matrix = (
                matrix
                +
                self.regularization
                *
                np.eye(
                    rows,
                    dtype=float,
                )
            )

        # -----------------------------------------------------
        # Solve.
        # -----------------------------------------------------

        try:

            dx = np.linalg.solve(
                matrix,
                rhs_array,
            )

        except np.linalg.LinAlgError as exc:

            raise RuntimeError(
                "Linear system could not be solved: "
                f"{exc}"
            ) from exc

        except Exception as exc:

            raise RuntimeError(
                "Unexpected linear-system failure: "
                f"{exc}"
            ) from exc

        # -----------------------------------------------------
        # Normalize result.
        # -----------------------------------------------------

        try:

            dx = np.asarray(
                dx,
                dtype=float,
            ).reshape(-1)

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise RuntimeError(
                "Linear solver returned an invalid "
                "solution vector."
            ) from exc

        # -----------------------------------------------------
        # Validate result.
        # -----------------------------------------------------

        if dx.size != rows:
            raise RuntimeError(
                "Linear solver returned an incorrect "
                "solution dimension: "
                f"expected {rows}, "
                f"received {dx.size}."
            )

        if not np.all(
            np.isfinite(dx)
        ):
            raise RuntimeError(
                "Linear solver returned NaN or "
                "infinite values."
            )

        return dx

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(
        self,
    ) -> dict:
        """
        Return linear-solver configuration information.
        """

        return {
            "solver": "SparseLinearSolver",
            "version": "1.0",
            "regularization": float(
                self.regularization
            ),
            "backend": "numpy",
            "supports_dense_input": True,
            "supports_sparse_input": True,
            "automatic_regularization": False,
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
            "SparseLinearSolver("
            f"regularization="
            f"{self.regularization}"
            ")"
        )


__all__ = [
    "SparseLinearSolver",
]
