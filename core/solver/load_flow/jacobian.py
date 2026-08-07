"""
GridForge Newton-Raphson Jacobian

Builds:

        dP/dθ   dP/dV
J  =   -------------
        dQ/dθ   dQ/dV


Based on:

Ybus
Voltage magnitude
Voltage angle


"""


import numpy as np



class JacobianBuilder:



    def __init__(
            self,
            network):


        self.network = network




    # =====================================================
    # BUILD JACOBIAN
    # =====================================================

    def build(self):


        buses = self.network.buses

        Ybus = self.network.Ybus


        n = len(buses)



        V = np.array(

            [
                bus.V

                for bus in buses
            ]

        )


        theta = np.array(

            [
                bus.theta

                for bus in buses
            ]

        )



        # ---------------------------------------------
        # State indexing
        # ---------------------------------------------

        pvpq = [

            i

            for i,bus

            in enumerate(buses)

            if not bus.is_slack()

        ]


        pq = [

            i

            for i,bus

            in enumerate(buses)

            if bus.is_pq()

        ]



        npv = len(pvpq)

        npq = len(pq)



        J1 = np.zeros(

            (npv,npv)

        )


        J2 = np.zeros(

            (npv,npq)

        )


        J3 = np.zeros(

            (npq,npv)

        )


        J4 = np.zeros(

            (npq,npq)

        )



        # ---------------------------------------------
        # Jacobian calculation
        # ---------------------------------------------

        for ii,i in enumerate(pvpq):


            for jj,j in enumerate(pvpq):


                if i == j:


                    J1[ii,jj] = (

                        -self._Q(i)

                        -

                        Ybus[i,i].imag

                        *

                        V[i]**2

                    )


                else:


                    angle = (

                        theta[i]

                        -

                        theta[j]

                    )


                    G = Ybus[i,j].real

                    B = Ybus[i,j].imag



                    J1[ii,jj] = (

                        V[i]

                        *

                        V[j]

                        *

                        (

                            G*np.sin(angle)

                            -

                            B*np.cos(angle)

                        )

                    )



            for jj,j in enumerate(pq):


                G = Ybus[i,j].real

                B = Ybus[i,j].imag


                angle = (

                    theta[i]

                    -

                    theta[j]

                )



                J2[ii,jj] = (

                    V[i]

                    *

                    (

                        G*np.cos(angle)

                        +

                        B*np.sin(angle)

                    )

                )





        for ii,i in enumerate(pq):


            for jj,j in enumerate(pvpq):


                angle = (

                    theta[i]

                    -

                    theta[j]

                )


                G = Ybus[i,j].real

                B = Ybus[i,j].imag



                J3[ii,jj] = (

                    -

                    V[i]

                    *

                    V[j]

                    *

                    (

                        G*np.cos(angle)

                        +

                        B*np.sin(angle)

                    )

                )



            for jj,j in enumerate(pq):


                if i == j:


                    J4[ii,jj] = (

                        self._P(i)

                        -

                        Ybus[i,i].real

                        *

                        V[i]**2

                    )


                else:


                    angle = (

                        theta[i]

                        -

                        theta[j]

                    )


                    G = Ybus[i,j].real

                    B = Ybus[i,j].imag



                    J4[ii,jj] = (

                        V[i]

                        *

                        (

                            G*np.sin(angle)

                            -

                            B*np.cos(angle)

                        )

                    )



        return np.block(

            [

                [J1,J2],

                [J3,J4]

            ]

        )



    # =====================================================
    # INTERNAL POWER HELPERS
    # =====================================================

    def _P(self,i):


        from core.solver.load_flow.mismatch import PowerMismatch


        P,Q = (

            PowerMismatch(
                self.network
            )
            .calculate_power()

        )


        return P[i]



    def _Q(self,i):


        from core.solver.load_flow.mismatch import PowerMismatch


        P,Q = (

            PowerMismatch(
                self.network
            )
            .calculate_power()

        )


        return Q[i]
