"""
GridForge Benchmark Cases


Standard networks for regression testing.


"""


from core.network.network import Network


from core.models.bus import Bus


from core.models.line import Line




def three_bus_radial_case():


    """
    Standard 3 bus radial network.


        B1
        |
        |
        B2
        |
        |
        B3


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



    network.add_line(

        Line(

            line_id="L1",

            from_bus=b1,

            to_bus=b2,

            r_pu=0.01,

            x_pu=0.05

        )

    )


    network.add_line(

        Line(

            line_id="L2",

            from_bus=b2,

            to_bus=b3,

            r_pu=0.015,

            x_pu=0.06

        )

    )


    return network
