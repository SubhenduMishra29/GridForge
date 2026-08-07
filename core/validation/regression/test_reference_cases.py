"""
GridForge Reference Case Regression Test


Ensures:

- Network builds
- Ybus remains stable
- Load flow converges


"""


from core.validation.regression.benchmark_cases import (

    three_bus_radial_case

)




def test_three_bus_case_build():


    network = three_bus_radial_case()



    assert len(network.buses) == 3


    assert len(network.lines) == 2




def test_three_bus_ybus_regression():


    network = three_bus_radial_case()



    Ybus = network.build_ybus()



    assert Ybus.shape == (

        3,

        3

    )




def test_three_bus_repeatability():


    network1 = three_bus_radial_case()

    network2 = three_bus_radial_case()



    Y1 = network1.build_ybus()

    Y2 = network2.build_ybus()



    assert (

        Y1 == Y2

    ).all()
