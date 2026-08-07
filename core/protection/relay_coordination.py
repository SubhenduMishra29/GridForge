GRADING_MARGIN = 0.3


class RelayCoordinator:
    def __init__(self, network):
        self.network = network

    # --------------------------------------------------------
    # BUILD TOPOLOGY GRAPH
    # --------------------------------------------------------
    def _build_adjacency(self):
        adj = {}

        for line in self.network.lines:
            i = line.from_bus.id
            j = line.to_bus.id

            adj.setdefault(i, []).append((j, line))
            adj.setdefault(j, []).append((i, line))

        return adj

    # --------------------------------------------------------
    # FIND DISTANCE FROM SOURCE (BFS)
    # --------------------------------------------------------
    def _distance_from_generators(self):
        from collections import deque

        adj = self._build_adjacency()
        dist = {bus.id: float("inf") for bus in self.network.buses}

        q = deque()

        # Generators = sources
        for gen in self.network.generators:
            bus_id = gen.bus.id
            dist[bus_id] = 0
            q.append(bus_id)

        while q:
            u = q.popleft()

            for v, _ in adj.get(u, []):
                if dist[v] > dist[u] + 1:
                    dist[v] = dist[u] + 1
                    q.append(v)

        return dist

    # --------------------------------------------------------
    # COORDINATE OVERCURRENT RELAYS
    # --------------------------------------------------------
    def coordinate_overcurrent(self, protection_system):
        dist = self._distance_from_generators()

        for relay in protection_system.oc_relays:
            line = relay.line

            # Use receiving end as "downstream"
            d = dist[line.to_bus.id]

            # ----------------------------
            # Pickup Setting
            # ----------------------------
            relay.pickup = 1.2 + 0.3 * d

            # ----------------------------
            # Time Dial Setting
            # ----------------------------
            relay.TMS = 0.1 + 0.1 * d

    # --------------------------------------------------------
    # COORDINATE DISTANCE RELAYS
    # --------------------------------------------------------
    def coordinate_distance(self, protection_system):
        for relay in protection_system.distance_relays:
            Z_line = complex(relay.line.r_pu, relay.line.x_pu)

            # Zone-1: 80% of line
            relay.Z1 = 0.8 * Z_line

            # Zone-2: 120% of line
            relay.Z2 = 1.2 * Z_line

            # Delay for backup
            relay.delay_zone2 = GRADING_MARGIN

    # --------------------------------------------------------
    # GLOBAL COORDINATION
    # --------------------------------------------------------
    def run(self, protection_system):
        self.coordinate_overcurrent(protection_system)
        self.coordinate_distance(protection_system)
