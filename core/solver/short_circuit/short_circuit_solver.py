"""
GridForge Short Circuit Solver

Main short circuit analysis engine.

Supports:

- Three phase fault
- LG fault
- LL fault
- LLG fault


Architecture:

Network
   |
   ↓
Impedance Matrix
   |
   ↓
Fault Calculator
   |
   ↓
Fault Result


"""


from core.solver.short_circuit.impedance_matrix import (
    ImpedanceMatrix
)


from core.solver.short_circuit.symmetrical_fault import (
    SymmetricalFault
)


from core.solver.short_circuit.unsymmetrical_fault import (
    UnsymmetricalFault
)


from core.solver.short_circuit.fault_types import (
    FaultType
)




class ShortCircuitSolver:



    def __init__(

            self,

            network,

            sequence_network=None):


        self.network = network


        self.sequence_network = (

            sequence_network

        )


        self.impedance_matrix = (

            ImpedanceMatrix(network)

        )



    # =====================================================
    # SOLVE
    # =====================================================

    def solve(

            self,

            fault_type,

            fault_bus,

            Zf=0.0):


        """
        Execute fault calculation.

        Parameters:

            fault_type:
                FaultType enum


            fault_bus:
                Fault location


            Zf:
                Fault impedance


        """



        # ---------------------------------
        # Balanced fault
        # ---------------------------------

        if fault_type == FaultType.THREE_PHASE:



            self.impedance_matrix.build()



            calculator = SymmetricalFault(

                self.impedance_matrix

            )



            return calculator.calculate_three_phase_fault(

                fault_bus,

                Zf=Zf

            )



        # ---------------------------------
        # Unbalanced faults
        # ---------------------------------

        if self.sequence_network is None:


            raise RuntimeError(

                "Sequence network required "
                "for unbalanced faults"

            )



        calculator = UnsymmetricalFault(

            self.sequence_network

        )



        elements = [

            fault_bus

        ]



        if fault_type == FaultType.SINGLE_LINE_GROUND:



            return calculator.calculate_lg_fault(

                elements,

                Zf=Zf

            )



        elif fault_type == FaultType.LINE_LINE:



            return calculator.calculate_ll_fault(

                elements,

                Zf=Zf

            )



        elif fault_type == FaultType.DOUBLE_LINE_GROUND:



            return calculator.calculate_llg_fault(

                elements,

                Zf=Zf

            )



        else:


            raise ValueError(

                "Unsupported fault type"

            )
