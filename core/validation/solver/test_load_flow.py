"""
GridForge Load Flow Validation Test

Validates:

- Newton-Raphson solver
- Voltage convergence
- Bus voltage results
- Power flow solution


"""


import numpy as np


from core.network.network import Network


from core.models.bus import Bus


from core.models.line import Line


from core.analysis.load_flow import LoadFlowSolver




def build_test_network():


    """
    Simple 3 bus load flow system


        B1
       /
      /
     B2 ---- B3


    B1 : Slack
    B2 : PQ
    B3 : PQ

    """


    network = Network(

        base_mva=100.0

    )



    b1 = Bus(

        bus_id="B1",

        voltage_kv=132,

        bus_type="SLACK",

        voltage_mag=1.05

    )


    b2 = Bus(

        bus_id="B2",

        voltage_kv=132,

        bus_type="PQ",

        p_load=-50,

        q_load=-30

    )


    b3 = Bus(

        bus_id="B3",

        voltage_kv=132,

        bus_type="PQ",

        p_load=-40,

        q_load=-20

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




# =====================================================
# TEST CASES
# =====================================================


def test_load_flow_convergence():


    network = build_test_network()



    solver = LoadFlowSolver(

        network

    )


    result = solver.solve()



    assert result is not None



    assert result["converged"] is True




def test_voltage_profile_exists():


    network = build_test_network()



    solver = LoadFlowSolver(

        network

    )


    result = solver.solve()



    Vm = result["Vm"]



    assert len(Vm) == 3




def test_voltage_limits():


    network = build_test_network()



    solver = LoadFlowSolver(

        network

    )


    result = solver.solve()



    Vm = result["Vm"]



    for voltage in Vm:


        assert (

            0.8 <= voltage <= 1.2

        )



def test_slack_voltage_preserved():


    network = build_test_network()



    solver = LoadFlowSolver(

        network

    )


    result = solver.solve()



    Vm = result["Vm"]



    assert np.isclose(

        Vm[0],

        1.05,

        atol=1e-3

    )
