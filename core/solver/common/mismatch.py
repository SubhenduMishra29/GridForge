"""
core/solver/common/mismatch.py

=====================================================
POWER MISMATCH COMPUTATION (NEWTON-RAPHSON)
=====================================================

This module computes the power mismatch vector used
in Newton-Raphson power flow analysis.

Mismatch definition:

    ΔP = P_spec - P_calc
    ΔQ = Q_spec - Q_calc

-----------------------------------------------------
ROLE IN SOLVER PIPELINE
-----------------------------------------------------

At each NR iteration:

    1. Compute injected power (P_calc, Q_calc)
    2. Compute mismatch vector
    3. Solve:
            J * Δx = mismatch

-----------------------------------------------------
INPUTS
-----------------------------------------------------

network : Grid
    - Contains ordered list of buses

Ybus : numpy.ndarray (complex)
    - Bus admittance matrix (n x n)

-----------------------------------------------------
BUS REQUIREMENTS
-----------------------------------------------------

Each Bus must provide:

    bus.V          → voltage magnitude (p.u.)
    bus.theta      → voltage angle (radians)
    bus.P_spec     → specified active power
    bus.Q_spec     → specified reactive power

    bus.is_slack()
    bus.is_pq()

-----------------------------------------------------
MISMATCH STRUCTURE
-----------------------------------------------------

Vector layout:

    [ ΔP (non-slack buses),
      ΔQ (PQ buses only) ]

-----------------------------------------------------
BUS TYPE HANDLING
-----------------------------------------------------

| Bus Type | ΔP | ΔQ |
|----------|----|----|
| SLACK    | ❌ | ❌ |
| PV       | ✅ | ❌ |
| PQ       | ✅ | ✅ |

-----------------------------------------------------
NOTES
-----------------------------------------------------

- Uses O(n²) formulation (baseline correct)
- Optimizable later (vectorization / sparse)
- No solver logic here (pure math)

=====================================================
"""

import numpy as np


class PowerMismatch:
    """
    Computes power mismatch vector for Newton-Raphson.
    """

    def __init__(self, network, Ybus):
        """
        Parameters
        ----------
        network : Grid
        Ybus : numpy.ndarray (complex)
        """

        self.network = network
        self.Ybus = Ybus

        # IMPORTANT: bus order must match Ybus indexing
        self.buses = network.buses
        self.n = len(self.buses)

    # =====================================================
    # INTERNAL: POWER CALCULATION
    # =====================================================

    def _compute_power(self):
        """
        Compute injected active (P) and reactive (Q)
        power at each bus.

        Returns
        -------
        P : ndarray
        Q : ndarray

        Equations:

        P_i = Σ V_i V_j (G_ij cosθ_ij + B_ij sinθ_ij)
        Q_i = Σ V_i V_j (G_ij sinθ_ij - B_ij cosθ_ij)
        """

        # Voltage magnitudes
        V = np.array([bus.V for bus in self.buses])

        # Voltage angles
        theta = np.array([bus.theta for bus in self.buses])

        # Separate real and imaginary parts
        G = self.Ybus.real
        B = self.Ybus.imag

        # Initialize output
        P = np.zeros(self.n)
        Q = np.zeros(self.n)

        # Double summation
        for i in range(self.n):
            for j in range(self.n):

                angle = theta[i] - theta[j]

                # Active power
                P[i] += (
                    V[i] * V[j] *
                    (G[i, j] * np.cos(angle) +
                     B[i, j] * np.sin(angle))
                )

                # Reactive power
                Q[i] += (
                    V[i] * V[j] *
                    (G[i, j] * np.sin(angle) -
                     B[i, j] * np.cos(angle))
                )

        return P, Q

    # =====================================================
    # PUBLIC: MISMATCH VECTOR
    # =====================================================

    def compute(self):
        """
        Build mismatch vector for Newton-Raphson.

        Returns
        -------
        mismatch : ndarray

        Structure:
            [ΔP (non-slack),
             ΔQ (PQ only)]
        """

        # Step 1: Compute power injections
        P_calc, Q_calc = self._compute_power()

        dP = []
        dQ = []

        # Step 2: Form mismatch vector
        for i, bus in enumerate(self.buses):

            # Active mismatch (exclude slack)
            if not bus.is_slack():
                dP.append(bus.P_spec - P_calc[i])

            # Reactive mismatch (PQ only)
            if bus.is_pq():
                dQ.append(bus.Q_spec - Q_calc[i])

        # Step 3: Combine into single vector
        mismatch = np.array(dP + dQ)

        return mismatch
