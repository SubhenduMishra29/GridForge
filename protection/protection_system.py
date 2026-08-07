from protection.distance_relay import DistanceRelay
from protection.overcurrent_relay import OvercurrentRelay

class ProtectionSystem:
    def __init__(self, network):
        self.network = network
        self.relays = {}

        for line in network.lines:
            i, j, Z = line
            self.relays[(i, j)] = {
                "distance": DistanceRelay(Z),
                "overcurrent": OvercurrentRelay(pickup=2.0)
            }

    def evaluate_fault(self, V, I_line):
        results = {}

        for (i, j), relay in self.relays.items():
            I = abs(I_line.get((i, j), 0))
            V_bus = abs(V[i])

            results[(i, j)] = {
                "Distance": relay["distance"].check_trip(V_bus, I),
                "Overcurrent": relay["overcurrent"].check_trip(I)
            }

        return results
