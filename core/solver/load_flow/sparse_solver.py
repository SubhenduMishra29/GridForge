"""
GridForge Sparse Linear Solver

Handles Newton-Raphson linear equation:

J Δx = mismatch

"""

import numpy as np


try:

    from scipy.sparse import csr_matrix

    from scipy.sparse.linalg import spsolve

    SCIPY_AVAILABLE = True


except ImportError:

    SCIPY_AVAILABLE = False



class SparseLinearSolver:


    def solve(
            self,
            J,
            mismatch):


        if SCIPY_AVAILABLE:


            J_sparse = csr_matrix(J)


            return spsolve(

                J_sparse,

                mismatch

            )


        else:


            # fallback for small systems

            return np.linalg.solve(

                J,

                mismatch

            )
