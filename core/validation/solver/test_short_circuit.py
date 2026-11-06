"""
GridForge Short Circuit Validation Test


Validates:

- Three phase fault
- LG fault
- LL fault
- LLG fault


"""



import numpy as np



from core.network.network import Network


from core.models.bus import Bus


from core.models.line import Line


from core.solver.short_circuit import (

    ShortCircuitSolver,

    FaultType,

    SequenceNetwork

)




def build_fault_test_network():


    """
    Simple radial fault network


        B1 -------- B2 -------- B3


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




def build_sequence_network():


    seq = SequenceNetwork()



    seq.add_element(

        "B3",

        Z1=complex(0.02,0.08),

        Z2=complex(0.02,0.08),

        Z0=complex(0.05,0.15)

    )


    return seq




# =====================================================
# TEST CASES
# =====================================================


def test_three_phase_fault():


    network = build_fault_test_network()



    solver = ShortCircuitSolver(

        network

    )



    result = solver.solve(

        FaultType.THREE_PHASE,

        2

    )



    assert result is not None



    assert result["fault_type"] == "3PH"



    assert (

        result["fault_current_magnitude"]

        >

        0

    )




def test_lg_fault():


    network = build_fault_test_network()



    seq = build_sequence_network()



    solver = ShortCircuitSolver(

        network,

        seq

    )



    result = solver.solve(

        FaultType.SINGLE_LINE_GROUND,

        "B3"

    )



    assert result["fault_type"] == "LG"



    assert result["magnitude"] > 0




def test_ll_fault():


    network = build_fault_test_network()



    seq = build_sequence_network()



    solver = ShortCircuitSolver(

        network,

        seq

    )



    result = solver.solve(

        FaultType.LINE_LINE,

        "B3"

    )



    assert result["fault_type"] == "LL"



    assert result["magnitude"] > 0




def test_llg_fault():


    network = build_fault_test_network()



    seq = build_sequence_network()



    solver = ShortCircuitSolver(

        network,

        seq

    )



    result = solver.solve(

        FaultType.DOUBLE_LINE_GROUND,

        "B3"

    )



    assert result["fault_type"] == "LLG"



    assert result["magnitude"] > 0
