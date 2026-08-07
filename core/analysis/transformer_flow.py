# core/analysis/transformer_flow.py

"""
GridForge Transformer Flow Calculation

Supports:
- Off-nominal tap ratio
- Phase shifting transformers
- Complex tap handling

Model:
    a = tap * exp(jθ)

    Iij = (Vi/a - Vj) * y
    Iji = (Vj - Vi/a*) * y
"""

import numpy as np


class TransformerFlowCalculator:
    def __init__(self, network):
        self.network = network
        self.bus_index = network.bus_index

    # ------------------------------------------------------------------
    # MAIN ENTRY
    # ------------------------------------------------------------------

    def compute(self, Vm, Va):
        results = []

        for trafo in self.network.transformers:
            res = self._flow(trafo, Vm, Va)
            results.append(res)

        return results

    # ------------------------------------------------------------------
    # CORE FORMULATION
    # ------------------------------------------------------------------

    def _flow(self, trafo, Vm, Va):
        i = self.bus_index[trafo.from_bus.id]
        j = self.bus_index[trafo.to_bus.id]

        Vi = Vm[i] * np.exp(1j * Va[i])
        Vj = Vm[j] * np.exp(1j * Va[j])

        # Transformer impedance (already in pu)
        z = complex(trafo.r_pu, trafo.x_pu)
        y = 1 / z

        # Tap + phase shift
        tap = getattr(trafo, "tap_ratio", 1.0)
        shift_deg = getattr(trafo, "phase_shift_deg", 0.0)
        shift_rad = np.deg2rad(shift_deg)

        a = tap * np.exp(1j * shift_rad)

        # Currents
        Iij = (Vi / a - Vj) * y
        Iji = (Vj - Vi / np.conj(a)) * y

        # Powers
        Sij = Vi * np.conj(Iij)
        Sji = Vj * np.conj(Iji)

        Pij, Qij = Sij.real, Sij.imag
        Pji, Qji = Sji.real, Sji.imag

        # Losses
        Ploss = Pij + Pji
        Qloss = Qij + Qji

        return {
            "from_bus": trafo.from_bus.id,
            "to_bus": trafo.to_bus.id,
            "tap_ratio": tap,
            "phase_shift_deg": shift_deg,
            "P_from_to": Pij,
            "Q_from_to": Qij,
            "P_to_from": Pji,
            "Q_to_from": Qji,
            "P_loss": Ploss,
            "Q_loss": Qloss
        }
