import numpy as np


# ------------------------------------------------------------
# IEC CURVES
# ------------------------------------------------------------
def iec_time(I, Ip, curve="SI", TMS=0.1):
    """
    IEC 60255 inverse time curves
    """
    if I <= Ip:
        return None

    M = I / Ip

    if curve == "SI":  # Standard Inverse
        return TMS * 0.14 / (M**0.02 - 1)

    elif curve == "VI":  # Very Inverse
        return TMS * 13.5 / (M - 1)

    elif curve == "EI":  # Extremely Inverse
        return TMS * 80 / (M**2 - 1)

    return None


# ------------------------------------------------------------
# DISTANCE RELAY
# ------------------------------------------------------------
class DistanceRelay:
    def __init__(self, line, Z1, Z2, delay_zone2=0.3):
        self.line = line
        self.Z1 = Z1  # Zone 1 reach
        self.Z2 = Z2  # Zone 2 reach
        self.delay_zone2 = delay_zone2

    def measure_impedance(self, V, I):
        if abs(I) < 1e-6:
            return np.inf
        return V / I

    def evaluate(self, V, I):
        Z = self.measure_impedance(V, I)

        if abs(Z) <= abs(self.Z1):
            return 0.0  # Instant trip

        elif abs(Z) <= abs(self.Z2):
            return self.delay_zone2  # Delayed trip

        return None


# ------------------------------------------------------------
# OVERCURRENT RELAY
# ------------------------------------------------------------
class OvercurrentRelay:
    def __init__(self, line, pickup, curve="SI", TMS=0.1):
        self.line = line
        self.pickup = pickup
        self.curve = curve
        self.TMS = TMS

    def evaluate(self, I):
        return iec_time(abs(I), self.pickup, self.curve, self.TMS)


# ------------------------------------------------------------
# PROTECTION SYSTEM
# ------------------------------------------------------------
class ProtectionSystem:
    def __init__(self):
        self.distance_relays = []
        self.oc_relays = []

    # --------------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------------
    def add_distance_relay(self, relay):
        self.distance_relays.append(relay)

    def add_overcurrent_relay(self, relay):
        self.oc_relays.append(relay)

    # --------------------------------------------------------
    # MAIN EVALUATION
    # --------------------------------------------------------
    def evaluate(self, fault_result, lines, generators):
        """
        Returns list of breaker actions
        """

        actions = []

        if fault_result is None:
            return actions

        # Expected structure:
        # fault_result["line_currents"][line_id]
        # fault_result["bus_voltages"][bus_id]

        line_currents = fault_result.get("line_currents", {})
        bus_voltages = fault_result.get("bus_voltages", {})

        # ------------------------
        # DISTANCE RELAYS
        # ------------------------
        for relay in self.distance_relays:
            line = relay.line

            if line.id not in line_currents:
                continue

            I = line_currents[line.id]

            # Use sending-end voltage
            V = bus_voltages.get(line.from_bus.id, 1.0)

            delay = relay.evaluate(V, I)

            if delay is not None:
                actions.append({
                    "target": line.id,
                    "delay": delay,
                    "type": "distance"
                })

        # ------------------------
        # OVERCURRENT RELAYS
        # ------------------------
        for relay in self.oc_relays:
            line = relay.line

            if line.id not in line_currents:
                continue

            I = line_currents[line.id]

            delay = relay.evaluate(I)

            if delay is not None:
                actions.append({
                    "target": line.id,
                    "delay": delay,
                    "type": "overcurrent"
                })

        return actions
