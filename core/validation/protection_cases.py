"""
GridForge Protection Test Cases

Standard validation scenarios.

Cases:

1. Three phase fault
2. Earth fault
3. Overcurrent coordination
4. Breaker failure


"""


class ProtectionCase:



    def __init__(
            self,
            name,
            fault_type,
            fault_location,
            fault_impedance=0.0):


        self.name = name

        self.fault_type = fault_type

        self.fault_location = fault_location

        self.fault_impedance = fault_impedance



    def describe(self):

        return {

            "name":
                self.name,


            "fault_type":
                self.fault_type,


            "location":
                self.fault_location,


            "fault_impedance":
                self.fault_impedance

        }



# =========================================================
# STANDARD CASE LIBRARY
# =========================================================


def three_phase_fault_case(bus):


    return ProtectionCase(

        name="3PH_FAULT",

        fault_type="3PH",

        fault_location=bus,

        fault_impedance=0.0

    )



def line_to_ground_fault_case(bus):


    return ProtectionCase(

        name="LG_FAULT",

        fault_type="LG",

        fault_location=bus,

        fault_impedance=0.0

    )



def overcurrent_coordination_case(
        line):


    return ProtectionCase(

        name="OC_COORDINATION",

        fault_type="3PH",

        fault_location=line,

        fault_impedance=0.05

    )



def breaker_failure_case(
        breaker):


    return ProtectionCase(

        name="BREAKER_FAILURE",

        fault_type="BREAKER_FAIL",

        fault_location=breaker,

        fault_impedance=0.0

    )
