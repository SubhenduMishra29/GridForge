"""
GridForge Symmetrical Fault Calculator

Handles balanced faults:

    Three Phase Fault (3Φ)

Uses:

    Positive sequence network only


Equation:

    If = Vth / (Z1 + Zf)


"""



class SymmetricalFault:



    def __init__(

            self,

            impedance_matrix):


        self.impedance_matrix = impedance_matrix



    # =====================================================
    # THREE PHASE FAULT
    # =====================================================

    def calculate_three_phase_fault(

            self,

            bus_index,

            Vprefault=1.0,

            Zf=0.0):


        """
        Calculate 3 phase fault current.

        Parameters:

            bus_index:
                Fault bus location


            Vprefault:
                Prefault voltage (pu)


            Zf:
                Fault impedance (pu)

        """


        # ---------------------------------
        # Thevenin impedance
        # ---------------------------------

        Zth = (

            self.impedance_matrix

            .get_thevenin_impedance(

                bus_index

            )

        )



        # ---------------------------------
        # Fault current
        # ---------------------------------

        If = (

            Vprefault

            /

            (

                Zth + Zf

            )

        )



        # ---------------------------------
        # Fault MVA

        # S = √3 V I

        # In pu:

        # Sfault = If

        # ---------------------------------


        return {


            "fault_type":

                "3PH",



            "bus":

                bus_index,



            "Zth":

                Zth,



            "fault_current_pu":

                If,



            "fault_current_magnitude":

                abs(If)

        }
