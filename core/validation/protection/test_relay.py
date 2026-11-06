"""
GridForge Relay Validation Test


Validates:

- Relay pickup decision
- Trip decision
- Reset behaviour
- Separation from breaker


"""


from core.protection.relay import Relay




def test_relay_initial_state():


    relay = Relay(

        relay_id="R1"

    )


    assert relay.tripped is False



def test_overcurrent_pickup():


    relay = Relay(

        relay_id="R1",

        pickup_current=1.0

    )


    current = 2.5


    decision = relay.evaluate(

        current

    )


    assert decision is True



def test_no_trip_below_pickup():


    relay = Relay(

        relay_id="R1",

        pickup_current=5.0

    )


    current = 2.0


    decision = relay.evaluate(

        current

    )


    assert decision is False



def test_relay_trip_operation():


    relay = Relay(

        relay_id="R1",

        pickup_current=1.0

    )


    relay.evaluate(

        10.0

    )


    assert relay.tripped is True



def test_relay_reset():


    relay = Relay(

        relay_id="R1",

        pickup_current=1.0

    )


    relay.evaluate(

        10.0

    )


    relay.reset()



    assert relay.tripped is False
