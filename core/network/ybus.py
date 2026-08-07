# core/network/ybus.py

"""
GridForge Y-Bus Builder (Industrial Grade)

Features:
- Multi-voltage per-unit system
- Line π-model (R + jX, B/2 charging)
- Transformer model (tap ratio + phase shift)
- Shunt elements
- Sparse-ready structure

Output:
- Ybus (complex NxN matrix)
- bus_index_map
"""

import numpy as np


class YBusBuilder:
    def __init__(self, network):
        self.network = network
        self.pu = network.per_unit  # PerUnitSystem instance

    # ------------------------------------------------------------------
    # PUBLIC ENTRY
    # ------------------------------------------------------------------

    def build(self):
        """
        Constructs the Y-bus matrix
        """
        buses = self.network.buses
        n = len(buses)

        if n == 0:
            raise ValueError("No buses in network")

        # Map bus_id → index
        bus_index = {bus.id: i for i, bus in enumerate(buses)}

        # Initialize Ybus
        Y = np.zeros((n, n), dtype=complex)

        # Stamp elements
        self._stamp_lines(Y, bus_index)
        self._stamp_transformers(Y, bus_index)
        self._stamp_shunts(Y, bus_index)

        return Y, bus_index

    # ------------------------------------------------------------------
    # LINE STAMPING (π MODEL)
    # ------------------------------------------------------------------

    def _stamp_lines(self, Y, bus_index):
        for line in self.network.lines:

            i = bus_index[line.from_bus.id]
            j = bus_index[line.to_bus.id]

            kv = line.base_kv

            # Convert impedance to PU
            z = complex(line.r_ohm, line.x_ohm)
            z_pu = self.pu.to_pu_impedance(z, kv)

            if z_pu == 0:
                continue  # avoid division by zero

            y = 1 / z_pu

            # Line charging (B/2 at each end)
            b = getattr(line, "b_siemens", 0.0)
            b_pu = self.pu.to_pu_admittance(1j * b, kv)

            # Off-diagonal
            Y[i, j] -= y
            Y[j, i] -= y

            # Diagonal
            Y[i, i] += y + b_pu / 2
            Y[j, j] += y + b_pu / 2

    # ------------------------------------------------------------------
    # TRANSFORMER STAMPING
    # ------------------------------------------------------------------

    def _stamp_transformers(self, Y, bus_index):
        for trafo in self.network.transformers:

            i = bus_index[trafo.from_bus.id]
            j = bus_index[trafo.to_bus.id]

            # Transformer parameters
            z_pu = complex(trafo.r_pu, trafo.x_pu)

            if z_pu == 0:
                continue

            y = 1 / z_pu

            # Tap ratio (magnitude)
            tap = getattr(trafo, "tap_ratio", 1.0)

            # Phase shift (degrees → radians)
            shift_deg = getattr(trafo, "phase_shift_deg", 0.0)
            shift_rad = np.deg2rad(shift_deg)

            # Complex tap
            a = tap * np.exp(1j * shift_rad)

            # Admittance stamping with tap
            Y[i, i] += y / (a * np.conj(a))
            Y[j, j] += y

            Y[i, j] -= y / np.conj(a)
            Y[j, i] -= y / a

    # ------------------------------------------------------------------
    # SHUNT STAMPING
    # ------------------------------------------------------------------

    def _stamp_shunts(self, Y, bus_index):
        for shunt in self.network.shunts:

            i = bus_index[shunt.bus.id]

            kv = shunt.base_kv

            y = complex(shunt.g_siemens, shunt.b_siemens)
            y_pu = self.pu.to_pu_admittance(y, kv)

            Y[i, i] += y_pu
