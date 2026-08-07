"""
GridForge Directional Relay

Directional protection element.

Functions:

    - Current pickup
    - Directional decision
    - Forward/reverse discrimination
    - Trip permission


Future extensions:

    - Polarizing memory voltage
    - Negative sequence directional element
    - Zero sequence directional element
    - IEC directional OC coordination

"""


import math


from core.protection.relay_base import RelayBase



class DirectionalRelay(RelayBase):


    def __init__(
            self,
            relay_id,
            pickup_current,
            forward_angle=90.0,
            tolerance=90.0):


        super().__init__(
            relay_id
        )


        self.pickup_current = pickup_current


        # Maximum torque angle

        self.forward_angle = forward_angle


        self.tolerance = tolerance



        self.direction = None



    # =====================================================
    # CURRENT PICKUP
    # =====================================================

    def check_pickup(self):


        if self.current >= self.pickup_current:


            self.picked_up = True


        else:


            self.picked_up = False



        return self.picked_up



    # =====================================================
    # DIRECTIONAL ELEMENT
    # =====================================================

    def check_direction(
            self,
            voltage_angle,
            current_angle):


        """
        Directional torque:

            T = V × I × cos(phi)

        phi = angle difference

        """


        angle_difference = (

            voltage_angle
            -
            current_angle

        )


        # Normalize angle

        while angle_difference > 180:

            angle_difference -= 360



        while angle_difference < -180:

            angle_difference += 360



        if abs(

            angle_difference
            -
            self.forward_angle

        ) <= self.tolerance:


            self.direction = "FORWARD"


        else:


            self.direction = "REVERSE"



        return self.direction



    # =====================================================
    # TRIP LOGIC
    # =====================================================

    def trip(self):


        if (

            self.check_pickup()

            and

            self.direction == "FORWARD"

        ):


            self.tripped = True



        else:


            self.tripped = False



        return self.tripped



    # =====================================================
    # STATUS
    # =====================================================

    def status(self):


        data = super().status()


        data.update({

            "direction":
                self.direction

        })


        return data



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (

            f"DirectionalRelay("
            f"{self.id}, "
            f"direction={self.direction})"

        )
