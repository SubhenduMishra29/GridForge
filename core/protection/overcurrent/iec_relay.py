"""
GridForge IEC Inverse Time Overcurrent Relay

Implements IEC 60255 inverse-time characteristics.

Curves:

    Normal Inverse
    Very Inverse
    Extremely Inverse


Equation:

        k × TMS
t = ----------------
       α
      M  - 1


where:

    M = I / Pickup

"""


from core.protection.relay_base import RelayBase



class IECOvercurrentRelay(RelayBase):


    IEC_CURVES = {


        "NORMAL_INVERSE":
        {
            "k": 0.14,
            "alpha": 0.02
        },


        "VERY_INVERSE":
        {
            "k": 13.5,
            "alpha": 1.0
        },


        "EXTREMELY_INVERSE":
        {
            "k": 80.0,
            "alpha": 2.0
        }

    }



    def __init__(
            self,
            relay_id,
            pickup_current,
            curve="NORMAL_INVERSE",
            TMS=1.0):


        super().__init__(
            relay_id
        )


        curve = curve.upper()


        if curve not in self.IEC_CURVES:

            raise ValueError(

                f"Unsupported IEC curve {curve}"

            )


        self.pickup_current = pickup_current

        self.curve = curve

        self.TMS = TMS



        self.k = (
            self.IEC_CURVES[curve]["k"]
        )


        self.alpha = (
            self.IEC_CURVES[curve]["alpha"]
        )



    # =====================================================
    # PICKUP CHECK
    # =====================================================

    def check_pickup(self):


        if self.current >= self.pickup_current:


            self.picked_up = True


        else:

            self.picked_up = False



        return self.picked_up



    # =====================================================
    # OPERATING TIME
    # =====================================================

    def operating_time(self):


        M = (

            self.current
            /
            self.pickup_current

        )



        if M <= 1:

            return float("inf")



        return (

            self.TMS
            *
            self.k
            /
            (
                M ** self.alpha
                -
                1
            )

        )



    # =====================================================
    # TRIP DECISION
    # =====================================================

    def trip(self):


        if not self.check_pickup():

            return False



        if self.operating_time() < float("inf"):

            self.tripped = True



        return self.tripped



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (

            f"IECRelay("
            f"{self.id}, "
            f"{self.curve}, "
            f"Ip={self.pickup_current}, "
            f"TMS={self.TMS})"

        )
