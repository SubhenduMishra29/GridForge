"""
GridForge Unsymmetrical Fault Calculator

Handles:

LG  - Single Line Ground Fault
LL  - Line Line Fault
LLG - Double Line Ground Fault


Uses:

Positive sequence Z1
Negative sequence Z2
Zero sequence Z0


"""



import cmath



class UnsymmetricalFault:



    def __init__(

            self,

            sequence_network):


        self.sequence_network = sequence_network




    # =====================================================
    # SINGLE LINE TO GROUND FAULT
    # =====================================================

    def calculate_lg_fault(

            self,

            elements,

            Vprefault=1.0,

            Zf=0.0):


        """
        LG fault:

        If = 3V /
        (Z1 + Z2 + Z0 + 3Zf)

        """


        Z1 = self.sequence_network.total_impedance(

            elements,

            "positive"

        )


        Z2 = self.sequence_network.total_impedance(

            elements,

            "negative"

        )


        Z0 = self.sequence_network.total_impedance(

            elements,

            "zero"

        )



        If = (

            3 * Vprefault

        ) / (

            Z1 +

            Z2 +

            Z0 +

            3 * Zf

        )



        return {


            "fault_type":

                "LG",


            "fault_current":

                If,


            "magnitude":

                abs(If)

        }




    # =====================================================
    # LINE TO LINE FAULT
    # =====================================================

    def calculate_ll_fault(

            self,

            elements,

            Vprefault=1.0,

            Zf=0.0):


        """
        LL fault:

        If = √3 V /
        (Z1 + Z2 + Zf)

        """


        Z1 = self.sequence_network.total_impedance(

            elements,

            "positive"

        )


        Z2 = self.sequence_network.total_impedance(

            elements,

            "negative"

        )



        If = (

            cmath.sqrt(3)

            *

            Vprefault

        ) / (

            Z1 +

            Z2 +

            Zf

        )



        return {


            "fault_type":

                "LL",


            "fault_current":

                If,


            "magnitude":

                abs(If)

        }




    # =====================================================
    # DOUBLE LINE TO GROUND FAULT
    # =====================================================

    def calculate_llg_fault(

            self,

            elements,

            Vprefault=1.0,

            Zf=0.0):


        """
        LLG fault calculation.

        Sequence network combination:

        Z2 || (Z0 + 3Zf)

        """


        Z1 = self.sequence_network.total_impedance(

            elements,

            "positive"

        )


        Z2 = self.sequence_network.total_impedance(

            elements,

            "negative"

        )


        Z0 = self.sequence_network.total_impedance(

            elements,

            "zero"

        )



        Zparallel = (

            Z2 *

            (Z0 + 3*Zf)

        ) / (

            Z2 +

            Z0 +

            3*Zf

        )



        If = (

            Vprefault

        ) / (

            Z1 +

            Zparallel

        )



        return {


            "fault_type":

                "LLG",


            "fault_current":

                If,


            "magnitude":

                abs(If)

        }
