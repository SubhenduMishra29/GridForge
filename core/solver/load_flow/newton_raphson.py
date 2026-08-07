"""
GridForge Newton-Raphson Load Flow Solver

Numerical engine for AC power flow.

Implements:

J Δx = ΔP/Q

where:

Δx =
[
 Δθ
 ΔV
]

"""

import numpy as np

from core.solver.load_flow.mismatch import (
    PowerMismatch
)

from core.solver.load_flow.jacobian import (
    JacobianBuilder
)


class NewtonRaphsonSolver:


    def __init__(
            self,
            network,
            options):


        self.network = network

        self.options = options



    # =====================================================
    # MAIN SOLVER LOOP
    # =====================================================

    def solve(self):


        self.options.validate()


        mismatch_solver = PowerMismatch(
            self.network
        )


        jacobian_builder = JacobianBuilder(
            self.network
        )



        for iteration in range(
                self.options.max_iterations
        ):


            # ---------------------------------------------
            # Calculate mismatch
            # ---------------------------------------------

            mismatch = (
                mismatch_solver
                .calculate()
            )



            error = np.max(
                np.abs(mismatch)
            )



            if self.options.verbose:

                print(
                    f"Iteration {iteration+1}: "
                    f"Mismatch={error}"
                )



            # ---------------------------------------------
            # Convergence check
            # ---------------------------------------------

            if error < self.options.tolerance:


                return {

                    "success": True,

                    "iterations":
                        iteration + 1,

                    "error":
                        error,

                    "voltages":
                        self._voltage_result()

                }



            # ---------------------------------------------
            # Jacobian
            # ---------------------------------------------

            J = jacobian_builder.build()



            # ---------------------------------------------
            # Solve linear system
            # ---------------------------------------------

            try:


                dx = np.linalg.solve(

                    J,

                    mismatch

                )


            except np.linalg.LinAlgError:


                raise RuntimeError(

                    "Jacobian singular. "
                    "Load flow failed."

                )



            # ---------------------------------------------
            # Update states
            # ---------------------------------------------

            self._update_states(
                dx
            )



        # -------------------------------------------------
        # Non convergence
        # -------------------------------------------------

        return {


            "success": False,

            "iterations":
                self.options.max_iterations,

            "error":
                error,

            "voltages":
                self._voltage_result()

        }




    # =====================================================
    # STATE UPDATE
    # =====================================================

    def _update_states(
            self,
            dx):


        buses = self.network.buses



        angle_index = 0


        voltage_index = 0



        # non-slack angle updates

        for bus in buses:


            if not bus.is_slack():


                bus.theta += (

                    self.options.damping

                    *

                    dx[angle_index]

                )


                angle_index += 1



        # PQ voltage updates


        offset = angle_index



        for bus in buses:


            if bus.is_pq():


                bus.V += (

                    self.options.damping

                    *

                    dx[offset + voltage_index]

                )


                voltage_index += 1




    # =====================================================
    # RESULT EXTRACTION
    # =====================================================

    def _voltage_result(
            self):


        return {


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
