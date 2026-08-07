# core/network/ybus.py

"""
GridForge Y-Bus Builder

Builds the network admittance matrix.

Responsibilities:

    - Convert network topology into Ybus
    - Stamp lines
    - Stamp transformers
    - Handle switched elements

Does NOT:

    - Solve load flow
    - Calculate faults
    - Perform dynamics


Used by:

    core/solver/power_flow
    core/solver/short_circuit
    core/solver/contingency
"""


import numpy as np

from scipy.sparse import lil_matrix



class YBusBuilder:


    def __init__(
            self,
            network):

        self.network = network

        self.bus_index = {}

        self.Ybus = None



    # =====================================================
    # BUS INDEX
    # =====================================================

    def build_bus_index(self):

        self.bus_index = {

            bus.id: idx

            for idx, bus
            in enumerate(
                self.network.buses
            )

        }



    # =====================================================
    # MAIN BUILD FUNCTION
    # =====================================================

    def build(self):

        self.build_bus_index()


        n = len(
            self.network.buses
        )


        Y = lil_matrix(
            (n, n),
            dtype=complex
        )


        # -------------------------------
        # Lines
        # -------------------------------

        for line in self.network.lines:

            self.stamp_line(
                Y,
                line
            )



        # -------------------------------
        # Transformers
        # -------------------------------

        for trafo in self.network.transformers:

            self.stamp_transformer(
                Y,
                trafo
            )



        self.Ybus = Y.tocsr()


        self.network.Ybus = self.Ybus


        return self.Ybus



    # =====================================================
    # LINE PI MODEL
    # =====================================================

    def stamp_line(
            self,
            Y,
            line):


        # Open circuit / breaker open

        if hasattr(line, "in_service"):

            if not line.in_service:

                return



        i = self.bus_index[
            line.from_bus
        ]

        j = self.bus_index[
            line.to_bus
        ]



        z = complex(
            line.r_pu,
            line.x_pu
        )


        y = 1 / z



        b = 1j * (
            line.b_pu / 2
        )



        # Diagonal

        Y[i,i] += y + b

        Y[j,j] += y + b



        # Mutual

        Y[i,j] -= y

        Y[j,i] -= y




    # =====================================================
    # TRANSFORMER MODEL
    # =====================================================

    def stamp_transformer(
            self,
            Y,
            trafo):


        if hasattr(trafo,"in_service"):

            if not trafo.in_service:

                return



        i = self.bus_index[
            trafo.from_bus
        ]

        j = self.bus_index[
            trafo.to_bus
        ]



        z = complex(
            trafo.r_pu,
            trafo.x_pu
        )


        y = 1/z



        # Tap ratio

        tap = getattr(
            trafo,
            "tap_ratio",
            1.0
        )



        # Phase shift

        shift = np.deg2rad(
            getattr(
                trafo,
                "phase_shift_deg",
                0.0
            )
        )



        a = (
            tap *
            np.exp(
                1j*shift
            )
        )



        # Transformer stamping

        Y[i,i] += (
            y /
            (a*np.conj(a))
        )


        Y[j,j] += y



        Y[i,j] -= (
            y /
            np.conj(a)
        )


        Y[j,i] -= (
            y /
            a
        )



    # =====================================================
    # VALIDATION
    # =====================================================

    def validate(self):

        if self.Ybus is None:

            raise ValueError(
                "Ybus not built"
            )


        n = len(
            self.network.buses
        )


        if self.Ybus.shape != (n,n):

            raise ValueError(
                "Invalid Ybus dimension"
            )



    # =====================================================
    # DEBUG
    # =====================================================

    def summary(self):

        return {

            "buses":
                len(self.network.buses),

            "lines":
                len(self.network.lines),

            "transformers":
                len(self.network.transformers),

            "matrix_size":
                None
                if self.Ybus is None
                else self.Ybus.shape

        }
