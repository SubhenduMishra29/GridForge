"""
GridForge Circuit Breaker Model

Physical switching equipment model.

Responsibilities:
- Maintain breaker electrical state
- Open / close operation
- Switching timing
- Failure modelling
- Event logging

Does NOT:
- Detect faults
- Calculate protection
- Coordinate relays

Protection belongs to:
core/protection

Used by:
core/network
core/simulation
core/protection
"""


class Breaker:


    def __init__(
        self,
        breaker_id: str,
        connected_element=None,
        name=None,

        voltage_kv=0.0,
        rated_current=0.0,
        interrupting_capacity=0.0,

        trip_time=0.05,
        close_time=0.10
    ):


        # -------------------------
        # Identification
        # -------------------------

        self.id = breaker_id

        self.name = name or breaker_id


        # -------------------------
        # Connection
        # -------------------------

        self.connected_element = connected_element



        # -------------------------
        # Ratings
        # -------------------------

        self.voltage_kv = voltage_kv

        self.rated_current = rated_current

        self.interrupting_capacity = (
            interrupting_capacity
        )



        # -------------------------
        # Operating times
        # -------------------------

        self.trip_time = trip_time

        self.close_time = close_time



        # -------------------------
        # State
        # -------------------------

        self.closed = True

        self.tripped = False

        self.failed = False



        # -------------------------
        # Event tracking
        # -------------------------

        self.last_operation_time = 0.0

        self.history = []



    # =====================================================
    # OPEN OPERATION
    # =====================================================

    def open(self,time=0.0):


        if self.failed:

            return False



        self.closed = False

        self.tripped = True

        self.last_operation_time = time



        self.history.append({

            "time":time,

            "action":"OPEN"

        })


        return True



    # =====================================================
    # CLOSE OPERATION
    # =====================================================

    def close(self,time=0.0):


        if self.failed:

            return False



        self.closed = True

        self.tripped = False


        self.last_operation_time = time


        self.history.append({

            "time":time,

            "action":"CLOSE"

        })


        return True



    # =====================================================
    # STATUS
    # =====================================================

    def is_closed(self):

        return self.closed



    def is_open(self):

        return not self.closed



    # =====================================================
    # FAILURE MODEL
    # =====================================================

    def fail(self):

        """
        Simulates breaker failure.
        """

        self.failed = True



    def reset_failure(self):

        self.failed = False



    # =====================================================
    # RESET
    # =====================================================

    def reset(self):

        self.closed = True

        self.tripped = False

        self.failed = False

        self.last_operation_time = 0.0

        self.history.clear()



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
            f"{state})"
        )
