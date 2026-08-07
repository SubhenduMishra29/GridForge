"""
GridForge Network Topology Manager

Responsible for:

    - Electrical connectivity graph
    - Network islands
    - Switching topology
    - Connectivity validation

Does NOT:

    - Build Ybus
    - Solve power flow
    - Calculate faults


Used by:

    core/network/network.py
    core/solver/contingency
    core/simulation
"""


import networkx as nx



class TopologyManager:


    def __init__(self, network):

        self.network = network

        self.graph = nx.Graph()



    # =====================================================
    # BUILD GRAPH
    # =====================================================

    def build(self):

        self.graph.clear()


        # -------------------------
        # Add buses
        # -------------------------

        for bus in self.network.buses:

            self.graph.add_node(
                bus.id
            )



        # -------------------------
        # Add lines
        # -------------------------

        for line in self.network.lines:


            if hasattr(line, "in_service"):

                if not line.in_service:

                    continue


            self.graph.add_edge(

                line.from_bus,

                line.to_bus,

                element=line,

                type="line"

            )



        # -------------------------
        # Add transformers
        # -------------------------

        for trafo in self.network.transformers:


            if hasattr(trafo, "in_service"):

                if not trafo.in_service:

                    continue



            self.graph.add_edge(

                trafo.from_bus,

                trafo.to_bus,

                element=trafo,

                type="transformer"

            )


        return self.graph



    # =====================================================
    # CONNECTIVITY
    # =====================================================


    def is_connected(
            self,
            bus_a,
            bus_b):


        if self.graph.number_of_nodes() == 0:

            self.build()


        return nx.has_path(

            self.graph,

            bus_a,

            bus_b

        )



    # =====================================================
    # ISLAND DETECTION
    # =====================================================


    def find_islands(self):


        if self.graph.number_of_nodes() == 0:

            self.build()



        islands = []


        for component in nx.connected_components(
                self.graph):


            islands.append(
                list(component)
            )


        return islands



    # =====================================================
    # SINGLE ISLAND CHECK
    # =====================================================


    def has_islanding(self):


        islands = self.find_islands()


        return len(islands) > 1



    # =====================================================
    # ELEMENT STATUS
    # =====================================================


    def open_element(
            self,
            element):


        element.in_service = False


        self.build()



    def close_element(
            self,
            element):


        element.in_service = True


        self.build()



    # =====================================================
    # CONTINGENCY SUPPORT
    # =====================================================


    def simulate_outage(
            self,
            element):


        original_state = (
            element.in_service
            if hasattr(
                element,
                "in_service"
            )
            else True
        )


        element.in_service = False


        self.build()



        islands = self.find_islands()



        # restore

        element.in_service = original_state


        self.build()



        return {

            "element":
                element.name,

            "islanded":
                len(islands) > 1,

            "islands":
                islands

        }



    # =====================================================
    # SUMMARY
    # =====================================================


    def summary(self):

        if self.graph.number_of_nodes() == 0:

            self.build()


        return {


            "buses":

                self.graph.number_of_nodes(),


            "connections":

                self.graph.number_of_edges(),


            "islands":

                len(
                    list(
                        nx.connected_components(
                            self.graph
                        )
                    )
                )

        }
