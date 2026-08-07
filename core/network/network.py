"""
GridForge Network Core

System orchestration layer.

Responsibilities:

- Manage network components
- Build Ybus
- Execute analysis
- Coordinate protection
- Handle switching events
- Interface with dynamics

Does NOT:

- Solve equations directly
- Contain relay algorithms
- Contain GUI state

"""


import numpy as np


# ==========================================================
# ANALYSIS
# ==========================================================

from core.analysis.load_flow import LoadFlowSolver
from core.analysis.line_flow import LineFlowCalculator
from core.analysis.transformer_flow import TransformerFlowCalculator
from core.analysis.contingency import ContingencyAnalyzer
from core.analysis.short_circuit import ShortCircuitAnalyzer
from core.analysis.unbalanced_fault import UnbalancedFaultAnalyzer


# ==========================================================
# PROTECTION
# ==========================================================

from core.protection.protection_system import ProtectionSystem
from core.protection.breaker_manager import BreakerManager


# ==========================================================
# DYNAMICS
# ==========================================================

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


        # --------------------------------------------------
        # Base
        # --------------------------------------------------

        self.base_mva = base_mva



        # --------------------------------------------------
        # Equipment containers
        # --------------------------------------------------

        self.buses = []

        self.lines = []

        self.transformers = []

        self.generators = []

        self.breakers = []



        # --------------------------------------------------
        # Internal structures
        # --------------------------------------------------

        self.bus_index = {}

        self.Ybus = None



        # --------------------------------------------------
        # Analysis results
        # --------------------------------------------------

        self.lf_result = None

        self.fault_result = None



        # --------------------------------------------------
        # Protection
        # --------------------------------------------------

        self.breaker_manager = BreakerManager()


        self.protection_system = ProtectionSystem(
            self.breaker_manager
        )



        # --------------------------------------------------
        # Fault state
        # --------------------------------------------------

        self.active_fault = None




    # ======================================================
    # ADD ELEMENTS
    # ======================================================

    def add_bus(self, bus):

        self.buses.append(bus)



    def add_line(self, line):

        self.lines.append(line)



    def add_transformer(self, transformer):

        self.transformers.append(transformer)



    def add_generator(self, generator):

        self.generators.append(generator)



    def add_breaker(self, breaker):

        self.breakers.append(breaker)

        self.breaker_manager.add_breaker(
            breaker
        )



    # ======================================================
    # INDEXING
    # ======================================================

    def _build_bus_index(self):

        self.bus_index = {

            bus.id:index

            for index,bus

            in enumerate(self.buses)

        }




    # ======================================================
    # YBUS BUILD
    # ======================================================

    def build_ybus(self):


        self._build_bus_index()


        n = len(self.buses)


        Y = np.zeros(

            (n,n),

            dtype=complex

        )



        # ------------------------------
        # Lines
        # ------------------------------

        for line in self.lines:


            if not self.breaker_manager.is_closed(
                line.name
            ):

                continue



            i = self.bus_index[
                line.from_bus
            ]


            j = self.bus_index[
                line.to_bus
            ]



            z = complex(

                line.r_pu,

                line.x_pu

            )


            y = 1/z



            b = 1j*line.b_pu/2



            Y[i,i] += y+b

            Y[j,j] += y+b

            Y[i,j] -= y

            Y[j,i] -= y



        # ------------------------------
        # Transformers
        # ------------------------------

        for trafo in self.transformers:


            i = self.bus_index[
                trafo.from_bus
            ]


            j = self.bus_index[
                trafo.to_bus
            ]



            y = trafo.y_pu


            tap = getattr(

                trafo,

                "tap_ratio",

                1.0

            )



            Y[i,i] += y/(tap*tap)

            Y[j,j] += y

            Y[i,j] -= y/tap

            Y[j,i] -= y/tap




        self.Ybus = Y


        return Y




    # ======================================================
    # LOAD FLOW
    # ======================================================

    def run_load_flow(self):


        solver = LoadFlowSolver(self)


        self.lf_result = solver.solve()


        return self.lf_result




    # ======================================================
    # FLOWS
    # ======================================================

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




    # ======================================================
    # CONTINGENCY
    # ======================================================

    def run_contingency(self):


        analyzer = ContingencyAnalyzer(

            self,

            LoadFlowSolver

        )


        return analyzer.run_n_minus_1()




    # ======================================================
    # FAULT
    # ======================================================

    def apply_fault(
            self,
            bus_id,
            fault_type="3PH",
            Zf=0.0):


        self.active_fault = {


            "bus_id":

                bus_id,


            "type":

                fault_type,


            "Zf":

                Zf

        }




    def run_short_circuit(self):


        solver = ShortCircuitAnalyzer(self)


        self.fault_result = (

            solver.run_three_phase_faults()

        )


        return self.fault_result




    def run_unbalanced_faults(self):


        solver = UnbalancedFaultAnalyzer(self)


        self.fault_result = solver.run(

            fault_type=self.active_fault["type"],

            Zf=self.active_fault["Zf"],

            lf_result=self.lf_result

        )


        return self.fault_result




    # ======================================================
    # PROTECTION
    # ======================================================

    def run_protection(
            self,
            measurements,
            time=0.0):


        return self.protection_system.process_fault(

            measurements,

            time

        )




    # ======================================================
    # NETWORK UPDATE
    # ======================================================

    def reconfigure(self):


        """
        Rebuild topology after breaker operations.
        """


        return self.build_ybus()




    # ======================================================
    # DYNAMICS
    # ======================================================

    def run_transient_stability(
            self,
            t_end=5.0,
            dt=0.01):


        solver = TransientStabilitySolver(self)


        return solver.run(

            self.active_fault,

            t_end,

            dt

        )




    def run_multi_machine(
            self,
            t_end=5.0,
            dt=0.01):


        simulator = MultiMachineSimulator(self)


        return simulator.run(

            t_end,

            dt

        )




    # ======================================================
    # COMPLETE SIMULATION PIPELINE
    # ======================================================

    def simulate(
            self,
            fault_bus,
            measurements):


        self.build_ybus()



        self.run_load_flow()



        self.apply_fault(
            fault_bus
        )



        self.run_short_circuit()



        self.run_protection(
            measurements
        )



        self.reconfigure()



        self.run_load_flow()



        return self.run_transient_stability()




    # ======================================================
    # VALIDATION
    # ======================================================

    def validate(self):


        assert len(self.buses)>0


        assert self.Ybus is not None




    # ======================================================
    # SUMMARY
    # ======================================================

    def summary(self):


        return {


            "buses":
                len(self.buses),


            "lines":
                len(self.lines),


            "transformers":
                len(self.transformers),


            "generators":
                len(self.generators),


            "breakers":
                len(self.breakers)

        }
