"""
GridForge Unsymmetrical Fault Solver

Calculates:

    SLG  - Single Line Ground
    LL   - Line Line
    LLG  - Double Line Ground


Uses:

    Positive sequence
    Negative sequence
    Zero sequence


Based on symmetrical component theory.

"""


import cmath
import math


from core.solver.short_circuit.fault_calculator import (
    FaultCalculator
)



class UnsymmetricalFaultSolver:



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
    # SOLVE FAULT
    # =====================================================

    def solve(
            self,
            bus_id,
            fault_type="SLG",
            fault_impedance=0j):


        V1 = (

            self.calculator
            .get_prefault_voltage(
                bus_id
            )

        )


        Z1 = (

            self.sequence_network
            .get_positive(
                bus_id
            )

        )


        Z2 = (

            self.sequence_network
            .get_negative(
                bus_id
            )

        )


        Z0 = (

            self.sequence_network
            .get_zero(
                bus_id
            )

        )



        # =================================================
        # SINGLE LINE TO GROUND
        # =================================================

        if fault_type.upper() == "SLG":


            If = (

                3 * V1
                /
                (
                    Z1
                    +
                    Z2
                    +
                    Z0
                    +
                    3*fault_impedance
                )

            )



        # =================================================
        # LINE TO LINE
        # =================================================

        elif fault_type.upper() == "LL":


            If = (

                math.sqrt(3)
                *
                V1
                /
                (
                    Z1
                    +
                    Z2
                    +
                    fault_impedance
                )

            )



        # =================================================
        # DOUBLE LINE TO GROUND
        # =================================================

        elif fault_type.upper() == "LLG":


            Z_parallel = (

                Z2
                *
                Z0
                /
                (
                    Z2
                    +
                    Z0
                    +
                    3*fault_impedance
                )

            )


            If = (

                V1
                /
                (
                    Z1
                    +
                    Z_parallel
                )

            )



        else:

            raise ValueError(
                "Unsupported fault type"
            )



        return {


            "bus":

                bus_id,


            "fault_type":

                fault_type.upper(),


            "V1":

                V1,


            "Z1":

                Z1,


            "Z2":

                Z2,


            "Z0":

                Z0,


            "fault_current":

                If,


            "fault_current_mag":

                abs(If)

        }
