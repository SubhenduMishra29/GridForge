import numpy as np


class UnbalancedFaultAnalyzer:
    def __init__(self, network):
        self.network = network

    # ------------------------------------------------------------
    # MAIN ENTRY
    # ------------------------------------------------------------

    def run(self, fault_type="SLG", Zf=0.0):
        from core.analysis.sequence_network import SequenceNetworkBuilder

        builder = SequenceNetworkBuilder(self.network)
        Y1, Y2, Y0 = builder.build()

        Z1 = np.linalg.inv(Y1)
        Z2 = np.linalg.inv(Y2)
        Z0 = np.linalg.inv(Y0)

        results = []

        for bus in self.network.buses:
            k = self.network.bus_index[bus.id]

            res = self._fault_at_bus(k, fault_type, Z1, Z2, Z0, Zf)

            results.append({
                "bus": bus.id,
                **res
            })

        return results

    # ------------------------------------------------------------
    # FAULT CALCULATION
    # ------------------------------------------------------------

    def _fault_at_bus(self, k, fault_type, Z1, Z2, Z0, Zf):
        V = 1.0 + 0j

        Z1k = Z1[k, k]
        Z2k = Z2[k, k]
        Z0k = Z0[k, k]

        if fault_type == "SLG":
            If = 3 * V / (Z1k + Z2k + Z0k + 3 * Zf)

        elif fault_type == "LL":
            If = np.sqrt(3) * V / (Z1k + Z2k + Zf)

        elif fault_type == "DLG":
            Z_eq = Z2k * Z0k / (Z2k + Z0k)
            If = 3 * V / (Z1k + Z_eq + 3 * Zf)

        else:
            raise ValueError("Unsupported fault type")

        return {
            "fault_type": fault_type,
            "Ik_mag": abs(If),
            "Ik_angle_deg": np.angle(If, deg=True)
        }
