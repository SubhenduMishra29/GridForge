"""
GridForge Transformer Model

Two-winding transformer model.

Parameters:
    - Series impedance in pu
    - Off nominal tap ratio
    - Phase shift angle

Used by:
    core/network/ybus.py

Does NOT perform:
    - Power flow
    - Fault calculation
    - Voltage regulation

Those belong to core/solver.
"""


import numpy as np



class Transformer:


    def __init__(
            self,

            from_bus: str,
            to_bus: str,

            r_pu: float,
            x_pu: float,

            tap_ratio: float = 1.0,

            phase_shift_deg: float = 0.0,

            name: str = None,

            rating_mva: float = 100.0
    ):


        if from_bus == to_bus:
            raise ValueError(
                "Transformer cannot connect a bus to itself"
            )


        if r_pu == 0 and x_pu == 0:
            raise ValueError(
                "Transformer impedance cannot be zero"
            )


        if tap_ratio <= 0:
            raise ValueError(
                "Tap ratio must be positive"
            )



        # -------------------------
        # Connectivity
        # -------------------------

        self.from_bus = from_bus

        self.to_bus = to_bus



        # -------------------------
        # Electrical parameters
        # -------------------------

        self.r_pu = r_pu

        self.x_pu = x_pu


        self.tap_ratio = tap_ratio


        self.phase_shift_deg = (
            phase_shift_deg
        )



        # -------------------------
        # Equipment data
        # -------------------------

        self.name = (
            name
            if name
            else f"{from_bus}-{to_bus}"
        )


        self.rating_mva = rating_mva



        # -------------------------
        # Operational state
        # -------------------------

        self.in_service = True



        # -------------------------
        # Results
        # -------------------------

        self.loading_mva = 0.0



    # =====================================================
    # DERIVED PROPERTIES
    # =====================================================


    @property
    def z_pu(self):

        return complex(
            self.r_pu,
            self.x_pu
        )



    @property
    def y_pu(self):

        return 1 / self.z_pu



    @property
    def complex_tap(self):

        """
        Complex transformer ratio:

        a = tap * exp(jθ)

        Used in Ybus stamping.
        """

        angle = np.deg2rad(
            self.phase_shift_deg
        )

        return (
            self.tap_ratio *
            np.exp(
                1j*angle
            )
        )



    # =====================================================
    # STATUS CONTROL
    # =====================================================


    def trip(self):

        self.in_service = False



    def close(self):

        self.in_service = True



    # =====================================================
    # DEBUG
    # =====================================================


    def __repr__(self):

        return (
            f"Transformer("
            f"{self.name}: "
            f"{self.from_bus}"
            " → "
            f"{self.to_bus}, "
            f"Z={self.r_pu}+j{self.x_pu}, "
            f"tap={self.tap_ratio}, "
            f"shift={self.phase_shift_deg}°, "
            f"status={self.in_service})"
        )
