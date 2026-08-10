"""
GridForge Sparse Linear Solver

Solves Newton-Raphson system:

    J Δx = mismatch

Supports:
- Sparse solve (SciPy)
- Dense fallback
- Numerical safeguards
"""

import numpy as np

try:
    from scipy.sparse import csr_matrix
    from scipy.sparse.linalg import spsolve

    SCIPY_AVAILABLE = True

except ImportError:
    SCIPY_AVAILABLE = False


class SparseLinearSolver:

    def __init__(self, regularization=0.0):
        """
        Parameters
        ----------
        regularization : float
            Small diagonal value added to improve stability
            (e.g. 1e-8 for ill-conditioned systems)
        """
        self.regularization = regularization

    # =====================================================
    # SOLVE
    # =====================================================

    def solve(self, J, mismatch):

        J = np.asarray(J)
        mismatch = np.asarray(mismatch)

        # ---------------------------------
        # Optional regularization
        # ---------------------------------

        if self.regularization > 0:
            J = J + self.regularization * np.eye(J.shape[0])

        # ---------------------------------
        # Sparse solve (preferred)
        # ---------------------------------

        if SCIPY_AVAILABLE:
            try:
                J_sparse = csr_matrix(J)

                dx = spsolve(J_sparse, mismatch)

                # sanity check
                if np.any(np.isnan(dx)) or np.any(np.isinf(dx)):
                    raise ValueError("Sparse solver returned invalid values")

                return dx

            except Exception as e:
                # fallback to dense
                return self._dense_solve(J, mismatch, error=e)

        # ---------------------------------
        # Dense fallback
        # ---------------------------------

        return self._dense_solve(J, mismatch)

    # =====================================================
    # DENSE SOLVER
    # =====================================================

    def _dense_solve(self, J, mismatch, error=None):

        try:
            return np.linalg.solve(J, mismatch)

        except np.linalg.LinAlgError as e:

            raise RuntimeError(
                "Linear solve failed (Jacobian likely singular or ill-conditioned)"
            ) from e if error is None else error
