"""
GridForge Relay Base Class

Common interface for all protection relays.

Derived classes:

    OvercurrentRelay
    DistanceRelay
    DirectionalRelay
    DifferentialRelay


"""


from abc import ABC, abstractmethod



class RelayBase(ABC):


    def __init__(
            self,
            relay_id):


        self.id = relay_id


        # Relay state

        self.picked_up = False

        self.tripped = False


        # Measured quantities

        self.voltage = 0.0

        self.current = 0.0

        self.angle = 0.0



    # =====================================================
    # MEASUREMENT INPUT
    # =====================================================

    def measure(
            self,
            voltage,
            current,
            angle=0.0):


        """
        Update relay measurements.

        """

        self.voltage = voltage

        self.current = current

        self.angle = angle



    # =====================================================
    # PICKUP LOGIC
    # =====================================================

    @abstractmethod
    def check_pickup(self):

        """
        Relay pickup decision.

        Must be implemented by
        derived relay classes.

        """

        pass



    # =====================================================
    # TRIP LOGIC
    # =====================================================

    def trip(self):


        if self.picked_up:

            self.tripped = True



        return self.tripped



    # =====================================================
    # RESET
    # =====================================================

    def reset(self):


        self.picked_up = False

        self.tripped = False


        self.voltage = 0.0

        self.current = 0.0

        self.angle = 0.0



    # =====================================================
    # STATUS
    # =====================================================

    def status(self):

        return {


            "id":
                self.id,


            "pickup":
                self.picked_up,


            "trip":
                self.tripped

        }
