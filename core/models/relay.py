"""
GridForge Relay Model

Represents a protection relay device.

Responsibilities:
    - Store relay settings
    - Accept measured electrical quantities
    - Generate trip indication

Does NOT perform:
    - System-wide coordination
    - Fault analysis
    - Breaker control

Those belong to:
    core/protection

Used by:
    core/protection
    core/simulation
"""


class Relay:


    VALID_TYPES = {
        "OVER_CURRENT",
        "DISTANCE",
        "DIFFERENTIAL",
        "VOLTAGE",
        "FREQUENCY"
    }



    def __init__(
            self,

            relay_id: str,

            relay_type: str,

            name=None,

            pickup=1.0,

            time_delay=0.0
    ):


        if relay_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid relay type: {relay_type}"
            )


        # -------------------------
        # Identification
        # -------------------------

        self.id = relay_id

        self.name = (
            name
            if name
            else relay_id
        )


        self.type = relay_type



        # -------------------------
        # Settings
        # -------------------------

        self.pickup = pickup

        self.time_delay = time_delay



        # -------------------------
        # Measurements
        # -------------------------

        self.current = 0.0

        self.voltage = 1.0

        self.impedance = 0.0



        # -------------------------
        # State
        # -------------------------

        self.trip = False



    # =====================================================
    # MEASUREMENT UPDATE
    # =====================================================

    def measure(
            self,

            current=0.0,

            voltage=1.0,

            impedance=0.0):


        self.current = current

        self.voltage = voltage

        self.impedance = impedance



    # =====================================================
    # BASIC TRIP LOGIC
    # =====================================================

    def evaluate(self):

        """
        Basic relay operation.

        Detailed relay curves are implemented in:

            core/protection
        """


        if self.type == "OVER_CURRENT":

            self.trip = (
                abs(self.current)
                >
                self.pickup
            )


        elif self.type == "DISTANCE":

            self.trip = (
                abs(self.impedance)
                <
                self.pickup
            )


        return self.trip



    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.trip = False

        self.current = 0.0

        self.voltage = 1.0

        self.impedance = 0.0



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        return (
            f"Relay("
            f"{self.name}, "
            f"type={self.type}, "
            f"trip={self.trip})"
        )
