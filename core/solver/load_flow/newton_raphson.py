"""
GridForge Newton-Raphson Load Flow Engine

Industrial AC Power Flow Solver

Responsibilities:

- Newton-Raphson iteration
- Jacobian solution
- Voltage state update
- Convergence monitoring
- PV/PQ reactive limit handling


Does NOT:

- Build Ybus
- Manage topology
- Create equipment models


"""

import numpy as np


from core.solver.load_flow.mismatch import (
    PowerMismatch
)

from core.solver.load_flow.jacobian import (
    JacobianBuilder
)

from core.solver.load_flow.sparse_solver import (
    SparseLinearSolver
)

from core.solver.load_flow.q_limit_handler import (
    QLimitHandler
)



class NewtonRaphsonSolver:


    def __init__(
            self,
            network,
            options):


        self.network = network

        self.options = options


        self.linear_solver = (
            SparseLinearSolver()
        )


        self.q_handler = (
            QLimitHandler(network)
        )



        self.history = []



    # =====================================================
    # MAIN SOLVER
    # =====================================================

    def solve(self):


        self.options.validate()



        mismatch_solver = PowerMismatch(
            self.network
        )


        jacobian_builder = JacobianBuilder(
            self.network
        )



        converted_pv = []



        for iteration in range(

            self.options.max_iterations

        ):



            # ---------------------------------
            # Calculate mismatch
            # ---------------------------------

            mismatch = (

                mismatch_solver

                .calculate()

            )



            error = np.max(

                np.abs(mismatch)

            )



            self.history.append(

                error

            )



            if self.options.verbose:


                print(

                    f"Iteration {iteration+1}: "

                    f"Mismatch={error:.6e}"

                )



            # ---------------------------------
            # Convergence check
            # ---------------------------------

            if error < self.options.tolerance:


                return self._result(

                    True,

                    iteration + 1,

                    error,

                    converted_pv

                )



            # ---------------------------------
            # Reactive power limit check
            # ---------------------------------

            if self.options.enforce_q_limits:


                changed = (

                    self.q_handler

                    .check_limits()

                )


                if changed:


                    converted_pv.extend(

                        changed

                    )


                    continue



            # ---------------------------------
            # Build Jacobian
            # ---------------------------------

            J = (

                jacobian_builder

                .build()

            )



            # ---------------------------------
            # Solve linear equation
            #
            # J dx = mismatch
            #
            # ---------------------------------

            try:


                dx = (

                    self.linear_solver

                    .solve(

                        J,

                        mismatch

                    )

                )


            except Exception as e:


                return self._result(

                    False,

                    iteration + 1,

                    error,

                    converted_pv,

                    message=str(e)

                )



            # ---------------------------------
            # Update states
            # ---------------------------------

            self._update_states(

                dx

            )



        # -------------------------------------
        # Failed convergence
        # -------------------------------------

        return self._result(

            False,

            self.options.max_iterations,

            error,

            converted_pv,

            message="Maximum iterations reached"

        )



    # =====================================================
    # STATE UPDATE
    # =====================================================

    def _update_states(
            self,
            dx):


        angle_index = 0



        # ---------------------------------
        # Voltage angle update
        # ---------------------------------

        for bus in self.network.buses:


            if not bus.is_slack():


                bus.theta += (

                    self.options.damping

                    *

                    dx[angle_index]

                )


                angle_index += 1



        # ---------------------------------
        # Voltage magnitude update
        # ---------------------------------

        voltage_index = angle_index



        for bus in self.network.buses:


            if bus.is_pq():


                bus.V += (

                    self.options.damping

                    *

                    dx[voltage_index]

                )


                voltage_index += 1



    # =====================================================
    # RESULT FORMAT
    # =====================================================

    def _result(
            self,
            success,
            iterations,
            error,
            converted_pv,
            message=None):


        return {


            "success":

                success,


            "iterations":

                iterations,


            "error":

                error,


            "pv_to_pq":

                converted_pv,


            "history":

                self.history,


            "message":

                message,


            "voltages":

                self._voltage_result()

        }



    # =====================================================
    # VOLTAGE OUTPUT
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
