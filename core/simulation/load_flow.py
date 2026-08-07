# core/simulation/load_flow.py

"""
GridForge Load Flow Solver (Newton-Raphson)

Features:
- Slack / PV / PQ bus handling
- Full Jacobian formulation
- Per-unit system compatible
- Deterministic convergence control

Output:
- Voltage magnitude (pu)
- Voltage angle (rad)
"""

import numpy as np
from core.network.ybus import YBusBuilder


class LoadFlowSolver:
    def __init__(self, network):
        self.network = network
        self.pu = network.per_unit

        self.Ybus, self.bus_index = YBusBuilder(network).build()
        self.n = len(self.bus_index)

    # ------------------------------------------------------------------
    # MAIN SOLVER
    # ------------------------------------------------------------------

    def solve(self, tol=1e-6, max_iter=20):
        buses = self.network.buses

        # --- Initialize arrays ---
        V = np.ones(self.n)           # Voltage magnitude
        theta = np.zeros(self.n)      # Voltage angle (rad)

        P_spec = np.zeros(self.n)
        Q_spec = np.zeros(self.n)

        bus_type = []

        # --- Load bus data ---
        for bus in buses:
            i = self.bus_index[bus.id]

            bus_type.append(bus.type.lower())

            # Power injections (generation - load)
            P, Q = bus.p_mw, bus.q_mvar
            S_pu = self.pu.to_pu_power(P, Q)

            P_spec[i] = S_pu.real
            Q_spec[i] = S_pu.imag

            # Initial voltage
            if hasattr(bus, "v_pu"):
                V[i] = bus.v_pu

            if hasattr(bus, "angle_deg"):
                theta[i] = np.deg2rad(bus.angle_deg)

        bus_type = np.array(bus_type)

        # --- Identify bus sets ---
        slack = np.where(bus_type == "slack")[0]
        pv = np.where(bus_type == "pv")[0]
        pq = np.where(bus_type == "pq")[0]

        if len(slack) != 1:
            raise ValueError("Exactly one slack bus required")

        # State variables:
        # Angles for all except slack
        # Voltages only for PQ
        pv_pq = np.concatenate((pv, pq))
        state_theta_idx = np.delete(np.arange(self.n), slack)
        state_V_idx = pq

        # ------------------------------------------------------------------
        # ITERATION LOOP
        # ------------------------------------------------------------------

        for iteration in range(max_iter):

            # --- Compute P, Q from current V ---
            P_calc = np.zeros(self.n)
            Q_calc = np.zeros(self.n)

            for i in range(self.n):
                for k in range(self.n):
                    Vi = V[i]
                    Vk = V[k]
                    G = self.Ybus[i, k].real
                    B = self.Ybus[i, k].imag

                    angle = theta[i] - theta[k]

                    P_calc[i] += Vi * Vk * (G * np.cos(angle) + B * np.sin(angle))
                    Q_calc[i] += Vi * Vk * (G * np.sin(angle) - B * np.cos(angle))

            # --- Mismatch ---
            dP = P_spec - P_calc
            dQ = Q_spec - Q_calc

            # Remove slack P mismatch
            dP = np.delete(dP, slack)

            # Only PQ buses have Q mismatch
            dQ = dQ[pq]

            mismatch = np.concatenate([dP, dQ])

            # --- Convergence check ---
            if np.max(np.abs(mismatch)) < tol:
                print(f"Converged in {iteration} iterations")
                return self._build_result(V, theta)

            # ------------------------------------------------------------------
            # JACOBIAN BUILD
            # ------------------------------------------------------------------

            J11 = self._dP_dTheta(V, theta)
            J12 = self._dP_dV(V, theta)
            J21 = self._dQ_dTheta(V, theta)
            J22 = self._dQ_dV(V, theta)

            # Reduce matrices
            J11 = np.delete(J11, slack, axis=0)
            J11 = np.delete(J11, slack, axis=1)

            J12 = np.delete(J12, slack, axis=0)
            J12 = J12[:, pq]

            J21 = J21[pq, :]
            J21 = np.delete(J21, slack, axis=1)

            J22 = J22[pq, :]
            J22 = J22[:, pq]

            # Full Jacobian
            J = np.block([
                [J11, J12],
                [J21, J22]
            ])

            # --- Solve ---
            dx = np.linalg.solve(J, mismatch)

            # --- Update states ---
            dTheta = dx[:len(state_theta_idx)]
            dV = dx[len(state_theta_idx):]

            theta[state_theta_idx] += dTheta
            V[state_V_idx] += dV

        raise RuntimeError("Load flow did not converge")

    # ------------------------------------------------------------------
    # JACOBIAN SUBMATRICES
    # ------------------------------------------------------------------

    def _dP_dTheta(self, V, theta):
        n = self.n
        J = np.zeros((n, n))

        for i in range(n):
            for k in range(n):
                if i == k:
                    for m in range(n):
                        if m == i:
                            continue
                        G = self.Ybus[i, m].real
                        B = self.Ybus[i, m].imag
                        angle = theta[i] - theta[m]
                        J[i, i] += V[i] * V[m] * (-G * np.sin(angle) + B * np.cos(angle))
                else:
                    G = self.Ybus[i, k].real
                    B = self.Ybus[i, k].imag
                    angle = theta[i] - theta[k]
                    J[i, k] = V[i] * V[k] * (G * np.sin(angle) - B * np.cos(angle))
        return J

    def _dP_dV(self, V, theta):
        n = self.n
        J = np.zeros((n, n))

        for i in range(n):
            for k in range(n):
                G = self.Ybus[i, k].real
                B = self.Ybus[i, k].imag
                angle = theta[i] - theta[k]

                if i == k:
                    for m in range(n):
                        Gm = self.Ybus[i, m].real
                        Bm = self.Ybus[i, m].imag
                        ang = theta[i] - theta[m]
                        J[i, i] += V[m] * (Gm * np.cos(ang) + Bm * np.sin(ang))
                else:
                    J[i, k] = V[i] * (G * np.cos(angle) + B * np.sin(angle))
        return J

    def _dQ_dTheta(self, V, theta):
        n = self.n
        J = np.zeros((n, n))

        for i in range(n):
            for k in range(n):
                if i == k:
                    for m in range(n):
                        if m == i:
                            continue
                        G = self.Ybus[i, m].real
                        B = self.Ybus[i, m].imag
                        angle = theta[i] - theta[m]
                        J[i, i] += V[i] * V[m] * (G * np.cos(angle) + B * np.sin(angle))
                else:
                    G = self.Ybus[i, k].real
                    B = self.Ybus[i, k].imag
                    angle = theta[i] - theta[k]
                    J[i, k] = -V[i] * V[k] * (G * np.cos(angle) + B * np.sin(angle))
        return J

    def _dQ_dV(self, V, theta):
        n = self.n
        J = np.zeros((n, n))

        for i in range(n):
            for k in range(n):
                G = self.Ybus[i, k].real
                B = self.Ybus[i, k].imag
                angle = theta[i] - theta[k]

                if i == k:
                    for m in range(n):
                        Gm = self.Ybus[i, m].real
                        Bm = self.Ybus[i, m].imag
                        ang = theta[i] - theta[m]
                        J[i, i] += V[m] * (Gm * np.sin(ang) - Bm * np.cos(ang))
                else:
                    J[i, k] = V[i] * (G * np.sin(angle) - B * np.cos(angle))
        return J

    # ------------------------------------------------------------------
    # RESULT BUILDER
    # ------------------------------------------------------------------

    def _build_result(self, V, theta):
        result = []

        for bus in self.network.buses:
            i = self.bus_index[bus.id]

            result.append({
                "bus_id": bus.id,
                "V_pu": V[i],
                "angle_deg": np.rad2deg(theta[i])
            })

        return result
