"""
GridForge Sequence Network Model

Handles:

    Positive sequence  Z1
    Negative sequence  Z2
    Zero sequence      Z0


Used by:

    symmetrical_fault.py
    unsymmetrical_fault.py


Sequence impedance convention:

    Z = R + jX

"""



class SequenceNetwork:


    def __init__(self):

        # ---------------------------------
        # Element sequence impedances
        # ---------------------------------

        self.positive = {}

        self.negative = {}

        self.zero = {}



    # =====================================================
    # ADD ELEMENT SEQUENCE IMPEDANCE
    # =====================================================

    def add_element(
            self,
            element_id,
            Z1,
            Z2=None,
            Z0=None):


        """
        Add sequence impedance.

        Parameters:

            element_id:
                Bus, line, transformer, generator ID


            Z1:
                Positive sequence impedance


            Z2:
                Negative sequence impedance


            Z0:
                Zero sequence impedance

        """


        self.positive[element_id] = Z1



        # Usually Z2 ≈ Z1

        self.negative[element_id] = (
            Z2
            if Z2 is not None
            else Z1
        )



        # Zero sequence may not exist

        self.zero[element_id] = (
            Z0
            if Z0 is not None
            else complex(0,0)
        )



    # =====================================================
    # GET SEQUENCE IMPEDANCE
    # =====================================================

    def get_positive(
            self,
            element_id):

        return self.positive[element_id]



    def get_negative(
            self,
            element_id):

        return self.negative[element_id]



    def get_zero(
            self,
            element_id):

        return self.zero[element_id]



    # =====================================================
    # NETWORK IMPEDANCE
    # =====================================================

    def total_impedance(
            self,
            elements,
            sequence="positive"):


        """
        Calculates equivalent series impedance.

        Used for fault path calculation.

        """


        if sequence == "positive":

            data = self.positive


        elif sequence == "negative":

            data = self.negative


        elif sequence == "zero":

            data = self.zero


        else:

            raise ValueError(
                "Invalid sequence"
            )



        Z = complex(0,0)



        for element in elements:

            Z += data[element]


        return Z



    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self):

        return {

            "positive_elements":
                len(self.positive),


            "negative_elements":
                len(self.negative),


            "zero_elements":
                len(self.zero)

        }
