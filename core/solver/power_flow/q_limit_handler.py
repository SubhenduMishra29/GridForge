"""
GridForge Generator Reactive Power Limit Handler

Handles:

- PV → PQ switching (when Q limits violated)
- PQ → PV restoration (when back within limits)
"""

class QLimitHandler:

    def __init__(self, network, tolerance=1e-6):

        self.network = network
        self.tol = tolerance

        # Track original PV buses
        self.original_pv = {
            bus.id for bus in network.buses if bus.is_pv()
        }

    # =====================================================
    # MAIN LOGIC
    # =====================================================

    def check_limits(self):

        converted = []

        for bus in self.network.buses:

            generator = self._find_generator(bus.id)

            if generator is None:
                continue

            Q = generator.Q

            # ---------------------------------
            # PV → PQ (limit violated)
            # ---------------------------------

            if bus.is_pv():

                if Q > generator.Qmax + self.tol:

                    bus.type = "PQ"
                    bus.Q_spec = generator.Qmax

                    converted.append(bus.id)

                elif Q < generator.Qmin - self.tol:

                    bus.type = "PQ"
                    bus.Q_spec = generator.Qmin

                    converted.append(bus.id)

            # ---------------------------------
            # PQ → PV (restore if possible)
            # ---------------------------------

            elif bus.is_pq() and bus.id in self.original_pv:

                if generator.Qmin + self.tol < Q < generator.Qmax - self.tol:

                    bus.type = "PV"

                    # restore voltage setpoint
                    bus.V = generator.Vset

                    converted.append(bus.id)

        return converted

    # =====================================================
    # INTERNAL
    # =====================================================

    def _find_generator(self, bus_id):

        for gen in self.network.generators:
            if gen.bus == bus_id:
                return gen

        return None
