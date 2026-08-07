"""
Protection Coordination Validation

Checks:

Primary relay operates before backup relay.

"""


class FaultCoordinationTest:


    def __init__(
            self,
            coordinator):

        self.coordinator = coordinator



    def run(
            self,
            fault_current):


        return self.coordinator.evaluate(

            fault_current

        )
