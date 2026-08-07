"""
GridForge Dynamic Integrators

Provides numerical integration methods for
transient stability and DAE simulation.

Supported:
    - RK4
    - Implicit Trapezoidal

"""

import numpy as np



class RK4Integrator:
    """
    Classical fourth-order Runge Kutta method.

    x(k+1)=x(k)+dt/6(k1+2k2+2k3+k4)

    Suitable for:
        - Rotor dynamics
        - Governor
        - AVR
        - PSS
    """

    def step(
            self,
            x,
            derivative,
            dt):

        k1 = derivative(x)


        k2 = derivative(
            x + 0.5*dt*k1
        )


        k3 = derivative(
            x + 0.5*dt*k2
        )


        k4 = derivative(
            x + dt*k3
        )


        x_new = x + (
            dt/6.0
        ) * (
            k1
            +
            2*k2
            +
            2*k3
            +
            k4
        )


        return x_new



class TrapezoidalIntegrator:
    """
    Implicit trapezoidal method.

    Used in industrial transient stability programs.

    Equation:

    x(n+1)=x(n)+dt/2*(f(n)+f(n+1))


    Requires Newton iteration for nonlinear systems.
    """


    def __init__(
            self,
            tolerance=1e-8,
            max_iterations=20):


        self.tolerance = tolerance

        self.max_iterations = max_iterations



    def step(
            self,
            x,
            derivative,
            dt):


        f_old = derivative(x)


        # Initial prediction
        x_new = (
            x
            +
            dt*f_old
        )


        # Newton iteration

        for _ in range(
                self.max_iterations):


            f_new = derivative(
                x_new
            )


            correction = (
                x
                +
                dt/2 *
                (
                    f_old
                    +
                    f_new
                )
                -
                x_new
            )


            x_new += correction



            if np.linalg.norm(
                    correction
            ) < self.tolerance:

                break


        return x_new



class Integrator:

    """
    Common interface used by
    GridForge DAE solver.
    """


    def __init__(
            self,
            method="RK4"):


        if method == "RK4":

            self.solver = (
                RK4Integrator()
            )


        elif method == "TRAPEZOIDAL":

            self.solver = (
                TrapezoidalIntegrator()
            )


        else:

            raise ValueError(
                "Unknown integration method"
            )



    def step(
            self,
            x,
            derivative,
            dt):

        return self.solver.step(
            x,
            derivative,
            dt
        )
