import numpy as np


class SequenceNetworkBuilder:
    def __init__(self, network):
        self.network = network

    # ------------------------------------------------------------
    # BUILD SEQUENCE NETWORKS
    # ------------------------------------------------------------

    def build(self):
        Y1 = self._build_positive_sequence()
        Y2 = self._build_negative_sequence()
        Y0 = self._build_zero_sequence()

        return Y1, Y2, Y0

    # ------------------------------------------------------------
    # POSITIVE SEQUENCE
    # ------------------------------------------------------------

    def _build_positive_sequence(self):
        return self.network.Ybus.copy()

    # ------------------------------------------------------------
    # NEGATIVE SEQUENCE
    # ------------------------------------------------------------

    def _build_negative_sequence(self):
        # Usually same as positive (no controls)
        return self.network.Ybus.copy()

    # ------------------------------------------------------------
    # ZERO SEQUENCE
    # ------------------------------------------------------------

    def _build_zero_sequence(self):
        n = len(self.network.buses)
        Y0 = np.zeros((n, n), dtype=complex)

        # Lines (need zero-sequence impedance)
        for line in self.network.lines:
            i = self.network.bus_index[line.from_bus.id]
            j = self.network.bus_index[line.to_bus.id]

            z0 = complex(line.r0_pu, line.x0_pu)
            y0 = 1 / z0

            Y0[i, i] += y0
            Y0[j, j] += y0
            Y0[i, j] -= y0
            Y0[j, i] -= y0

        # Transformers (grounding matters)
        for trafo in self.network.transformers:
            if not getattr(trafo, "zero_seq_enabled", False):
                continue

            i = self.network.bus_index[trafo.from_bus.id]
            j = self.network.bus_index[trafo.to_bus.id]

            z0 = complex(trafo.r0_pu, trafo.x0_pu)
            y0 = 1 / z0

            Y0[i, i] += y0
            Y0[j, j] += y0
            Y0[i, j] -= y0
            Y0[j, i] -= y0

        return Y0
