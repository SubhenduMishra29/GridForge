"""
GridForge Core Network Engine v0.6

Responsibilities:

- Network topology management
- Equipment containers
- Ybus construction
- Analysis orchestration
- Protection coordination interface
- Dynamic simulation interface


Does NOT:

- Perform numerical solving
- Calculate faults directly
- Make protection decisions


"""

import numpy as np


# =====================================================
# ANALYSIS MODULES
# =====================================================

from core.analysis.load_flow import (
    LoadFlowSolver
)

from core.analysis.short_circuit import (
    ShortCircuitAnalyzer
)

from core.analysis.line_flow import (
    LineFlowCalculator
)

from core.analysis.transformer_flow import (
    TransformerFlowCalculator
)

from core.analysis.contingency import (
    ContingencyAnalyzer
)

from core.analysis.unbalanced_fault import (
    UnbalancedFaultAnalyzer
)



# =====================================================
# PROTECTION
# =====================================================

from core.protection.protection import (
    ProtectionSystem
)

from core.protection.breaker import (
    BreakerManager
)



# =====================================================
# DYNAMICS
# =====================================================

from core.dynamics.transient_stability import (
    TransientStabilitySolver
)

from core.dynamics.multi_machine import (
    MultiMachineSimulator
)



class Network:


    def __init__(
            self,
            base_mva=100.0):


        # ---------------------------------
        # Base system
        # ---------------------------------

        self.base_mva = base_mva



        # ---------------------------------
        # Equipment containers
        # ---------------------------------

        self.buses = []

        self.lines = []

        self.transformers = []

        self.generators = []



        # ---------------------------------
        # Internal indexing
        # ---------------------------------

        self.bus_index = {}

        self.Ybus = None



        # ---------------------------------
        # Sequence data
        # ---------------------------------

        self.sequence_network = None



        # ---------------------------------
        # Analysis results
        # ---------------------------------

        self.lf_result = None

        self.fault_result = None



        # ---------------------------------
        # Protection
        # ---------------------------------

        self.protection_system = (

            ProtectionSystem()

        )


        self.breaker_manager = (

            BreakerManager()

        )



        # ---------------------------------
        # Event state
        # ---------------------------------

        self.active_fault = None



    # =================================================
    # ADD ELEMENTS
    # =================================================


    def add_bus(
            self,
            bus):

        self.buses.append(bus)



    def add_line(
            self,
            line):

        self.lines.append(line)



    def add_transformer(
            self,
            trafo):

        self.transformers.append(trafo)



    def add_generator(
            self,
            gen):

        self.generators.append(gen)



    # =================================================
    # INDEXING
    # =================================================


    def _build_bus_index(self):


        self.bus_index = {

            bus.id: idx

            for idx, bus

            in enumerate(self.buses)

        }



    # =================================================
    # YBUS
    # =================================================


    def build_ybus(self):


        self._build_bus_index()


        n = len(self.buses)


        Y = np.zeros(

            (n,n),

            dtype=complex

        )



        # -------------------------------
        # Lines
        # -------------------------------


        for line in self.lines:


            if not self.breaker_manager.is_closed(
                    line.id):

                continue



            i = self.bus_index[
                line.from_bus.id
            ]

            j = self.bus_index[
                line.to_bus.id
            ]



            z = complex(

                line.r_pu,

                line.x_pu

            )


            y = 1/z



            b = (

                1j *

                line.b_pu /

                2

            )



            Y[i,i] += y+b

            Y[j,j] += y+b

            Y[i,j] -= y

            Y[j,i] -= y



        # -------------------------------
        # Transformers
        # -------------------------------


        for trafo in self.transformers:


            i = self.bus_index[
                trafo.from_bus.id
            ]


            j = self.bus_index[
                trafo.to_bus.id
            ]



            z = complex(

                trafo.r_pu,

                trafo.x_pu

            )


            y = 1/z



            tap = getattr(

                trafo,

                "tap_ratio",

                1.0

            )


            shift = np.deg2rad(

                getattr(

                    trafo,

                    "phase_shift_deg",

                    0.0

                )

            )



            a = (

                tap *

                np.exp(

                    1j*shift

                )

            )



            Y[i,i] += y/(a*np.conj(a))

            Y[j,j] += y

            Y[i,j] -= y/np.conj(a)

            Y[j,i] -= y/a



        self.Ybus = Y


        return Y



    # =================================================
    # LOAD FLOW
    # =================================================


    def run_load_flow(self):


        solver = LoadFlowSolver(

            self

        )


        self.lf_result = solver.solve()


        return self.lf_result



    # =================================================
    # POWER FLOW RESULTS
    # =================================================


    def compute_line_flows(self):


        calc = LineFlowCalculator(self)


        return calc.compute(

            self.lf_result["Vm"],

            self.lf_result["Va"]

        )



    def compute_transformer_flows(self):


        calc = TransformerFlowCalculator(self)


        return calc.compute(

            self.lf_result["Vm"],

            self.lf_result["Va"]

        )



    # =================================================
    # SHORT CIRCUIT
    # =================================================


    def apply_fault(

            self,

            bus_id,

            fault_type,

            Zf=0.0):


        self.active_fault = {


            "bus_id":

                bus_id,


            "type":

                fault_type,


            "Zf":

                Zf

        }



    def run_short_circuit(

            self,

            fault_bus,

            Zf=0.0):


        analyzer = ShortCircuitAnalyzer(

            self

        )


        self.fault_result = (

            analyzer.run_three_phase_fault(

                fault_bus,

                Zf

            )

        )


        return self.fault_result




    def run_unbalanced_faults(

            self,

            fault_type,

            fault_bus,

            Zf=0.0):


        analyzer = ShortCircuitAnalyzer(

            self,

            self.sequence_network

        )


        self.fault_result = analyzer.run(

            fault_type,

            fault_bus,

            Zf

        )


        return self.fault_result



    # =================================================
    # PROTECTION
    # =================================================


    def run_protection(self):


        actions = (

            self.protection_system.evaluate(

                self.fault_result,

                self.lines,

                self.generators

            )

        )


        self.breaker_manager.apply(

            actions

        )



    # =================================================
    # NETWORK UPDATE
    # =================================================


    def reconfigure(self):


        self.build_ybus()



    # =================================================
    # DYNAMICS
    # =================================================


    def run_transient_stability(

            self,

            t_end=5.0,

            dt=0.01):


        solver = TransientStabilitySolver(

            self

        )


        return solver.run(

            self.active_fault,

            t_end,

            dt

        )



    def run_multi_machine(

            self,

            t_end=5.0,

            dt=0.01):


        simulator = MultiMachineSimulator(

            self

        )


        return simulator.run(

            t_end,

            dt

        )



    # =================================================
    # FULL PIPELINE
    # =================================================


    def simulate(

            self,

            fault_bus):


        self.build_ybus()



        self.run_load_flow()



        self.apply_fault(

            fault_bus,

            "3PH"

        )



        self.run_short_circuit(

            fault_bus

        )



        self.run_protection()



        self.reconfigure()



        self.run_load_flow()



        return self.run_transient_stability()



    # =================================================
    # UTILITIES
    # =================================================


    def validate(self):


        assert len(self.buses)>0, (

            "No buses in network"

        )


        assert self.Ybus is not None, (

            "Ybus not built"

        )



    def summary(self):


        return {


            "buses":

                len(self.buses),


            "lines":

                len(self.lines),


            "transformers":

                len(self.transformers),


            "generators":

                len(self.generators)

        }
