"""
GridForge Breaker Manager

Protection control layer.

Responsibilities:

- Register breakers
- Execute relay trip commands
- Operate physical breakers
- Maintain switching events


Does NOT:

- Calculate faults
- Detect faults
- Contain relay logic


Uses:

core.models.breaker.Breaker

"""


from core.models.breaker import Breaker



class BreakerManager:



    def __init__(self):


        self.breakers = {}


        self.events = []



    # =====================================================
    # REGISTER BREAKER
    # =====================================================

    def add_breaker(
            self,
            breaker: Breaker):


        if breaker.id in self.breakers:

            raise ValueError(

                f"Breaker already exists: "
                f"{breaker.id}"

            )


        self.breakers[breaker.id] = breaker



    # =====================================================
    # TRIP COMMAND
    # =====================================================

    def trip(
            self,
            breaker_id,
            time=0.0):


        if breaker_id not in self.breakers:


            raise KeyError(

                f"Breaker not found: "
                f"{breaker_id}"

            )


        breaker = self.breakers[breaker_id]


        result = breaker.open(time)



        self.events.append({

            "time":time,

            "breaker":
                breaker_id,

            "action":
                "TRIP",

            "success":
                result

        })


        return result



    # =====================================================
    # CLOSE COMMAND
    # =====================================================

    def close(
            self,
            breaker_id,
            time=0.0):


        if breaker_id not in self.breakers:


            raise KeyError(

                f"Breaker not found: "
                f"{breaker_id}"

            )


        breaker = self.breakers[breaker_id]


        result = breaker.close(time)



        self.events.append({

            "time":time,

            "breaker":
                breaker_id,

            "action":
                "CLOSE",

            "success":
                result

        })


        return result



    # =====================================================
    # STATUS
    # =====================================================

    def is_closed(
            self,
            breaker_id):


        if breaker_id not in self.breakers:


            # No breaker means element always connected

            return True



        return self.breakers[breaker_id].is_closed()



    # =====================================================
    # GET BREAKER
    # =====================================================

    def get_breaker(
            self,
            breaker_id):


        return self.breakers.get(

            breaker_id

        )



    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self):


        return {


            "breakers":

            {

                bid:

                {

                    "closed":
                        br.is_closed(),

                    "tripped":
                        br.tripped,

                    "failed":
                        br.failed

                }


                for bid, br

                in self.breakers.items()

            },


            "events":

            self.events

        }
