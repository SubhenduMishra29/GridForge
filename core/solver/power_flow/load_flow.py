"""
GridForge AC Load Flow Solver Interface

Public entry point for:

    Network.run_load_flow()


Workflow:

    Network
       |
       |
    Ybus
       |
       |
    Newton-Raphson
       |
       |
    Results


Supports:

    - Slack bus
    - PV bus
    - PQ bus
    - AC power flow
"""


from core.network.ybus import YBusBuilder

from core.solver.power_flow.newton_raphson import (
    NewtonRaphsonSolver
)



class LoadFlowSolver:


    def __init__(
            self,
            network):


        self.network = network

        self.result = None



    # =====================================================
    # SOLVE
    # =====================================================

    def solve(self):


        # -------------------------------------------------
        # Build admittance matrix
        # -------------------------------------------------

        ybus_builder = YBusBuilder(
            self.network
        )


        Ybus = ybus_builder.build()



        self.network.Ybus = Ybus



        # -------------------------------------------------
        # Newton-Raphson solution
        # -------------------------------------------------

        solver = NewtonRaphsonSolver(

            self.network,

            Ybus

        )


        solution = solver.solve()



        # -------------------------------------------------
        # Store bus states
        # -------------------------------------------------

        for i,bus in enumerate(
                self.network.buses):


            bus.V = solution["Vm"][i]

            bus.theta = solution["Va"][i]



        # -------------------------------------------------
        # Standard result object
        # -------------------------------------------------

        self.result = {


            "converged":

                solution["converged"],



            "iterations":

                solution["iterations"],



            "error":

                solution["error"],



            "Vm":

                solution["Vm"],



            "Va":

                solution["Va"],



            "Ybus":

                Ybus

        }



        return self.result
