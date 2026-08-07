# core/network/ybus.py

import numpy as np


class YBusBuilder:
    """
    Builds the bus admittance matrix (Y-bus)

    Supports:
    - Lines (pi model)
    - Transformers (tap ratio)
    - Shunt elements
    """

    def __init__(self, buses):
        """
        buses: list of bus objects with unique IDs
        """
        self.buses = buses
        self.n = len(buses)
        self.bus_index = {bus.id: idx for idx, bus in enumerate(buses)}

        self.Y = np.zeros((self.n, self.n), dtype=complex)

    # ---------------------------------------------------------
    # ADD LINE (π MODEL)
    # ---------------------------------------------------------
    def add_line(self, line):
        i = self.bus_index[line.from_bus]
        j = self.bus_index[line.to_bus]

        z = complex(line.r_pu, line.x_pu)

        if z == 0:
            raise ValueError("Line impedance cannot be zero")

        y = 1 / z

        b_shunt = complex(0, line.b_pu / 2)  # half on each side

        # Off-diagonal
        self.Y[i, j] -= y
        self.Y[j, i] -= y

        # Diagonal
        self.Y[i, i] += y + b_shunt
        self.Y[j, j] += y + b_shunt

    # ---------------------------------------------------------
    # ADD TRANSFORMER
    # ---------------------------------------------------------
    def add_transformer(self, trafo):
        i = self.bus_index[trafo.from_bus]
        j = self.bus_index[trafo.to_bus]

        z = complex(trafo.r_pu, trafo.x_pu)

        if z == 0:
            raise ValueError("Transformer impedance cannot be zero")

        y = 1 / z

        tap = trafo.tap_ratio if hasattr(trafo, "tap_ratio") else 1.0

        # Off-diagonal
        self.Y[i, j] -= y / tap
        self.Y[j, i] -= y / tap

        # Diagonal
        self.Y[i, i] += y / (tap ** 2)
        self.Y[j, j] += y

    # ---------------------------------------------------------
    # ADD SHUNT
    # ---------------------------------------------------------
    def add_shunt(self, shunt):
        i = self.bus_index[shunt.bus]
        self.Y[i, i] += shunt.y_pu

    # ---------------------------------------------------------
    # BUILD COMPLETE MATRIX
    # ---------------------------------------------------------
    def build(self, lines=None, transformers=None, shunts=None):
        if lines:
            for line in lines:
                self.add_line(line)

        if transformers:
            for trafo in transformers:
                self.add_transformer(trafo)

        if shunts:
            for shunt in shunts:
                self.add_shunt(shunt)

        return self.Y

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    def print_matrix(self):
        print("Y-Bus Matrix:")
        print(self.Y)
