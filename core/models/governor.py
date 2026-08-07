"""
GridForge Governor Model

Represents turbine governor dynamics.

Equation:

dPm/dt =
(Pref - Pm - omega/R) / Tg


Inputs:
    Rotor speed deviation

Output:
    Mechanical power command


The governor does NOT integrate states.
The DAE solver performs integration.

Used by:
    Generator model
    Transient stability solver
"""


class Governor:


    def __init__(
            self,

            Pref=1.0,

            R=0.05,

            Tg=0.2,

            Pm_min=0.0,

            Pm_max=1.2
    ):


        # -------------------------
        # Parameters
        # -------------------------

        self.Pref = Pref

        self.R = R

        self.Tg = Tg


        # -------------------------
        # Limits
        # -------------------------

        self.Pm_min = Pm_min

        self.Pm_max = Pm_max



        # State

        self.Pm = Pref



    # =====================================================
    # GOVERNOR DIFFERENTIAL EQUATION
    # =====================================================

    def derivative(
            self,

            Pm,

            omega
    ):

        """
        Calculate mechanical power derivative.


        Pm:
            Current mechanical power


        omega:
            Rotor speed deviation
        """


        dPm = (

            self.Pref
            -
            Pm
            -
            omega / self.R

        ) / self.Tg


        return dPm



    # =====================================================
    # LIMITER
    # =====================================================

    def limit(
            self,

            Pm
    ):

        return max(
            self.Pm_min,
            min(
                Pm,
                self.Pm_max
            )
        )



    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.Pm = self.Pref



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (
            f"Governor("
            f"Pref={self.Pref}, "
            f"R={self.R}, "
            f"Tg={self.Tg})"
        )
