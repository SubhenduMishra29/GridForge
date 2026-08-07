"""
GridForge Circuit Breaker Model


Functions:

    - Open / close breaker
    - Receive trip command
    - Track breaker state
    - Provide switching status


Used by:

    protection_system.py
    network.py


"""


class Breaker:


    def __init__(
            self,
            breaker_id,
            connected_element=None):


        self.id = breaker_id


        self.connected_element = connected_element


        # Electrical state

        self.closed = True


        # Operation state

        self.trip_count = 0



    # =====================================================
    # OPEN BREAKER
    # =====================================================

    def open(self):


        if self.closed:


            self.closed = False

            self.trip_count += 1



        return self.closed



    # =====================================================
    # CLOSE BREAKER
    # =====================================================

    def close(self):


        self.closed = True


        return self.closed



    # =====================================================
    # TRIP COMMAND
    # =====================================================

    def trip(self):


        return self.open()



    # =====================================================
    # STATUS
    # =====================================================

    def is_closed(self):


        return self.closed



    def status(self):


        return {


            "id":

                self.id,


            "element":

                self.connected_element,


            "closed":

                self.closed,


            "trip_count":

                self.trip_count

        }



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        state = (

            "CLOSED"

            if self.closed

            else

            "OPEN"

        )


        return (

            f"Breaker("
            f"{self.id}: {state})"

        )





# =========================================================
# BREAKER MANAGER
# =========================================================

class BreakerManager:



    def __init__(self):


        self.breakers = {}



    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    def add_breaker(
            self,
            breaker):


        self.breakers[breaker.id] = breaker



    # -----------------------------------------------------
    # TRIP
    # -----------------------------------------------------

    def trip(
            self,
            breaker_id):


        if breaker_id in self.breakers:


            return self.breakers[breaker_id].trip()



        raise KeyError(

            f"Breaker not found: {breaker_id}"

        )



    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------

    def close(
            self,
            breaker_id):


        if breaker_id in self.breakers:


            return self.breakers[breaker_id].close()



        raise KeyError(

            f"Breaker not found: {breaker_id}"

        )



    # -----------------------------------------------------
    # STATE QUERY
    # -----------------------------------------------------

    def is_closed(
            self,
            breaker_id):


        if breaker_id not in self.breakers:


            # default behaviour:
            # no breaker means permanently closed

            return True



        return (

            self.breakers[breaker_id]
            .is_closed()

        )



    # -----------------------------------------------------
    # DEBUG
    # -----------------------------------------------------

    def summary(self):


        return {


            bid:

            breaker.status()

            for bid, breaker

            in self.breakers.items()

        }
