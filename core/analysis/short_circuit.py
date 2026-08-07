# core/analysis/short_circuit.py

"""
GridForge Short Circuit Analysis

Balanced 3-phase fault using Zbus method
"""

import numpy as np


class ShortCircuitAnalyzer:
    def __init__(self, network):
        self.network = network

    # ------------------------------------------------------------------
    # MAIN ENTRY
    # ------------------------------------------------------------------

    def run_three_phase_faults(self):
        """
        Run 3-phase faults at all buses
        """
        Ybus = self.network.Ybus
        Zbus = np.linalg.inv(Ybus)

        results = []

        for bus in self.network.buses:
            k = self.network.bus_index[bus.id]

            fault = self._fault_at_bus(k, Zbus)

            results.append({
                "bus": bus.id,
                **fault
            })

        return results

    # ------------------------------------------------------------------
    # SINGLE BUS FAULT
    # ------------------------------------------------------------------

    def _fault_at_bus(self, k, Zbus):
        Zkk = Zbus[k, k]

        # Prefault voltage (assumed 1.0 ∠0)
        Vk = 1.0 + 0j

        # Fault current
        If = Vk / Zkk

        # Post-fault voltages
        V_post = -Zbus[:, k] * If

        return {
            "Ik_mag": abs(If),
            "Ik_angle_deg": np.angle(If, deg=True),
            "Z_th": Zkk,
            "voltages_post_fault": V_post
        }
