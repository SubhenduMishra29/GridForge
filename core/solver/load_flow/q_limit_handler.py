"""
GridForge Generator Reactive Power Limit Handler

Handles:

PV → PQ switching

"""



class QLimitHandler:



    def __init__(
            self,
            network):

        self.network = network



    def check_limits(self):


        converted = []



        for bus in self.network.buses:


            if not bus.is_pv():

                continue



            generator = self._find_generator(

                bus.id

            )


            if generator is None:

                continue



            if generator.Q > generator.Qmax:


                bus.type = "PQ"


                bus.Q_spec = generator.Qmax


                converted.append(

                    bus.id

                )



            elif generator.Q < generator.Qmin:


                bus.type = "PQ"


                bus.Q_spec = generator.Qmin


                converted.append(

                    bus.id

                )



        return converted




    def _find_generator(
            self,
            bus_id):


        for gen in self.network.generators:


            if gen.bus == bus_id:

                return gen



        return None
