from protection.distance_relay import DistanceRelay
from protection.overcurrent_relay import OvercurrentRelay


class ProtectionSystem:
    def __init__(self, network):
        """
        Initializes protection for each transmission line.

        Each line gets:
        - Distance relay (primary protection)
        - Overcurrent relay (backup protection)
        """
        self.network = network
        self.relays = {}

        for line in network.lines:
            i, j, Z = line

            self.relays[(i, j)] = {
                "distance": DistanceRelay(
                    Z_line=Z,
                    zone1_reach=0.8,   # 80% line (instantaneous)
                    zone2_reach=1.2    # backup reach
                ),
                "overcurrent": OvercurrentRelay(
                    pickup=2.0,
                    TMS=0.2,
                    curve="IEC_STANDARD_INVERSE"
                )
            }

    def evaluate_fault(self, V, I_line):
        """
        Evaluate relay operation under fault conditions.

        Parameters:
        -----------
        V : dict
            Bus voltages {bus: complex voltage}
        I_line : dict
            Line currents {(i,j): complex current}

        Returns:
        --------
        results : dict
            Trip decisions per relay
        """

        results = {}

        for (i, j), relay in self.relays.items():
            I = abs(I_line.get((i, j), 0))
            V_bus = abs(V[i])  # sending end voltage

            distance_trip = relay["distance"].check_trip(V_bus, I)
            overcurrent_trip = relay["overcurrent"].check_trip(I)

            results[(i, j)] = {
                "Distance": distance_trip,
                "Overcurrent": overcurrent_trip
            }

        return results
