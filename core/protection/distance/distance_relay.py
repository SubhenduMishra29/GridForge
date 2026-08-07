"""
GridForge Distance Relay

Transmission line impedance protection.

Functions:

    Calculate apparent impedance
    Zone reach comparison
    Trip decision


Future extensions:

    - Mho characteristic
    - Quadrilateral characteristic
    - Load encroachment
    - Power swing blocking
    - Out-of-step protection


"""


import cmath


from core.protection.relay_base import RelayBase



class DistanceRelay(RelayBase):


    def __init__(
            self,
            relay_id,
            zone1_reach,
            zone2_reach,
            zone3_reach,
            zone1_time=0.0,
            zone2_time=0.3,
            zone3_time=1.0):


        super().__init__(
            relay_id
        )


        self.zone1_reach = zone1_reach

        self.zone2_reach = zone2_reach

        self.zone3_reach = zone3_reach



        self.zone_times = {


            "ZONE1":
                zone1_time,


            "ZONE2":
                zone2_time,


            "ZONE3":
                zone3_time

        }



        self.Z_seen = 0j

        self.active_zone = None



    # =====================================================
    # IMPEDANCE MEASUREMENT
    # =====================================================

    def calculate_impedance(
            self,
            voltage,
            current):


        if current == 0:

            self.Z_seen = complex(
                float("inf"),
                0
            )

        else:

            self.Z_seen = (

                voltage
                /
                current

            )



        return self.Z_seen



    # =====================================================
    # ZONE DETECTION
    # =====================================================

    def check_zone(self):


        Z = abs(
            self.Z_seen
        )



        if Z <= self.zone1_reach:


            self.active_zone = "ZONE1"



        elif Z <= self.zone2_reach:


            self.active_zone = "ZONE2"



        elif Z <= self.zone3_reach:


            self.active_zone = "ZONE3"



        else:


            self.active_zone = None



        return self.active_zone



    # =====================================================
    # PICKUP
    # =====================================================

    def check_pickup(self):


        if self.active_zone is not None:


            self.picked_up = True


        else:

            self.picked_up = False



        return self.picked_up



    # =====================================================
    # TRIP
    # =====================================================

    def trip(self):


        self.check_zone()


        self.check_pickup()



        if self.picked_up:

            self.tripped = True



        return self.tripped



    # =====================================================
    # OPERATING TIME
    # =====================================================

    def operating_time(self):


        if self.active_zone is None:

            return float("inf")



        return self.zone_times[

            self.active_zone

        ]



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (

            f"DistanceRelay("
            f"{self.id}, "
            f"Zone={self.active_zone}, "
            f"Z={self.Z_seen})"

        )
