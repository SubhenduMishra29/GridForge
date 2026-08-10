import networkx as nx


class TopologyManager:

    def __init__(self, network):
        self.network = network
        self.graph = nx.MultiGraph()
        self._dirty = True

    # =====================================================
    # BUILD GRAPH
    # =====================================================

    def build(self):

        if not self._dirty:
            return self.graph

        self.graph.clear()

        # -------------------------
        # Add buses
        # -------------------------
        for bus in self.network.buses:
            self.graph.add_node(bus.id)

        # -------------------------
        # Add lines
        # -------------------------
        for line in getattr(self.network, "lines", []):

            if not getattr(line, "in_service", True):
                continue

            u = line.from_bus.id
            v = line.to_bus.id

            if u == v:
                continue

            self.graph.add_edge(
                u,
                v,
                element=line,
                type="line"
            )

        # -------------------------
        # Add transformers
        # -------------------------
        for trafo in getattr(self.network, "transformers", []):

            if not getattr(trafo, "in_service", True):
                continue

            u = trafo.from_bus.id
            v = trafo.to_bus.id

            if u == v:
                continue

            self.graph.add_edge(
                u,
                v,
                element=trafo,
                type="transformer"
            )

        self._dirty = False

        return self.graph

    # =====================================================
    # CONNECTIVITY
    # =====================================================

    def is_connected(self, bus_a, bus_b):

        self.build()

        a = bus_a.id if hasattr(bus_a, "id") else bus_a
        b = bus_b.id if hasattr(bus_b, "id") else bus_b

        return nx.has_path(self.graph, a, b)

    # =====================================================
    # ISLAND DETECTION
    # =====================================================

    def find_islands(self):

        self.build()

        return [list(comp) for comp in nx.connected_components(self.graph)]

    # =====================================================
    # SINGLE ISLAND CHECK
    # =====================================================

    def has_islanding(self):

        return len(self.find_islands()) > 1

    # =====================================================
    # ELEMENT STATUS
    # =====================================================

    def open_element(self, element):

        element.in_service = False
        self._dirty = True

    def close_element(self, element):

        element.in_service = True
        self._dirty = True

    # =====================================================
    # CONTINGENCY SUPPORT
    # =====================================================

    def simulate_outage(self, element):

        original = getattr(element, "in_service", True)

        element.in_service = False
        self._dirty = True

        self.build()
        islands = self.find_islands()

        # restore
        element.in_service = original
        self._dirty = True
        self.build()

        return {
            "element": getattr(element, "name", str(element)),
            "islanded": len(islands) > 1,
            "islands": islands
        }

    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self):

        self.build()

        return {
            "buses": self.graph.number_of_nodes(),
            "connections": self.graph.number_of_edges(),
            "islands": len(list(nx.connected_components(self.graph)))
        }
