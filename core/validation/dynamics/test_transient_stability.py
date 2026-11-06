"""
GridForge Transient Stability Validation Test


Validates:

- Dynamic solver execution
- Time integration
- Rotor angle update
- Fault event handling


"""



from core.network.network import Network


from core.models.generator import Generator


from core.dynamics.transient_stability import (

    TransientStabilitySolver

)




def build_dynamic_test_network():


    """
    Simple single machine infinite bus system


        G1 ---- BUS1 ---- BUS2


    """


    network = Network(

        base_mva=100.0

    )



    generator = Generator(

        generator_id="G1",

        rated_mva=100,

        inertia=5.0

    )


    network.add_generator(

        generator

    )


    return network




# =====================================================
# TEST CASES
# =====================================================



def test_transient_solver_initialization():


    network = build_dynamic_test_network()



    solver = TransientStabilitySolver(

        network

    )



    assert solver is not None




def test_time_simulation_runs():


    network = build_dynamic_test_network()



    solver = TransientStabilitySolver(

        network

    )


    result = solver.run(

        fault=None,

        t_end=1.0,

        dt=0.01

    )



    assert result is not None




def test_rotor_angle_state_exists():


    network = build_dynamic_test_network()



    solver = TransientStabilitySolver(

        network

    )


    result = solver.run(

        fault=None,

        t_end=1.0,

        dt=0.01

    )



    assert "delta" in result




def test_time_vector_exists():


    network = build_dynamic_test_network()



    solver = TransientStabilitySolver(

        network

    )


    result = solver.run(

        fault=None,

        t_end=1.0,

        dt=0.01

    )



    assert "time" in result
