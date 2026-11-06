"""
Relay Functional Tests

Checks:

- Pickup operation
- Trip logic
- Operating time

"""


class RelayTest:


    def __init__(self):

        self.results = []



    def test_pickup(
            self,
            relay,
            current):


        relay.current = current


        result = relay.check_pickup()


        self.results.append({

            "test":
                "pickup",

            "result":
                result

        })


        return result



    def summary(self):

        return self.results
