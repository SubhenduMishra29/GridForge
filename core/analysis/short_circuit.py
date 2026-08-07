"""
GridForge Short Circuit Analysis Interface

High-level API for fault studies.


Numerical engine:

core.solver.short_circuit


Supported:

- Three phase fault
- LG fault
- LL fault
- LLG fault


"""


from core.solver.short_circuit import (

    ShortCircuitSolver,

    FaultType

)




class ShortCircuitAnalyzer:



    def __init__(

            self,

            network,

            sequence_network=None):


        self.network = network


        self.sequence_network = (

            sequence_network

        )


        self.result = None



    # =====================================================
    # RUN FAULT STUDY
    # =====================================================

    def run(

            self,

            fault_type,

            fault_bus,

            Zf=0.0):



        solver = ShortCircuitSolver(

            self.network,

            self.sequence_network

        )



        self.result = solver.solve(

            fault_type,

            fault_bus,

            Zf

        )



        return self.result



    # =====================================================
    # COMMON 3 PHASE FAULT
    # =====================================================

    def run_three_phase_fault(

            self,

            fault_bus,

            Zf=0.0):


        return self.run(

            FaultType.THREE_PHASE,

            fault_bus,

            Zf

        )



    # =====================================================
    # REPORT
    # =====================================================

    def summary(self):


        if self.result is None:


            return {


                "status":

                    "NOT_RUN"

            }



        return self.result
