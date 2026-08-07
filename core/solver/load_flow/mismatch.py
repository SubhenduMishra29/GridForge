"""
GridForge Load Flow Mismatch Calculation

Calculates:

ΔP = P_spec - P_calc

ΔQ = Q_spec - Q_calc


Uses:

Network Ybus

Bus voltage states


"""


import numpy as np



class PowerMismatch:



    def __init__(
            self,
            network):


        self.network = network



    # =====================================================
    # CALCULATE BUS POWER INJECTION
    # =====================================================

    def calculate_power(self):


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



        P = np.zeros(n)

        Q = np.zeros(n)



        for i in range(n):


            for j in range(n):


                angle = (

                    theta[i]

                    -

                    theta[j]

                )



                G = Ybus[i,j].real

                B = Ybus[i,j].imag



                P[i] += (

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



                Q[i] += (

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



        return P,Q




    # =====================================================
    # MISMATCH VECTOR
    # =====================================================

    def calculate(self):


        P_calc, Q_calc = (

            self.calculate_power()

        )



        dp = []

        dq = []



        for bus,Pc,Qc in zip(

            self.network.buses,

            P_calc,

            Q_calc

        ):



            if not bus.is_slack():


                dp.append(

                    bus.P_spec - Pc

                )



            if bus.is_pq():


                dq.append(

                    bus.Q_spec - Qc

                )



        mismatch = np.concatenate(

            [

                np.array(dp),

                np.array(dq)

            ]

        )



        return mismatch
