"""
GridForge Protection Test Cases


Future cases:

- 3 phase fault
- L-G fault
- L-L fault
- Relay failure
- Breaker failure
- Backup protection


"""


class ProtectionTestCase:


    def __init__(
            self,
            name,
            fault_type,
            fault_current):


        self.name = name

        self.fault_type = fault_type

        self.fault_current = fault_current



    def run(self):

        return {

            "case":
                self.name,

            "fault":
                self.fault_type,

            "current":
                self.fault_current

        }
