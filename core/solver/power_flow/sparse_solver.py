```python
"""
GridForge Sparse Linear Solver
==============================

File:
    core/solver/power_flow/sparse_solver.py

Industrial linear-system backend for the GridForge
Newton-Raphson Power Flow Engine.

Responsibilities
----------------
- Solve J * dx = rhs.
- Support dense and sparse matrix inputs.
- Validate matrix/vector dimensions.
- Validate numerical finiteness.
- Provide optional explicit diagonal regularization.
- Return a deterministic correction vector.

This module is deliberately independent of:

- Network
- Bus
- Ybus
- PowerMismatch
- JacobianBuilder
- Newton-Raphson iteration
- PV/PQ classification
- Reactive-power limits

The module is a linear-algebra service only.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

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

        ``0.0`` means the original system is solved:

            J dx = rhs

        A positive value solves:

            (J + λI) dx = rhs

        This is an explicit numerical option and is never
        applied implicitly.

    Notes
    -----
    The implementation accepts both:

        - dense NumPy matrices
        - SciPy sparse matrices

    The public interface deliberately does not expose a
    particular sparse backend so that future GPU or alternative
    sparse implementations can replace this layer.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        regularization: float = 0.0,
    ):

        if isinstance(
            regularization,
            bool,
        ) or not isinstance(
            regularization,
            (int, float),
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
    # MAIN SOLVE
    # =========================================================

    def solve(
        self,
        J: Any,
        rhs: np.ndarray,
    ) -> np.ndarray:
        """
        Solve:

            J dx = rhs

        or, when regularization is explicitly enabled:

            (J + λI) dx = rhs

        Parameters
        ----------
        J:
            Square Jacobian matrix.

            Dense NumPy arrays and SciPy sparse matrices
            are supported.

        rhs:
            One-dimensional right-hand-side vector.

        Returns
        -------
        np.ndarray
            One-dimensional finite correction vector.

        Raises
        ------
        ValueError
            If matrix/vector dimensions or numerical values
            are invalid.

        RuntimeError
            If the linear system cannot be solved.
        """

        # -----------------------------------------------------
        # Validate matrix
        # -----------------------------------------------------

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

        if len(J.shape) != 2:
            raise ValueError(
                "Jacobian matrix must be two-dimensional."
            )

        rows, cols = J.shape

        if rows != cols:
            raise ValueError(
                "Jacobian matrix must be square: "
                f"received shape {J.shape}."
            )

        # -----------------------------------------------------
        # Validate RHS
        # -----------------------------------------------------

        if rhs is None:
            raise ValueError(
                "Right-hand-side vector cannot be None."
            )

        rhs = np.asarray(
            rhs,
            dtype=float,
        ).reshape(-1)

        if rhs.size != rows:
            raise ValueError(
                "Linear-system dimension mismatch: "
                f"Jacobian has dimension {rows}, "
                f"but RHS has dimension {rhs.size}."
            )

        if not np.all(
            np.isfinite(rhs)
        ):
            raise ValueError(
                "Right-hand-side vector contains "
                "NaN or infinite values."
            )

        # -----------------------------------------------------
        # Empty system
        # -----------------------------------------------------

        if rows == 0:
            return np.empty(
                0,
                dtype=float,
            )

        # -----------------------------------------------------
        # Convert matrix to a numerical representation.
        #
        # Dense conversion is intentional for the v1.0
        # reference implementation.
        #
        # The public interface remains compatible with
        # sparse/GPU implementations later.
        # -----------------------------------------------------

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

        if matrix.shape != (
            rows,
            cols,
        ):
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

        # -----------------------------------------------------
        # Explicit regularization
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
        # Solve
        # -----------------------------------------------------

        try:

            dx = np.linalg.solve(
                matrix,
                rhs,
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
        # Normalize result
        # -----------------------------------------------------

        dx = np.asarray(
            dx,
            dtype=float,
        ).reshape(-1)

        # -----------------------------------------------------
        # Validate solution
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

    def summary(self) -> dict:
        """
        Return solver configuration information.
        """

        return {
            "solver": "SparseLinearSolver",
            "regularization": float(
                self.regularization
            ),
            "backend": "numpy",
            "supports_sparse_input": True,
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
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
```
