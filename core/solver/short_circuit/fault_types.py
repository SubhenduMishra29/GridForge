"""
GridForge Short Circuit Fault Types

Defines supported electrical fault classifications.

Calculation logic belongs to:

core.solver.short_circuit.fault_calculator

"""


from enum import Enum



class FaultType(Enum):


    """
    Electrical fault classification
    """



    # ---------------------------------
    # Balanced fault
    # ---------------------------------

    THREE_PHASE = "3PH"



    # ---------------------------------
    # Unbalanced faults
    # ---------------------------------

    SINGLE_LINE_GROUND = "LG"


    LINE_LINE = "LL"


    DOUBLE_LINE_GROUND = "LLG"



    # ---------------------------------
    # Utility
    # ---------------------------------

    @staticmethod
    def is_balanced(
            fault_type):


        return (

            fault_type ==

            FaultType.THREE_PHASE

        )



    @staticmethod
    def is_unbalanced(
            fault_type):


        return (

            fault_type in [

                FaultType.SINGLE_LINE_GROUND,

                FaultType.LINE_LINE,

                FaultType.DOUBLE_LINE_GROUND

            ]

        )
