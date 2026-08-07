# core/network/network.py

"""
GridForge Network Core

Central electrical network container.

Responsibilities:
    - Store electrical equipment
    - Maintain topology
    - Provide element lookup
    - Maintain network state

Does NOT:
    - Solve load flow
    - Build Ybus
    - Solve faults
    - Run transient stability

Those belong to:
    core/network/ybus.py
    core/solver/
    core/simulation/
"""


from core.models import (
    Bus,
    Line,
    Transformer,
    Generator,
    Relay,
    Breaker
)



class Network:


    def __init__(
            self,
            name="GridForge Network"
    ):

        self.name = name


        # ==================================================
        # EQUIPMENT CONTAINERS
        # ==================================================

        self.buses = []

        self.lines = []

        self.transformers = []

        self.generators = []

        self.relays = []

        self.breakers = []



        # ==================================================
        # INDEX STRUCTURES
        # ==================================================

        self.bus_index = {}

        self.line_index = {}

        self.generator_index = {}



        # ==================================================
        # NETWORK STATE
        # ==================================================

        self.Ybus = None


        self.active_fault = None


        self.time = 0.0



        # Simulation results

        self.load_flow_result = None

        self.fault_result = None

        self.dynamic_result = None



    # ======================================================
    # ADD ELEMENTS
    # ======================================================


    def add_bus(
            self,
            bus: Bus):

        self.buses.append(bus)

        self._build_bus_index()



    def add_line(
            self,
            line: Line):

        self.lines.append(line)

        self.line_index[line.name] = line



    def add_transformer(
            self,
            transformer: Transformer):

        self.transformers.append(
            transformer
        )



    def add_generator(
            self,
            generator: Generator):

        self.generators.append(
            generator
        )

        self.generator_index[
            generator.name
        ] = generator



    def add_relay(
            self,
            relay: Relay):

        self.relays.append(relay)



    def add_breaker(
            self,
            breaker: Breaker):

        self.breakers.append(breaker)



    # ======================================================
    # INDEXING
    # ======================================================


    def _build_bus_index(self):

        self.bus_index = {

            bus.id: idx

            for idx, bus
            in enumerate(self.buses)

        }



    def rebuild_indexes(self):

        self._build_bus_index()


        self.line_index = {

            line.name: line

            for line in self.lines

        }


        self.generator_index = {

            gen.name: gen

            for gen in self.generators

        }



    # ======================================================
    # LOOKUP
    # ======================================================


    def get_bus(
            self,
            bus_id):

        return self.buses[
            self.bus_index[bus_id]
        ]



    def get_line(
            self,
            name):

        return self.line_index[name]



    def get_generator(
            self,
            name):

        return self.generator_index[name]



    # ======================================================
    # TOPOLOGY INFORMATION
    # ======================================================


    def connected_lines(
            self,
            bus_id):

        result = []


        for line in self.lines:

            if not line.in_service:
                continue


            if (
                line.from_bus == bus_id
                or
                line.to_bus == bus_id
            ):

                result.append(line)


        return result



    def connected_generators(
            self,
            bus_id):

        return [

            gen

            for gen in self.generators

            if gen.bus == bus_id

        ]



    # ======================================================
    # ACTIVE ELEMENTS
    # ======================================================


    def active_lines(self):

        return [

            line

            for line in self.lines

            if line.in_service

        ]



    def active_transformers(self):

        return [

            trafo

            for trafo in self.transformers

            if trafo.in_service

        ]



    # ======================================================
    # FAULT STATE
    # ======================================================


    def apply_fault(
            self,

            bus_id,

            fault_type="3PH",

            impedance=0.0):


        self.active_fault = {


            "bus":

                bus_id,


            "type":

                fault_type,


            "Zf":

                impedance

        }



    def clear_fault(self):

        self.active_fault = None



    # ======================================================
    # RESET
    # ======================================================


    def reset(self):


        for bus in self.buses:

            bus.reset()



        for gen in self.generators:

            gen.reset_state()



        for breaker in self.breakers:

            breaker.reset()



        self.active_fault = None

        self.time = 0.0



        self.load_flow_result = None

        self.fault_result = None

        self.dynamic_result = None



    # ======================================================
    # VALIDATION
    # ======================================================


    def validate(self):

        if len(self.buses) == 0:

            raise ValueError(
                "Network has no buses"
            )


        if not any(
            bus.is_slack()
            for bus in self.buses
        ):

            raise ValueError(
                "No slack bus defined"
            )



    # ======================================================
    # SUMMARY
    # ======================================================


    def summary(self):

        return {


            "name":
                self.name,


            "buses":
                len(self.buses),


            "lines":
                len(self.lines),


            "transformers":
                len(self.transformers),


            "generators":
                len(self.generators),


            "relays":
                len(self.relays),


            "breakers":
                len(self.breakers)

        }



    # ======================================================
    # DEBUG
    # ======================================================


    def __repr__(self):

        return (

            f"Network("
            f"{self.name}, "
            f"Buses={len(self.buses)}, "
            f"Lines={len(self.lines)}, "
            f"Generators={len(self.generators)})"

        )
