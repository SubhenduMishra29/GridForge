import numpy as np

class DistanceRelay:
    def __init__(self, line_z, zone1=0.8, zone2=1.2, zone3=2.0):
        self.Z_line = line_z
        self.zone1 = zone1 * abs(line_z)
        self.zone2 = zone2 * abs(line_z)
        self.zone3 = zone3 * abs(line_z)

    def measure_impedance(self, V, I):
        if abs(I) < 1e-6:
            return np.inf
        return abs(V / I)

    def check_trip(self, V, I):
        Z = self.measure_impedance(V, I)

        if Z <= self.zone1:
            return "Zone-1 Trip"
        elif Z <= self.zone2:
            return "Zone-2 Trip"
        elif Z <= self.zone3:
            return "Zone-3 Trip"
        else:
            return "No Trip"
