"""
GridForge Symmetrical Fault Solver

Calculates:

    Three-phase faults

Uses:

    Positive sequence network only


Equation:

        Vprefault
    If = -------------
          Z1 + Zf


"""



from core.solver.short_circuit.fault_calculator import (
    FaultCalculator
)



class SymmetricalFaultSolver:



    def __init__(
            self,
            network,
            sequence_network):


        self.network = network

        self.sequence_network = sequence_network

        self.calculator = FaultCalculator(
            network
        )



    # =====================================================
    # THREE PHASE FAULT
    # =====================================================

    def solve(
            self,
            bus_id,
            fault_impedance=0j):


        # ---------------------------------
        # Prefault voltage
        # ---------------------------------

        Vprefault = (

            self.calculator
            .get_prefault_voltage(
                bus_id
            )

        )



        # ---------------------------------
        # Positive sequence impedance
        # ---------------------------------

        Z1 = (

            self.sequence_network
            .get_positive(
                bus_id
            )

        )



        # ---------------------------------
        # Fault current
        # ---------------------------------

        If = (

            self.calculator
            .calculate_current(

                Vprefault,

                Z1 + fault_impedance

            )

        )



        # ---------------------------------
        # Return result
        # ---------------------------------

        return {


            "bus":

                bus_id,


            "fault_type":

                "3PH",


            "sequence":

                "positive",


            "V_prefault":

                Vprefault,


            "Z1":

                Z1,


            "Zf":

                fault_impedance,


            "fault_current":

                If,


            "fault_current_mag":

                abs(If)

        }
