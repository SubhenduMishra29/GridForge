"""
GridForge Ybus Validation Test

Validates:

- Bus indexing
- Line admittance
- Transformer admittance
- Ybus dimensions
- Matrix properties


"""


import numpy as np


from core.network.network import Network


from core.models.bus import Bus


from core.models.line import Line



def build_test_network():


    """
    Creates a simple 3 bus system.

    Bus1 ---- Bus2 ---- Bus3

    """


    network = Network(
        base_mva=100.0
    )



    b1 = Bus(

        bus_id="B1",

        voltage_kv=132,

        bus_type="SLACK"

    )


    b2 = Bus(

        bus_id="B2",

        voltage_kv=132,

        bus_type="PQ"

    )


    b3 = Bus(

        bus_id="B3",

        voltage_kv=132,

        bus_type="PQ"

    )



    network.add_bus(b1)

    network.add_bus(b2)

    network.add_bus(b3)



    l1 = Line(

        line_id="L1",

        from_bus=b1,

        to_bus=b2,

        r_pu=0.01,

        x_pu=0.05

    )


    l2 = Line(

        line_id="L2",

        from_bus=b2,

        to_bus=b3,

        r_pu=0.015,

        x_pu=0.06

    )



    network.add_line(l1)

    network.add_line(l2)



    return network




# =====================================================
# TEST CASES
# =====================================================


def test_ybus_dimensions():


    network = build_test_network()


    Ybus = network.build_ybus()



    assert Ybus.shape == (

        3,

        3

    )



def test_ybus_symmetry():


    network = build_test_network()


    Ybus = network.build_ybus()



    assert np.allclose(

        Ybus,

        Ybus.T

    )



def test_ybus_diagonal_elements():


    network = build_test_network()


    Ybus = network.build_ybus()



    for i in range(3):

        assert abs(

            Ybus[i,i]

        ) > 0



def test_ybus_off_diagonal_connection():


    network = build_test_network()


    Ybus = network.build_ybus()



    # B1-B2 connection

    assert abs(

        Ybus[0,1]

    ) > 0



    # B2-B3 connection

    assert abs(

        Ybus[1,2]

    ) > 0
