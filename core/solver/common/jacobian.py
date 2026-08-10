import numpy as np

from core.solver.common.mismatch import PowerMismatch


class JacobianBuilder:

    def __init__(self, network):
        self.network = network

    # =====================================================
    # BUILD JACOBIAN
    # =====================================================

    def build(self):

        buses = self.network.buses
        Ybus = self.network.Ybus

        n = len(buses)

        V = np.array([bus.V for bus in buses])
        theta = np.array([bus.theta for bus in buses])

        G = Ybus.real
        B = Ybus.imag

        # ---------------------------------------------
        # State indexing
        # ---------------------------------------------

        pvpq = [i for i, bus in enumerate(buses) if not bus.is_slack()]
        pq = [i for i, bus in enumerate(buses) if bus.is_pq()]

        npv = len(pvpq)
        npq = len(pq)

        J1 = np.zeros((npv, npv))
        J2 = np.zeros((npv, npq))
        J3 = np.zeros((npq, npv))
        J4 = np.zeros((npq, npq))

        # ---------------------------------------------
        # PRECOMPUTE POWER (CRITICAL FIX)
        # ---------------------------------------------

        mismatch = PowerMismatch(self.network, Ybus)
        P, Q = mismatch._compute_power()

        # ---------------------------------------------
        # J1 = dP/dθ
        # ---------------------------------------------

        for ii, i in enumerate(pvpq):
            for jj, j in enumerate(pvpq):

                if i == j:
                    J1[ii, jj] = -Q[i] - B[i, i] * V[i]**2
                else:
                    angle = theta[i] - theta[j]
                    J1[ii, jj] = V[i] * V[j] * (
                        G[i, j] * np.sin(angle)
                        - B[i, j] * np.cos(angle)
                    )

        # ---------------------------------------------
        # J2 = dP/dV
        # ---------------------------------------------

        for ii, i in enumerate(pvpq):
            for jj, j in enumerate(pq):

                if i == j:
                    J2[ii, jj] = P[i] / V[i] + G[i, i] * V[i]
                else:
                    angle = theta[i] - theta[j]
                    J2[ii, jj] = V[i] * (
                        G[i, j] * np.cos(angle)
                        + B[i, j] * np.sin(angle)
                    )

        # ---------------------------------------------
        # J3 = dQ/dθ
        # ---------------------------------------------

        for ii, i in enumerate(pq):
            for jj, j in enumerate(pvpq):

                if i == j:
                    J3[ii, jj] = P[i] - G[i, i] * V[i]**2
                else:
                    angle = theta[i] - theta[j]
                    J3[ii, jj] = -V[i] * V[j] * (
                        G[i, j] * np.cos(angle)
                        + B[i, j] * np.sin(angle)
                    )

        # ---------------------------------------------
        # J4 = dQ/dV
        # ---------------------------------------------

        for ii, i in enumerate(pq):
            for jj, j in enumerate(pq):

                if i == j:
                    J4[ii, jj] = Q[i] / V[i] - B[i, i] * V[i]
                else:
                    angle = theta[i] - theta[j]
                    J4[ii, jj] = V[i] * (
                        G[i, j] * np.sin(angle)
                        - B[i, j] * np.cos(angle)
                    )

        # ---------------------------------------------
        # FINAL ASSEMBLY
        # ---------------------------------------------

        J = np.block([
            [J1, J2],
            [J3, J4]
        ])

        return J
