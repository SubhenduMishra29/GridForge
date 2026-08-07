# core/analysis/line_flow.py

"""
GridForge Line Flow Calculation (v0.7)

Computes:
- Pij, Qij (from → to)
- Pji, Qji (to → from)
- Line losses

Uses π-model:
- Series admittance
- Shunt charging (B/2 each side)
"""

import numpy as np


class LineFlowCalculator:
    def __init__(self, network):
        self.network = network

        # --- REQUIRED CORE ATTRIBUTES ---
        if not hasattr(network, "per_unit"):
            raise ValueError("Network missing 'per_unit' system (required for v0.7)")

        if not hasattr(network, "bus_index"):
            raise ValueError("Network missing 'bus_index' mapping")

        self.pu = network.per_unit
        self.bus_index = network.bus_index

    # ------------------------------------------------------------------
    # MAIN ENTRY
    # ------------------------------------------------------------------

    def compute(self, Vm, Va):
        """
        Vm: voltage magnitudes (pu)
        Va: voltage angles (rad)

        Returns:
            list of dicts per line
        """
        results = []

        for line in self.network.lines:
            res = self._line_flow(line, Vm, Va)
            results.append(res)

        return results

    # ------------------------------------------------------------------
    # CORE FORMULATION
    # ------------------------------------------------------------------

    def _line_flow(self, line, Vm, Va):
        # --- BUS LOOKUP SAFETY ---
        try:
            i = self.bus_index[line.from_bus.id]
            j = self.bus_index[line.to_bus.id]
        except KeyError as e:
            raise ValueError(f"Bus index missing for line: {e}")

        Vi = Vm[i] * np.exp(1j * Va[i])
        Vj = Vm[j] * np.exp(1j * Va[j])

        # --- VALIDATE LINE DATA ---
        if not hasattr(line, "base_kv"):
            raise ValueError(f"Line {line} missing base_kv")

        # Series impedance
        z = complex(line.r_ohm, line.x_ohm)
        z_pu = self.pu.to_pu_impedance(z, line.base_kv)

        if abs(z_pu) == 0:
            raise ValueError(f"Zero impedance line detected: {line}")

        y = 1 / z_pu

        # Shunt charging
        b = getattr(line, "b_siemens", 0.0)
        b_pu = self.pu.to_pu_admittance(1j * b, line.base_kv)

        # --- CURRENT CALCULATIONS ---
        Iij = (Vi - Vj) * y + Vi * (b_pu / 2)
        Iji = (Vj - Vi) * y + Vj * (b_pu / 2)

        # --- POWER ---
        Sij = Vi * np.conj(Iij)
        Sji = Vj * np.conj(Iji)

        Pij, Qij = Sij.real, Sij.imag
        Pji, Qji = Sji.real, Sji.imag

        # --- LOSSES ---
        Ploss = Pij + Pji
        Qloss = Qij + Qji

        return {
            "from_bus": line.from_bus.id,
            "to_bus": line.to_bus.id,
            "P_from_to": Pij,
            "Q_from_to": Qij,
            "P_to_from": Pji,
            "Q_to_from": Qji,
            "P_loss": Ploss,
            "Q_loss": Qloss,
        }
