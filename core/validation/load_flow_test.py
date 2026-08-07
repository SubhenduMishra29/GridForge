"""
GridForge Load Flow Validation Test

Simple 3-Bus System

Bus 1:
    Slack

Bus 2:
    PQ Load

Bus 3:
    PQ Load


Purpose:

Validate:

- Network container
- Ybus construction
- Newton-Raphson solver
- Voltage convergence

"""


from core.models.bus import Bus
from core.models.line import Line

from core.network.network import Network

from core.analysis.load_flow import (
    LoadFlowSolver
)




def create_test_network():



    network = Network()



    # ------------------------------------
    # Buses
    # ------------------------------------


    bus1 = Bus(

        bus_id="B1",

        bus_type="SLACK",

        V=1.05,

        theta=0.0

    )



    bus2 = Bus(

        bus_id="B2",

        bus_type="PQ",

        P=-1.0,

        Q=-0.5

    )



    bus3 = Bus(

        bus_id="B3",

        bus_type="PQ",

        P=-0.8,

        Q=-0.3

    )




    network.add_bus(bus1)

    network.add_bus(bus2)

    network.add_bus(bus3)



    # ------------------------------------
    # Lines
    # ------------------------------------


    line12 = Line(

        from_bus="B1",

        to_bus="B2",

        r_pu=0.02,

        x_pu=0.06,

        b_pu=0.03

    )



    line23 = Line(

        from_bus="B2",

        to_bus="B3",

        r_pu=0.025,

        x_pu=0.075,

        b_pu=0.04

    )



    line13 = Line(

        from_bus="B1",

        to_bus="B3",

        r_pu=0.01,

        x_pu=0.03,

        b_pu=0.02

    )



    network.add_line(line12)

    network.add_line(line23)

    network.add_line(line13)



    return network





def run_test():



    network = create_test_network()



    # Build admittance matrix

    network.build_ybus()



    print("\nYbus")

    print(network.Ybus)



    # Run load flow


    solver = LoadFlowSolver(

        network

    )


    result = solver.solve()



    print("\nLoad Flow Result")

    print("----------------")



    print(

        "Success:",

        result["success"]

    )


    print(

        "Iterations:",

        result["iterations"]

    )


    print(

        "Error:",

        result["error"]

    )



    print("\nBus Voltages")

    print("----------------")



    for bus in network.buses:


        print(

            bus.id,

            "V=",

            bus.V,

            "Angle=",

            bus.theta

        )




if __name__ == "__main__":


    run_test()
