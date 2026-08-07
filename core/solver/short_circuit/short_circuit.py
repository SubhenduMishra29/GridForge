"""
GridForge Short Circuit Solver Interface

Public API for:

    - 3 Phase fault
    - SLG fault
    - LL fault
    - LLG fault


Uses:

    sequence_network.py
    symmetrical_fault.py
    unsymmetrical_fault.py


Called by:

    core/network/network.py
"""


from core.solver.short_circuit.sequence_network import (
    SequenceNetwork
)

from core.solver.short_circuit.symmetrical_fault import (
    SymmetricalFaultSolver
)

from core.solver.short_circuit.unsymmetrical_fault import (
    UnsymmetricalFaultSolver
)



class ShortCircuitSolver:


    def __init__(self, network):

        self.network = network

        self.sequence_network = (
            SequenceNetwork()
        )


        self._build_sequence_network()



    # =====================================================
    # BUILD SEQUENCE MODEL
    # =====================================================

    def _build_sequence_network(self):

        """
        Creates sequence impedance database.

        Current implementation:
        Uses available model data.

        Later extended with:
            - generator Xd''
            - transformer Z0
            - line sequence impedance

        """


        for bus in self.network.buses:


            # Placeholder Thevenin impedance

            Z1 = complex(
                0.0,
                0.1
            )


            Z2 = Z1


            Z0 = complex(
                0.0,
                0.2
            )


            self.sequence_network.add_element(

                bus.id,

                Z1,

                Z2,

                Z0

            )



    # =====================================================
    # SOLVE FAULT
    # =====================================================

    def solve(
            self,
            bus_id,
            fault_type="3PH",
            fault_impedance=0j):


        fault_type = fault_type.upper()



        # -----------------------------
        # Three phase fault
        # -----------------------------

        if fault_type in [
            "3PH",
            "3_PHASE",
            "THREE_PHASE"
        ]:


            solver = SymmetricalFaultSolver(

                self.network,

                self.sequence_network

            )


            return solver.solve(

                bus_id,

                fault_impedance

            )



        # -----------------------------
        # Unbalanced faults
        # -----------------------------

        elif fault_type in [

            "SLG",
            "LL",
            "LLG"

        ]:


            solver = UnsymmetricalFaultSolver(

                self.network,

                self.sequence_network

            )


            return solver.solve(

                bus_id,

                fault_type,

                fault_impedance

            )



        else:

            raise ValueError(
                f"Unsupported fault type: {fault_type}"
            )
