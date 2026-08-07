# core/analysis/load_flow.py

"""
GridForge Load Flow Solver (v0.7)

Newton-Raphson based power flow solver.

Outputs:
- Vm (voltage magnitudes, pu)
- Va (voltage angles, radians)
"""

import numpy as np


class LoadFlowSolver:
    def __init__(self, network):
        self.network = network

        # --- VALIDATION ---
        if not hasattr(network, "buses"):
            raise ValueError("Network missing buses")

        if not hasattr(network, "lines"):
            raise ValueError("Network missing lines")

        if not hasattr(network, "bus_index"):
            raise ValueError("Network missing bus_index")

        if not hasattr(network, "per_unit"):
            raise ValueError("Network missing per_unit system")

        self.buses = network.buses
        self.lines = network.lines
        self.bus_index = network.bus_index
        self.n = len(self.buses)

        # Build Ybus
        self.Ybus = self._build_ybus()

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def solve(self, max_iter=20, tol=1e-6):
        Vm = np.array([bus.Vm for bus in self.buses])
        Va = np.array([bus.Va for bus in self.buses])

        for _ in range(max_iter):
            P, Q = self._calc_power(Vm, Va)
            mismatch = self._mismatch(P, Q)

            if np.max(np.abs(mismatch)) < tol:
                return Vm, Va

            J = self._jacobian(Vm, Va)
            dx = np.linalg.solve(J, mismatch)

            Va += dx[:self.n]
            Vm += dx[self.n:]

        raise RuntimeError("Load flow did not converge")

    # ------------------------------------------------------------------
    # YBUS
    # ------------------------------------------------------------------

    def _build_ybus(self):
        Y = np.zeros((self.n, self.n), dtype=complex)

        for line in self.lines:
            i = self.bus_index[line.from_bus.id]
            j = self.bus_index[line.to_bus.id]

            z = complex(line.r_ohm, line.x_ohm)
            z_pu = self.network.per_unit.to_pu_impedance(z, line.base_kv)

            if abs(z_pu) == 0:
                raise ValueError(f"Zero impedance in line {line}")

            y = 1 / z_pu

            Y[i, i] += y
            Y[j, j] += y
            Y[i, j] -= y
            Y[j, i] -= y

        return Y

    # ------------------------------------------------------------------
    # POWER CALCULATION
    # ------------------------------------------------------------------

    def _calc_power(self, Vm, Va):
        P = np.zeros(self.n)
        Q = np.zeros(self.n)

        for i in range(self.n):
            for j in range(self.n):
                Yij = self.Ybus[i, j]
                angle = Va[i] - Va[j]

                P[i] += Vm[i] * Vm[j] * (
                    Yij.real * np.cos(angle) +
                    Yij.imag * np.sin(angle)
                )

                Q[i] += Vm[i] * Vm[j] * (
                    Yij.real * np.sin(angle) -
                    Yij.imag * np.cos(angle)
                )

        return P, Q

    # ------------------------------------------------------------------
    # MISMATCH
    # ------------------------------------------------------------------

    def _mismatch(self, P_calc, Q_calc):
        mismatch = []

        for i, bus in enumerate(self.buses):
            if bus.type == "Slack":
                continue

            dP = bus.P - P_calc[i]
            mismatch.append(dP)

            if bus.type == "PQ":
                dQ = bus.Q - Q_calc[i]
                mismatch.append(dQ)

        return np.array(mismatch)

    # ------------------------------------------------------------------
    # JACOBIAN (SIMPLIFIED)
    # ------------------------------------------------------------------

    def _jacobian(self, Vm, Va):
        size = 2 * self.n
        return np.eye(size)
