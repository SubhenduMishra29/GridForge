"""
GridForge Newton-Raphson Power Flow Solver

Solves:

        J(x) Δx = ΔS

where:

        x = [theta, V]

Uses:

    mismatch.py
    jacobian.py


Output:

    Bus voltage magnitude
    Bus voltage angle
"""


import numpy as np

from scipy.sparse.linalg import spsolve


from core.solver.power_flow.mismatch import (
    PowerMismatch
)

from core.solver.power_flow.jacobian import (
    JacobianBuilder
)



class NewtonRaphsonSolver:


    def __init__(
            self,
            network,
            Ybus,
            tolerance=1e-8,
            max_iterations=20):


        self.network = network

        self.Ybus = Ybus

        self.tolerance = tolerance

        self.max_iterations = max_iterations



    # =====================================================
    # STATE VECTOR UPDATE
    # =====================================================

    def update_state(
            self,
            dx):


        angle_vars = []

        voltage_vars = []


        for i,bus in enumerate(
                self.network.buses):


            if not bus.is_slack():

                angle_vars.append(i)



            if bus.is_pq():

                voltage_vars.append(i)



        n_angle = len(angle_vars)



        # -------------------------
        # Update angles
        # -------------------------

        for k,i in enumerate(angle_vars):

            self.network.buses[i].theta += dx[k]



        # -------------------------
        # Update voltages
        # -------------------------

        for k,i in enumerate(voltage_vars):

            self.network.buses[i].V += (
                dx[n_angle+k]
            )



    # =====================================================
    # SOLVE
    # =====================================================

    def solve(self):


        converged = False


        iteration = 0



        while iteration < self.max_iterations:


            # -------------------------
            # mismatch
            # -------------------------

            mismatch_solver = PowerMismatch(

                self.network,

                self.Ybus

            )


            mismatch = (
                mismatch_solver.calculate()
            )



            error = np.max(
                np.abs(mismatch)
            )



            if error < self.tolerance:

                converged = True

                break



            # -------------------------
            # Jacobian
            # -------------------------

            jacobian = JacobianBuilder(

                self.network,

                self.Ybus

            )


            J = jacobian.build()



            # -------------------------
            # Solve correction
            # -------------------------

            dx = spsolve(

                J,

                mismatch

            )



            # -------------------------
            # Update voltages
            # -------------------------

            self.update_state(dx)



            iteration += 1



        return {


            "converged":

                converged,


            "iterations":

                iteration,


            "error":

                error,


            "Vm":

                np.array(

                    [
                    bus.V

                    for bus
                    in self.network.buses

                    ]

                ),


            "Va":

                np.array(

                    [
                    bus.theta

                    for bus
                    in self.network.buses

                    ]

                )

        }
