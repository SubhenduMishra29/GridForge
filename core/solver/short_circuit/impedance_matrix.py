"""
GridForge Short Circuit Impedance Matrix

Handles:

Ybus → Zbus conversion

Used for:

- Three phase faults
- Sequence fault calculations
- Thevenin equivalent extraction


"""

import numpy as np



class ImpedanceMatrix:


    def __init__(
            self,
            network):


        self.network = network


        self.Zbus = None



    # =====================================================
    # BUILD ZBUS
    # =====================================================

    def build(self):


        if self.network.Ybus is None:


            self.network.build_ybus()



        Ybus = self.network.Ybus



        try:


            self.Zbus = np.linalg.inv(

                Ybus

            )


        except np.linalg.LinAlgError:


            raise RuntimeError(

                "Ybus singular. "
                "Cannot calculate Zbus."

            )



        return self.Zbus



    # =====================================================
    # THEVENIN IMPEDANCE
    # =====================================================

    def get_thevenin_impedance(
            self,
            bus_index):


        if self.Zbus is None:


            self.build()



        return self.Zbus[

            bus_index,

            bus_index

        ]



    # =====================================================
    # TRANSFER IMPEDANCE
    # =====================================================

    def get_transfer_impedance(

            self,

            from_bus,

            to_bus):


        if self.Zbus is None:


            self.build()



        return self.Zbus[

            from_bus,

            to_bus

        ]



    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self):


        if self.Zbus is None:


            return {


                "status":

                    "NOT_BUILT"

            }



        return {


            "size":

                self.Zbus.shape

        }
