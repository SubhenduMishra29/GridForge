"""
GridForge Protection System

Central protection coordinator.

Responsibilities:

- Register relays
- Evaluate relay operations
- Generate trip commands
- Interface with breaker manager


Uses:

Relay models
BreakerManager


"""


class ProtectionSystem:



    def __init__(
            self,
            breaker_manager=None):


        self.relays = {}


        self.breaker_manager = (
            breaker_manager
        )


        self.events = []



    # =====================================================
    # RELAY REGISTRATION
    # =====================================================

    def add_relay(
            self,
            relay,
            breaker_id):


        self.relays[relay.id] = {


            "relay":

                relay,


            "breaker":

                breaker_id

        }



    # =====================================================
    # FAULT EVALUATION
    # =====================================================

    def evaluate(
            self,
            measurements):


        trips = []



        for relay_id, data in self.relays.items():


            relay = data["relay"]


            if relay_id not in measurements:

                continue



            measurement = measurements[relay_id]



            relay.measure(

                measurement.get(
                    "voltage",
                    0.0
                ),

                measurement.get(
                    "current",
                    0.0
                ),

                measurement.get(
                    "angle",
                    0.0
                )

            )



            if relay.trip():


                trips.append({

                    "relay":
                        relay_id,


                    "breaker":
                        data["breaker"]

                })



        return trips



    # =====================================================
    # EXECUTE TRIPS
    # =====================================================

    def operate(
            self,
            trip_commands,
            time=0.0):


        results = []



        for command in trip_commands:


            if self.breaker_manager:


                result = (

                    self.breaker_manager.trip(

                        command["breaker"],

                        time

                    )

                )


                results.append({

                    "breaker":
                        command["breaker"],

                    "success":
                        result

                })


                self.events.append({

                    "time":
                        time,


                    "relay":
                        command["relay"],


                    "breaker":
                        command["breaker"]

                })


        return results



    # =====================================================
    # COMPLETE PROTECTION CYCLE
    # =====================================================

    def process_fault(
            self,
            measurements,
            time=0.0):


        commands = self.evaluate(

            measurements

        )


        return self.operate(

            commands,

            time

        )



    # =====================================================
    # STATUS
    # =====================================================

    def summary(self):


        return {


            "relays":

            list(

                self.relays.keys()

            ),


            "events":

            self.events

        }
