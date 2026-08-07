"""
GridForge Power Flow Mismatch Calculator

Calculates:

    ΔP = P_spec - P_calc
    ΔQ = Q_spec - Q_calc


Used by:

    newton_raphson.py


Supports:

    - Slack bus
    - PV bus
    - PQ bus
"""


import numpy as np



class PowerMismatch:


    def __init__(
            self,
            network,
            Ybus):

        self.network = network
        self.Ybus = Ybus



    # =====================================================
    # CALCULATE BUS POWER
    # =====================================================

    def calculate_power(self):

        buses = self.network.buses


        n = len(buses)


        Vm = np.array(
            [
                bus.V
                for bus in buses
            ]
        )


        Va = np.array(
            [
                bus.theta
                for bus in buses
            ]
        )



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


        return P, Q



    # =====================================================
    # MISMATCH VECTOR
    # =====================================================

    def calculate(self):


        P_calc, Q_calc = self.calculate_power()



        mismatch = []



        for index,bus in enumerate(
                self.network.buses):


            # -------------------------
            # Slack bus
            # -------------------------

            if bus.is_slack():

                continue



            # -------------------------
            # Active power mismatch
            # -------------------------

            dP = (
                bus.P_spec
                -
                P_calc[index]
            )


            mismatch.append(dP)



            # -------------------------
            # Reactive mismatch
            # -------------------------

            if bus.is_pq():


                dQ = (
                    bus.Q_spec
                    -
                    Q_calc[index]
                )


                mismatch.append(dQ)



        return np.array(
            mismatch
        )
