"""
GridForge Fault Calculator Core

Common engine for short circuit calculations.

Used by:

    symmetrical_fault.py
    unsymmetrical_fault.py


Calculates:

    Fault current
    Fault impedance
    Fault MVA
"""


import cmath



class FaultCalculator:


    def __init__(self, network):

        self.network = network



    # =====================================================
    # PREFault VOLTAGE
    # =====================================================

    def get_prefault_voltage(
            self,
            bus_id):

        """
        Returns prefault voltage at fault bus.

        Uses solved load flow voltage.

        """

        for bus in self.network.buses:

            if bus.id == bus_id:

                return (
                    bus.V *
                    cmath.exp(
                        1j * bus.theta
                    )
                )


        raise ValueError(
            f"Bus {bus_id} not found"
        )



    # =====================================================
    # FAULT CURRENT
    # =====================================================

    def calculate_current(
            self,
            V_prefault,
            Z_fault):


        if Z_fault == 0:

            raise ZeroDivisionError(
                "Fault impedance cannot be zero"
            )


        return (
            V_prefault /
            Z_fault
        )



    # =====================================================
    # FAULT MVA
    # =====================================================

    def fault_mva(
            self,
            voltage_kv,
            current_ka):


        """
        Three phase fault level

        MVA = sqrt(3) × kV × kA

        """


        return (

            1.7320508
            *
            voltage_kv
            *
            current_ka

        )



    # =====================================================
    # RESULT FORMATTER
    # =====================================================

    def result(
            self,
            bus_id,
            fault_type,
            current,
            impedance):


        return {


            "bus":

                bus_id,


            "fault_type":

                fault_type,


            "fault_current":

                current,


            "fault_impedance":

                impedance


        }
