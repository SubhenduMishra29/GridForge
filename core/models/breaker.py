"""
GridForge Circuit Breaker Model

Represents a physical circuit breaker.

Responsibilities:
    - Maintain breaker state
    - Open/close operation
    - Switching timing information

Does NOT perform:
    - Fault detection
    - Protection decisions
    - Relay coordination

Those belong to:
    core/protection

Used by:
    core/network
    core/simulation
"""


class Breaker:


    def __init__(
            self,

            breaker_id: str,

            connected_element=None,

            name=None,

            trip_time=0.05,

            close_time=0.10
    ):


        # -------------------------
        # Identification
        # -------------------------

        self.id = breaker_id

        self.name = (
            name
            if name
            else breaker_id
        )


        # -------------------------
        # Connected equipment
        # -------------------------

        self.connected_element = (
            connected_element
        )


        # -------------------------
        # Timing parameters
        # -------------------------

        self.trip_time = trip_time

        self.close_time = close_time



        # -------------------------
        # State
        # -------------------------

        self.closed = True

        self.tripped = False



        # Event time

        self.last_operation_time = 0.0



    # =====================================================
    # SWITCHING OPERATIONS
    # =====================================================

    def open(
            self,
            time=0.0):

        """
        Open breaker.
        """

        self.closed = False

        self.tripped = True

        self.last_operation_time = time



    def close(
            self,
            time=0.0):

        """
        Close breaker.
        """

        self.closed = True

        self.tripped = False

        self.last_operation_time = time



    # =====================================================
    # STATUS
    # =====================================================

    def is_closed(self):

        return self.closed



    def is_open(self):

        return not self.closed



    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.closed = True

        self.tripped = False

        self.last_operation_time = 0.0



    # =====================================================
    # DEBUG
    # =====================================================

    def __repr__(self):

        state = (
            "CLOSED"
            if self.closed
            else "OPEN"
        )

        return (
            f"Breaker("
            f"{self.name}, "
            f"state={state})"
        )
