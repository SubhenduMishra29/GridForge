"""
GridForge Breaker Validation Test


Validates:

- Initial breaker state
- Open operation
- Close operation
- Reset operation
- Switching timestamp


"""


from core.models.breaker import Breaker




def test_breaker_initial_state():


    breaker = Breaker(

        breaker_id="CB1"

    )


    assert breaker.is_closed() is True

    assert breaker.is_open() is False

    assert breaker.tripped is False




def test_breaker_open_operation():


    breaker = Breaker(

        breaker_id="CB1"

    )


    breaker.open(

        time=1.5

    )


    assert breaker.is_open() is True

    assert breaker.tripped is True

    assert breaker.last_operation_time == 1.5




def test_breaker_close_operation():


    breaker = Breaker(

        breaker_id="CB1"

    )


    breaker.open()



    breaker.close(

        time=2.0

    )


    assert breaker.is_closed() is True

    assert breaker.tripped is False

    assert breaker.last_operation_time == 2.0




def test_breaker_reset():


    breaker = Breaker(

        breaker_id="CB1"

    )


    breaker.open(

        time=3.0

    )


    breaker.reset()



    assert breaker.is_closed() is True

    assert breaker.tripped is False

    assert breaker.last_operation_time == 0.0




def test_breaker_representation():


    breaker = Breaker(

        breaker_id="CB1",

        name="Main Incomer"

    )


    text = repr(breaker)



    assert "Main Incomer" in text

    assert "CLOSED" in text
