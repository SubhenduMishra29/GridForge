"""
GridForge AVR Model

Automatic Voltage Regulator model.

Represents excitation control dynamics.

Equation:

dEfd/dt =
( Ka*(Vref - Vt + Vpss) - Efd ) / Ta


The AVR does NOT integrate itself.

The dynamic solver handles integration.

Used by:
    core/models/generator.py
    core/solver/dynamics/dae_solver.py
"""


class AVR:


    def __init__(
            self,

            Ka=200.0,

            Ta=0.02,

            Vref=1.0,

            Efd_min=0.0,

            Efd_max=5.0
    ):


        # -------------------------
        # Parameters
        # -------------------------

        self.Ka = Ka

        self.Ta = Ta

        self.Vref = Vref



        # -------------------------
        # Excitation limits
        # -------------------------

        self.Efd_min = Efd_min

        self.Efd_max = Efd_max



        # Output state

        self.Efd = 1.0



    # =====================================================
    # AVR DIFFERENTIAL EQUATION
    # =====================================================

    def derivative(
            self,

            Efd,

            Vt,

            Vpss=0.0):


        """
        Calculates dEfd/dt

        Inputs:
            Efd  : field voltage
            Vt   : terminal voltage
            Vpss : stabilizer signal


        Output:
            dEfd/dt
        """


        error = (
            self.Vref
            -
            Vt
            +
            Vpss
        )


        dEfd = (
            self.Ka * error
            -
            Efd
        ) / self.Ta


        return dEfd



    # =====================================================
    # LIMITER
    # =====================================================

    def limit(
            self,
            Efd):


        return max(
            self.Efd_min,
            min(
                Efd,
                self.Efd_max
            )
        )



    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.Efd = 1.0



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (
            f"AVR("
            f"Ka={self.Ka}, "
            f"Ta={self.Ta}, "
            f"Vref={self.Vref})"
        )
