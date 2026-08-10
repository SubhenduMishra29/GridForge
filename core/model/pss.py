"""
GridForge Power System Stabilizer (PSS)

Purpose:
    Provides damping signal to AVR.

Basic model:

Vpss = Kpss * washout(Δω)

Input:
    Rotor speed deviation

Output:
    Stabilizing voltage signal

The PSS does NOT integrate dynamics.
The DAE solver performs integration.

Used by:
    Generator
    AVR
    DAE Solver
"""


class PSS:


    def __init__(
            self,

            Kpss=10.0,

            Tw=10.0,

            Vpss_min=-0.2,

            Vpss_max=0.2
    ):


        # -------------------------
        # Parameters
        # -------------------------

        self.Kpss = Kpss

        self.Tw = Tw



        # Output limits

        self.Vpss_min = Vpss_min

        self.Vpss_max = Vpss_max



        # Washout state

        self.state = 0.0



    # =====================================================
    # PSS OUTPUT
    # =====================================================

    def output(
            self,

            omega
    ):

        """
        Calculate stabilizing signal.

        omega:
            rotor speed deviation Δω
        """


        Vpss = (
            self.Kpss *
            omega
        )


        return self.limit(Vpss)



    # =====================================================
    # WASHOUT DYNAMICS
    # =====================================================

    def derivative(
            self,

            omega,

            state
    ):

        """
        Washout filter:

        Tw*dX/dt + X = Δω
        """


        return (
            omega - state
        ) / self.Tw



    # =====================================================
    # LIMITER
    # =====================================================

    def limit(
            self,

            value
    ):

        return max(
            self.Vpss_min,
            min(
                value,
                self.Vpss_max
            )
        )



    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.state = 0.0



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (
            f"PSS("
            f"Kpss={self.Kpss}, "
            f"Tw={self.Tw})"
        )
