"""
GridForge Newton-Raphson Jacobian Builder

Builds:

        H  N
    J = 
        M  L


For AC power flow solution.

Supports:

    - Slack bus
    - PV bus
    - PQ bus

Compatible with:

    scipy sparse solvers
"""


import numpy as np
from scipy.sparse import csr_matrix



class JacobianBuilder:


    def __init__(
            self,
            network,
            Ybus):

        self.network = network
        self.Ybus = Ybus



    # =====================================================
    # VARIABLE INDEXING
    # =====================================================

    def build_indices(self):

        angle_vars = []

        voltage_vars = []


        for i,bus in enumerate(
                self.network.buses):


            if not bus.is_slack():

                angle_vars.append(i)



            if bus.is_pq():

                voltage_vars.append(i)



        return angle_vars, voltage_vars



    # =====================================================
    # JACOBIAN BUILD
    # =====================================================

    def build(self):


        buses = self.network.buses


        n = len(buses)


        Vm = np.array(
            [
                b.V
                for b in buses
            ]
        )


        Va = np.array(
            [
                b.theta
                for b in buses
            ]
        )



        angle_vars, voltage_vars = (
            self.build_indices()
        )


        size = (
            len(angle_vars)
            +
            len(voltage_vars)
        )


        J = np.zeros(
            (
                size,
                size
            )
        )



        # -------------------------------------------------
        # Calculate bus power
        # -------------------------------------------------

        P = np.zeros(n)
        Q = np.zeros(n)



        for i in range(n):

            for j in range(n):


                G = self.Ybus[i,j].real

                B = self.Ybus[i,j].imag


                angle = Va[i]-Va[j]


                P[i] += (

                    Vm[i]
                    *
                    Vm[j]
                    *
                    (
                    G*np.cos(angle)
                    +
                    B*np.sin(angle)
                    )

                )


                Q[i] += (

                    Vm[i]
                    *
                    Vm[j]
                    *
                    (
                    G*np.sin(angle)
                    -
                    B*np.cos(angle)
                    )

                )



        # -------------------------------------------------
        # H block  dP/dTheta
        # -------------------------------------------------

        for r,i in enumerate(angle_vars):

            for c,j in enumerate(angle_vars):


                if i == j:


                    J[r,c] = (
                        -Q[i]
                        -
                        (
                        Vm[i]**2
                        *
                        self.Ybus[i,i].imag
                        )
                    )


                else:


                    angle = Va[i]-Va[j]


                    G = self.Ybus[i,j].real

                    B = self.Ybus[i,j].imag


                    J[r,c] = (

                        Vm[i]
                        *
                        Vm[j]
                        *
                        (
                        G*np.sin(angle)
                        -
                        B*np.cos(angle)
                        )

                    )



        offset = len(angle_vars)



        # -------------------------------------------------
        # N block dP/dV
        # -------------------------------------------------

        for r,i in enumerate(angle_vars):

            for c,j in enumerate(voltage_vars):


                if i == j:


                    J[r,offset+c] = (

                        P[i]
                        /
                        Vm[i]
                        +
                        self.Ybus[i,i].real
                        *
                        Vm[i]

                    )


                else:


                    angle = Va[i]-Va[j]


                    G = self.Ybus[i,j].real

                    B = self.Ybus[i,j].imag


                    J[r,offset+c] = (

                        Vm[i]
                        *
                        (
                        G*np.cos(angle)
                        +
                        B*np.sin(angle)
                        )

                    )



        # -------------------------------------------------
        # M block dQ/dTheta
        # -------------------------------------------------

        row_offset = len(angle_vars)


        for r,i in enumerate(voltage_vars):

            for c,j in enumerate(angle_vars):


                if i == j:


                    J[row_offset+r,c] = (

                        P[i]
                        -
                        Vm[i]**2
                        *
                        self.Ybus[i,i].real

                    )


                else:


                    angle = Va[i]-Va[j]


                    G = self.Ybus[i,j].real

                    B = self.Ybus[i,j].imag


                    J[row_offset+r,c] = -(

                        Vm[i]
                        *
                        Vm[j]
                        *
                        (
                        G*np.cos(angle)
                        +
                        B*np.sin(angle)
                        )

                    )



        # -------------------------------------------------
        # L block dQ/dV
        # -------------------------------------------------

        for r,i in enumerate(voltage_vars):

            for c,j in enumerate(voltage_vars):


                if i == j:


                    J[
                    row_offset+r,
                    offset+c
                    ] = (

                        Q[i]
                        /
                        Vm[i]
                        -
                        self.Ybus[i,i].imag
                        *
                        Vm[i]

                    )


                else:


                    angle = Va[i]-Va[j]


                    G = self.Ybus[i,j].real

                    B = self.Ybus[i,j].imag


                    J[
                    row_offset+r,
                    offset+c
                    ] = (

                        Vm[i]
                        *
                        (
                        G*np.sin(angle)
                        -
                        B*np.cos(angle)
                        )

                    )



        return csr_matrix(J)
