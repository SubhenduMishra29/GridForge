"""
GridForge TCC Curve Engine

Time Current Characteristic calculations.

Supported IEC curves:

    Normal Inverse
    Very Inverse
    Extremely Inverse


Used by:

    relay_coordination.py


"""


class TCCCurve:


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
            curve_type="NORMAL_INVERSE"):


        curve_type = curve_type.upper()


        if curve_type not in self.IEC_CURVES:

            raise ValueError(
                f"Unsupported curve: {curve_type}"
            )


        self.curve_type = curve_type


        self.k = (
            self.IEC_CURVES[curve_type]["k"]
        )


        self.alpha = (
            self.IEC_CURVES[curve_type]["alpha"]
        )



    # =====================================================
    # OPERATING TIME
    # =====================================================

    def calculate_time(
            self,
            fault_current,
            pickup_current,
            TMS=1.0):


        if pickup_current <= 0:

            raise ValueError(
                "Pickup current must be positive"
            )


        M = (

            fault_current
            /
            pickup_current

        )


        # Below pickup

        if M <= 1:

            return float("inf")



        time = (

            TMS
            *
            self.k
            /
            (
                M ** self.alpha
                -
                1
            )

        )


        return time



    # =====================================================
    # CURVE DATA GENERATION
    # =====================================================

    def generate_curve(
            self,
            pickup_current,
            TMS=1.0,
            multiplier_range=None):


        if multiplier_range is None:

            multiplier_range = range(
                1,
                21
            )


        curve = []


        for m in multiplier_range:


            current = (

                pickup_current
                *
                m

            )


            t = self.calculate_time(

                current,

                pickup_current,

                TMS

            )


            curve.append({

                "current":
                    current,


                "time":
                    t

            })


        return curve



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (

            f"TCCCurve("
            f"{self.curve_type})"

        )
