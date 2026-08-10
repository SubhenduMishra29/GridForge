"""
GridForge Y-Bus Builder

Builds the network admittance matrix.

Responsibilities:
- Convert network topology into Ybus
- Stamp lines
- Stamp transformers
- Handle shunts and switched elements

Does NOT:
- Solve load flow
- Calculate faults
- Perform dynamics
"""

import numpy as np
from scipy.sparse import lil_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components


class YBusBuilder:

    def __init__(self, network):
        self.network = network
        self.bus_index = {}
        self.Ybus = None

    # =====================================================
    # BUS INDEX
    # =====================================================

    def build_bus_index(self):
        self.bus_index = {
            bus.id: idx
            for idx, bus in enumerate(self.network.buses)
        }

    # =====================================================
    # MAIN BUILD FUNCTION
    # =====================================================

    def build(self):

        self.build_bus_index()

        n = len(self.network.buses)

        Y = lil_matrix((n, n), dtype=complex)

        # -------------------------------
        # Lines
        # -------------------------------
        for line in getattr(self.network, "lines", []):
            self.stamp_line(Y, line)

        # -------------------------------
        # Transformers
        # -------------------------------
        for trafo in getattr(self.network, "transformers", []):
            self.stamp_transformer(Y, trafo)

        # -------------------------------
        # Bus Shunts
        # -------------------------------
        for bus in self.network.buses:
            idx = self.bus_index[bus.id]

            g = getattr(bus, "g_shunt", 0.0)
            b = getattr(bus, "b_shunt", 0.0)

            if g != 0.0 or b != 0.0:
                Y[idx, idx] += complex(g, b)

        # Convert to CSR
        self.Ybus = Y.tocsr()

        # Validation checks
        self._validate_dimensions()
        self._validate_symmetry()
        self._check_islands()

        # Store in network
        self.network.Ybus = self.Ybus

        return self.Ybus

    # =====================================================
    # LINE PI MODEL
    # =====================================================

    def stamp_line(self, Y, line):

        if not getattr(line, "in_service", True):
            return

        i = self.bus_index[line.from_bus.id]
        j = self.bus_index[line.to_bus.id]

        r = line.r_pu
        x = line.x_pu

        z = complex(r, x)

        if abs(z) < 1e-12:
            raise ValueError(f"Zero impedance line detected: {line}")

        y = 1 / z

        b = 1j * (getattr(line, "b_pu", 0.0) / 2)

        # Diagonal
        Y[i, i] += y + b
        Y[j, j] += y + b

        # Off-diagonal
        Y[i, j] -= y
        Y[j, i] -= y

    # =====================================================
    # TRANSFORMER MODEL
    # =====================================================

    def stamp_transformer(self, Y, trafo):

        if not getattr(trafo, "in_service", True):
            return

        i = self.bus_index[trafo.from_bus.id]
        j = self.bus_index[trafo.to_bus.id]

        r = trafo.r_pu
        x = trafo.x_pu

        z = complex(r, x)

        if abs(z) < 1e-12:
            raise ValueError(f"Zero impedance transformer: {trafo}")

        y = 1 / z

        # Tap ratio and phase shift
        tap = getattr(trafo, "tap_ratio", 1.0)
        shift_deg = getattr(trafo, "phase_shift_deg", 0.0)
        shift = np.deg2rad(shift_deg)

        a = tap * np.exp(1j * shift)

        # Shunt (magnetizing branch, optional)
        b_shunt = getattr(trafo, "b_shunt_pu", 0.0)

        # Diagonal
        Y[i, i] += y / (a * np.conj(a)) + 1j * b_shunt / 2
        Y[j, j] += y + 1j * b_shunt / 2

        # Off-diagonal
        Y[i, j] -= y / np.conj(a)
        Y[j, i] -= y / a

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_dimensions(self):
        n = len(self.network.buses)

        if self.Ybus.shape != (n, n):
            raise ValueError("Invalid Ybus dimension")

    def _validate_symmetry(self):

        Y_dense = self.Ybus.toarray()

        if not np.allclose(Y_dense, Y_dense.T.conj()):
            raise ValueError("Ybus is not symmetric")

    def _check_islands(self):

        n_components, _ = connected_components(self.Ybus)

        if n_components > 1:
            raise ValueError(f"Network has {n_components} disconnected islands")

    # =====================================================
    # DEBUG
    # =====================================================

    def summary(self):

        return {
            "buses": len(self.network.buses),
            "lines": len(getattr(self.network, "lines", [])),
            "transformers": len(getattr(self.network, "transformers", [])),
            "matrix_size": None if self.Ybus is None else self.Ybus.shape,
        }
