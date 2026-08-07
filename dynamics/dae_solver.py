"""
GridForge Dynamic Algebraic Equation Solver

Solves:

dx/dt = f(x,V)

0 = g(x,V)

Dynamic states:
    delta  - rotor angle
    omega  - speed deviation
    Efd    - excitation voltage
    Pm     - mechanical power
    Pss    - stabilizer state

Algebraic states:
    Bus voltages
    Network currents
    Electrical power
"""


import numpy as np


from dynamics.state_vector import DynamicState
from dynamics.algebraic_solver import AlgebraicNetworkSolver
from dynamics.integrator import RK4Integrator



class DAESolver:


    def __init__(
            self,
            network,
            generators,
            dt=0.01):


        self.network = network

        self.generators = generators

        self.dt = dt


        # Dynamic states

        self.state = DynamicState(
            generators
        )


        # Network algebraic solver

        self.algebraic_solver = (
            AlgebraicNetworkSolver(
                network
            )
        )


        # Numerical integration

        self.integrator = (
            RK4Integrator()
        )



    # =====================================================
    # GENERATOR CURRENT INJECTION
    # =====================================================

    def generator_currents(self):

        currents = {}


        for gen in self.generators:


            # Internal emf

            E = (
                gen.Efd *
                np.exp(
                    1j *
                    gen.delta
                )
            )


            Xd = getattr(
                gen,
                "Xd",
                1.8
            )


            I = (
                E /
                (1j * Xd)
            )


            currents[
                gen.bus
            ] = I


        return currents



    # =====================================================
    # NETWORK SOLUTION
    # =====================================================

    def solve_network(self):


        currents = (
            self.generator_currents()
        )


        V = (
            self.algebraic_solver.solve(
                currents
            )
        )


        return V



    # =====================================================
    # ELECTRICAL POWER CALCULATION
    # =====================================================

    def electrical_power(
            self,
            V):


        Pe = []


        currents = (
            self.generator_currents()
        )


        for gen in self.generators:


            I = currents[
                gen.bus
            ]


            S = (
                V[gen.bus]
                *
                np.conj(I)
            )


            Pe.append(
                S.real
            )


        return Pe



    # =====================================================
    # DIFFERENTIAL EQUATIONS
    # =====================================================

    def derivatives(
            self,
            state):


        # ---------------------------------
        # 1. Solve algebraic network
        # ---------------------------------

        V = self.solve_network()



        # ---------------------------------
        # 2. Electrical power
        # ---------------------------------

        Pe = (
            self.electrical_power(
                V
            )
        )



        dx = {

            "delta":[],
            "omega":[],
            "Efd":[],
            "Pm":[],
            "Pss":[]
        }



        # ---------------------------------
        # 3. Generator models
        # ---------------------------------

        for index,gen in enumerate(
                self.generators):


            result = gen.derivatives(

                V[gen.bus],

                Pe[index]

            )


            dx["delta"].append(
                result["delta"]
            )


            dx["omega"].append(
                result["omega"]
            )


            dx["Efd"].append(
                result["Efd"]
            )


            dx["Pm"].append(
                result["Pm"]
            )


            # PSS output

            dx["Pss"].append(
                gen.pss.output(
                    gen.omega
                )
            )


        return dx



    # =====================================================
    # TIME STEP
    # =====================================================

    def step(self):


        dx = self.derivatives(
            self.state
        )


        self.integrate(
            dx
        )


        return {

            "delta":
                self.state.delta,

            "omega":
                self.state.omega,

            "Efd":
                self.state.Efd,

            "Pm":
                self.state.Pm

        }



    # =====================================================
    # INTEGRATION
    # =====================================================

    def integrate(
            self,
            dx):


        dt = self.dt


        for i in range(
                len(self.generators)):


            self.state.delta[i] += (
                dx["delta"][i]
                *
                dt
            )


            self.state.omega[i] += (
                dx["omega"][i]
                *
                dt
            )


            self.state.Efd[i] += (
                dx["Efd"][i]
                *
                dt
            )


            self.state.Pm[i] += (
                dx["Pm"][i]
                *
                dt
            )
