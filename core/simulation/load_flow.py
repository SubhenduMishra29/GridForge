# core/simulation/load_flow.py

import numpy as np


class LoadFlowSolver:
    def __init__(self, buses, Ybus, tolerance=1e-6, max_iter=20):
        self.buses = buses
        self.Ybus = Ybus
        self.n = len(buses)

        self.tol = tolerance
        self.max_iter = max_iter

        self.bus_index = {bus.id: i for i, bus in enumerate(buses)}

        # State variables
        self.V = np.array([bus.V for bus in buses])
        self.theta = np.array([bus.theta for bus in buses])

    # ---------------------------------------------------------
    # POWER CALCULATION
    # ---------------------------------------------------------
    def calc_power(self):
        P = np.zeros(self.n)
        Q = np.zeros(self.n)

        for i in range(self.n):
            for j in range(self.n):
                Yij = self.Ybus[i, j]
                Vi, Vj = self.V[i], self.V[j]
                theta_ij = self.theta[i] - self.theta[j]

                G = Yij.real
                B = Yij.imag

                P[i] += Vi * Vj * (G * np.cos(theta_ij) + B * np.sin(theta_ij))
                Q[i] += Vi * Vj * (G * np.sin(theta_ij) - B * np.cos(theta_ij))

        return P, Q

    # ---------------------------------------------------------
    # MISMATCH VECTOR
    # ---------------------------------------------------------
    def mismatch(self):
        P_calc, Q_calc = self.calc_power()

        dP = []
        dQ = []

        for i, bus in enumerate(self.buses):
            if bus.type != "SLACK":
                dP.append(bus.P - P_calc[i])

            if bus.type == "PQ":
                dQ.append(bus.Q - Q_calc[i])

        return np.array(dP + dQ)

    # ---------------------------------------------------------
    # JACOBIAN MATRIX
    # ---------------------------------------------------------
    def build_jacobian(self):
        n = self.n
        J1 = np.zeros((n, n))
        J2 = np.zeros((n, n))
        J3 = np.zeros((n, n))
        J4 = np.zeros((n, n))

        P, Q = self.calc_power()

        for i in range(n):
            for j in range(n):
                Yij = self.Ybus[i, j]
                G = Yij.real
                B = Yij.imag

                if i == j:
                    J1[i, i] = -Q[i] - (self.V[i] ** 2) * B
                    J2[i, i] = P[i] / self.V[i] + self.V[i] * G
                    J3[i, i] = P[i] - (self.V[i] ** 2) * G
                    J4[i, i] = Q[i] / self.V[i] - self.V[i] * B
                else:
                    theta_ij = self.theta[i] - self.theta[j]

                    J1[i, j] = self.V[i] * self.V[j] * (G * np.sin(theta_ij) - B * np.cos(theta_ij))
                    J2[i, j] = self.V[i] * (G * np.cos(theta_ij) + B * np.sin(theta_ij))
                    J3[i, j] = -self.V[i] * self.V[j] * (G * np.cos(theta_ij) + B * np.sin(theta_ij))
                    J4[i, j] = self.V[i] * (G * np.sin(theta_ij) - B * np.cos(theta_ij))

        return J1, J2, J3, J4

    # ---------------------------------------------------------
    # REDUCED JACOBIAN (REMOVE SLACK/PV CONSTRAINTS)
    # ---------------------------------------------------------
    def reduced_jacobian(self, J1, J2, J3, J4):
        pv_pq = [i for i, b in enumerate(self.buses) if b.type != "SLACK"]
        pq = [i for i, b in enumerate(self.buses) if b.type == "PQ"]

        J11 = J1[np.ix_(pv_pq, pv_pq)]
        J12 = J2[np.ix_(pv_pq, pq)]
        J21 = J3[np.ix_(pq, pv_pq)]
        J22 = J4[np.ix_(pq, pq)]

        top = np.hstack((J11, J12))
        bottom = np.hstack((J21, J22))

        return np.vstack((top, bottom)), pv_pq, pq

    # ---------------------------------------------------------
    # SOLVE
    # ---------------------------------------------------------
    def solve(self):
        for iteration in range(self.max_iter):

            mismatch = self.mismatch()

            if np.max(np.abs(mismatch)) < self.tol:
                print(f"Converged in {iteration} iterations")
                return self.V, self.theta

            J1, J2, J3, J4 = self.build_jacobian()
            J, pv_pq, pq = self.reduced_jacobian(J1, J2, J3, J4)

            dx = np.linalg.solve(J, mismatch)

            # Update state
            for idx, bus_i in enumerate(pv_pq):
                self.theta[bus_i] += dx[idx]

            for idx, bus_i in enumerate(pq):
                self.V[bus_i] += dx[len(pv_pq) + idx]

        raise RuntimeError("Load flow did not converge")
